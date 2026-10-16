"""Chunked, scale-safe field metrics and positive condition-tree evaluation."""
import math
import numpy as np

CHUNK_SIZE = 65536


def _number(value):
    return float(value) if math.isfinite(value) else 'overflow'


def _scaled_ratio(scale, value, denominator_scale, denominator_value):
    if value == 0:
        return 0.0
    if denominator_value == 0:
        return math.inf
    sm, se = math.frexp(scale)
    vm, ve = math.frexp(value)
    dm, de = math.frexp(denominator_scale)
    nm, ne = math.frexp(denominator_value)
    try:
        return math.ldexp(sm * vm / (dm * nm), se + ve - de - ne)
    except OverflowError:
        return math.inf


def _difference_parts(left, right):
    """Nonnegative mantissa/exponent for abs(left-right), even above DBL_MAX.

    Compute the direct difference first to preserve cancellation accuracy. Only
    overflowing entries are recomputed at half scale; no offset is subtracted
    from the submitted value before computing its actual error.
    """
    with np.errstate(over='ignore'):
        difference = np.abs(left - right)
    overflow = np.isinf(difference)
    if np.any(overflow):
        with np.errstate(over='ignore', under='ignore'):
            halved = np.abs(left / 2 - right / 2)
        difference = np.where(overflow, halved, difference)
    mantissa, exponent = np.frexp(difference)
    return mantissa, exponent + overflow.astype(np.int32)


def _offset_ratio(actual, reference, offset, atol, rtol):
    """abs(a-b)/(atol+rtol*abs(b-offset)), without overflowing terms."""
    em, ee = _difference_parts(actual, reference)
    bm, be = _difference_parts(reference, offset)
    am, ae = math.frexp(atol)
    rm, re = math.frexp(rtol)
    # Products use bounded mantissas; exponent sums retain subnormal tolerances.
    relative_m = rm * bm
    relative_e = re + be
    common_e = np.maximum(np.where(relative_m > 0, relative_e, -100000),
                          ae if am else -100000)
    with np.errstate(over='ignore', under='ignore', invalid='ignore', divide='ignore'):
        denominator = (np.ldexp(relative_m, relative_e-common_e) +
                       np.ldexp(np.full_like(bm, am), ae-common_e))
        ratio = np.ldexp(np.divide(em, denominator,
                                  out=np.full_like(em, np.inf), where=denominator > 0),
                         ee-common_e)
    ratio[em == 0] = 0.
    return ratio


def evaluate_field(problem, name, actual, expected, tree):
    spec = problem.manifest['outputs'][name]
    ids = problem.arrays[problem.manifest['locations'][spec['location']]['ids']]
    times = problem.arrays[problem.manifest['time_axes'][spec['time_axis']]]
    weights = {key: problem.arrays[value['array']][0, :, 0]
               for key, value in problem.manifest['fields'].items()
               if value['kind'] == 'scalar' and value['location'] == spec['location']}
    return evaluate_observation(actual, expected, tree, ids=ids, times=times, weights=weights)


def evaluate_observation(actual, expected, tree, *, ids, times, weights=None):
    """Score aligned observations without inventing an input/output manifest."""
    weight_fields = weights or {}
    # Tensor components have the same flattening order as the output contract.
    shape = (actual.shape[0], actual.shape[1], -1)
    actual, expected = actual.reshape(shape), expected.reshape(shape)
    cache = {}

    def statistics(node):
        key = (node['time'], node['components'], node.get('weight_field'),
               node.get('atol', 0), node.get('rtol', 0), node.get('count', 'scalar_values'),
               node.get('reference_offset', 0))
        if key in cache:
            return cache[key]
        weights = None
        if 'weight_field' in node:
            weights = weight_fields[node['weight_field']]
        weight_scale = float(np.max(weights)) if weights is not None else 1.0
        groups = []
        time_groups = [[i] for i in range(len(times))] if node['time'] == 'per_time' else [range(len(times))]
        component_groups = [[i] for i in range(actual.shape[2])] if node['components'] == 'per_component' else [range(actual.shape[2])]
        for ts in time_groups:
            for cs in component_groups:
                def chunks():
                    for t in ts:
                        for start in range(0, actual.shape[1], CHUNK_SIZE):
                            end = min(start + CHUNK_SIZE, actual.shape[1])
                            # Basic slices avoid copying the full field for component selection.
                            sl = slice(cs[0], cs[-1] + 1)
                            yield t, start, actual[t, start:end, sl], expected[t, start:end, sl]
                scale = ref_scale = 0.0
                overflow_difference = False
                for _, _, a, b in chunks():
                    with np.errstate(over='ignore'):
                        delta = np.abs(a - b)
                    if np.any(np.isinf(delta)):
                        overflow_difference = True
                        scale = float(np.finfo(np.float64).max)
                    else:
                        scale = max(scale, float(np.max(delta)))
                    ref_scale = max(ref_scale, float(np.max(np.abs(b))))
                scale = scale or 1.0
                ref_scale = ref_scale or 1.0
                error_sum = ref_sum = weight_sum = 0.0
                failed = count = 0
                maximum = scaled_max = 0.0
                worst = None
                for t, start, a, b in chunks():
                    if overflow_difference:
                        error = np.abs(a / scale - b / scale)
                    else:
                        error = np.abs(a - b) / scale
                    bn = b / ref_scale
                    w = (weights[start:start + len(a)] / weight_scale)[:, None] if weights is not None else np.ones((len(a), 1))
                    error_sum += float(np.sum(w * error**2))
                    ref_sum += float(np.sum(w * bn**2))
                    weight_sum += float(np.sum(w)) * len(cs)
                    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
                        tolerance = np.full_like(error, node.get('atol', 0) / scale)
                        if node.get('rtol', 0):
                            tolerance += node['rtol'] * (np.abs(b) / scale)
                        matches = np.isclose(a, b, atol=node.get('atol', 0), rtol=node.get('rtol', 0))
                        ratio = np.divide(error, tolerance, out=np.full_like(error, np.inf), where=tolerance > 0)
                        ratio[(error == 0) & (tolerance == 0)] = 0
                    if node.get('reference_offset', 0) != 0:
                        ratio = _offset_ratio(a, b, node['reference_offset'],
                                              node.get('atol', 0), node.get('rtol', 0))
                        matches = ratio <= 1.
                    if node.get('count') == 'spatial_points':
                        failed += int(np.count_nonzero(~np.all(matches, axis=1)))
                        count += len(a)
                    else:
                        failed += int(np.count_nonzero(~matches))
                        count += error.size
                    local_index = np.unravel_index(int(np.argmax(error)), error.shape)
                    local_max = float(error[local_index])
                    if worst is None or local_max > maximum:
                        maximum = local_max
                        worst = {'time_index': int(t), 'time': float(times[t]),
                                 'id': int(ids[start + local_index[0]]),
                                 'component_index': int(cs[local_index[1]])}
                    scaled_max = max(scaled_max, float(np.max(ratio)))
                groups.append({'time_index': int(ts[0]) if len(ts) == 1 else None,
                               'component_index': int(cs[0]) if len(cs) == 1 else None,
                               'scale': scale, 'ref_scale': ref_scale, 'rms': math.sqrt(error_sum / weight_sum),
                               'ref_rms': math.sqrt(ref_sum / weight_sum), 'maximum': maximum,
                               'max_scaled': scaled_max, 'failed_values': failed,
                               'total_values': count, 'worst_location': worst})
        cache[key] = groups
        return groups

    def visit(node):
        if 'all' in node or 'any' in node:
            op = 'all' if 'all' in node else 'any'
            children = [visit(child) for child in node[op]]
            passed = all(c['passed'] for c in children) if op == 'all' else any(c['passed'] for c in children)
            return {'operator': op, 'passed': passed, 'children': children}
        metric = node['metric']
        records = []
        for group in statistics(node):
            scale = group['scale']
            limit = node.get('limit', 0)
            if metric in ('pointwise', 'violation_fraction'):
                value = group['failed_values'] / group['total_values']
                passed = group['failed_values'] == 0 if metric == 'pointwise' else value <= limit
            elif metric == 'max_scaled':
                value = group['max_scaled']; passed = value <= limit
            elif metric == 'nrmse':
                denominator_scale = max(group['ref_scale'], node['scale_floor'])
                denominator = max(group['ref_rms'] * (group['ref_scale'] / denominator_scale),
                                  node['scale_floor'] / denominator_scale)
                value = _scaled_ratio(scale, group['rms'], denominator_scale, denominator)
                passed = value <= limit
            else:
                normalized = group['rms'] if metric == 'rmse' else group['maximum']
                value = normalized * scale
                passed = normalized <= limit / scale
            record = {k: group[k] for k in ('time_index', 'component_index', 'worst_location')}
            record.update(value=_number(value), passed=bool(passed))
            if metric in ('pointwise', 'violation_fraction'):
                record.update(failed_values=group['failed_values'], total_values=group['total_values'])
            records.append(record)
        return {'condition': node, 'passed': all(r['passed'] for r in records), 'groups': records}
    return visit(tree)
