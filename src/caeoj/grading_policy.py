"""Versioned public grading policy, validation and participant descriptions."""
import hashlib
import json
import math
from pathlib import Path

import jsonschema
import numpy as np

UNSET = object()
METRICS = ('pointwise', 'rmse', 'nrmse', 'max_abs', 'max_scaled', 'violation_fraction')


def parse_policy(text):
    def reject(token):
        raise ValueError(f'Nonfinite grading JSON token: {token}')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'Duplicate grading JSON key: {key}')
            result[key] = value
        return result
    policy = json.loads(text, parse_constant=reject,
                        object_pairs_hook=unique)
    validate_policy(policy)
    return policy


def load_policy(path):
    return parse_policy(Path(path).read_text(encoding='utf-8'))


def validate_policy(policy, problem=None):
    schema = json.loads(Path(__file__).with_name('grading.schema.json').read_text())
    try:
        jsonschema.Draft202012Validator(schema).validate(policy)
    except RecursionError as exc:
        raise ValueError('Grading condition nesting is too deep') from exc
    except jsonschema.ValidationError as exc:
        raise ValueError(f'Invalid grading policy at {list(exc.absolute_path)}: {exc.message}') from exc
    def walk(node, depth=0):
        if depth > 32:
            raise ValueError('Grading condition nesting exceeds 32')
        if 'all' in node or 'any' in node:
            for child in node.get('all', node.get('any')):
                walk(child, depth + 1)
        else:
            for value in node.values():
                if isinstance(value, (float, int)):
                    try:
                        finite = math.isfinite(value)
                    except OverflowError:
                        finite = False
                    if not finite:
                        raise ValueError('Grading numbers must be finite')
            if node.get('count') == 'spatial_points' and node['components'] != 'joint':
                raise ValueError('spatial_points requires joint components')
    for tree in policy['fields'].values():
        walk(tree)
    if problem is None:
        return policy
    outputs = problem.manifest['outputs']
    floating = {k for k, v in outputs.items() if v['dtype'] == 'float64'}
    if set(policy['fields']) != floating:
        raise ValueError(f'Policy must cover exactly floating outputs: {sorted(floating)}')
    def bind(node, spec):
        if 'all' in node or 'any' in node:
            for child in node.get('all', node.get('any')):
                bind(child, spec)
        elif 'weight_field' in node:
            weight_spec = problem.manifest['fields'].get(node['weight_field'])
            if (not weight_spec or weight_spec['location'] != spec['location'] or
                    weight_spec['dtype'] != 'float64' or weight_spec['kind'] != 'scalar'):
                raise ValueError('Weight field must be a float64 scalar at the output location')
            weights = problem.arrays[weight_spec['array']]
            # Output arrays are not normally input arrays. The location's IDs give N.
            location = problem.manifest['locations'][spec['location']]
            n = len(problem.arrays[location['ids']])
            if weights.shape != (1, n, 1) or not np.all(np.isfinite(weights)) or not np.all(weights > 0):
                raise ValueError('Weight field must have shape [1,N,1] and finite positive values')
    for name, tree in policy['fields'].items():
        bind(tree, outputs[name])
    return policy


def policy_hash(policy):
    validate_policy(policy)
    return hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def legacy_policy(problem, atol, rtol):
    return {'version': 1, 'fields': {
        name: {'metric': 'pointwise', 'time': 'per_time', 'components': 'per_component',
               'atol': atol, 'rtol': rtol}
        for name, spec in problem.manifest['outputs'].items() if spec['dtype'] == 'float64'}}


def render_policy(policy):
    """Describe exactly the same tree used by the grader, without author metadata."""
    validate_policy(policy)
    def describe(node):
        if 'all' in node or 'any' in node:
            op = ' 且 ' if 'all' in node else ' 或 '
            return '(' + op.join(describe(c) for c in node.get('all', node.get('any'))) + ')'
        metric = node['metric']
        scope = ('每个输出时刻' if node['time'] == 'per_time' else '合并全部输出时刻')
        scope += '、' + ('每个分量分别计算' if node['components'] == 'per_component' else '合并全部分量')
        tolerance = f"|输出−参考| ≤ {node.get('atol')} + {node.get('rtol')}×|参考|"
        if metric == 'pointwise':
            text = '全部值满足 ' + tolerance
        elif metric == 'violation_fraction':
            count = '空间点（该点所有分量均满足才算通过）' if node.get('count') == 'spatial_points' else '标量值'
            text = f"不满足 {tolerance} 的{count}比例 ≤ {node['limit']}"
        elif metric == 'max_scaled':
            text = f"max(|误差|/(atol+rtol×|参考|)) ≤ {node['limit']}，atol={node['atol']}，rtol={node['rtol']}"
        elif metric == 'nrmse':
            text = f"RMSE / max(参考 RMS, {node['scale_floor']}) ≤ {node['limit']}"
        else:
            text = f"{'RMSE' if metric == 'rmse' else '最大绝对误差'} ≤ {node['limit']}"
        weight = f"，按输入字段 {node['weight_field']} 加权" if 'weight_field' in node else '，等采样权重'
        return f'[{scope}{weight}：{text}；所有计算范围均须达标]'
    lines = ['所有输出字段均须通过各自规则；整数和布尔场精确一致，IDs、时间轴和结构严格匹配。',
             'RMSE、最大绝对误差和 scale_floor 使用字段单位；NRMSE、比例及缩放误差无量纲。',
             'RMSE=√加权平均(误差²)，参考 RMS=√加权平均(参考²)。所有阈值包含等号。',
             '合并时刻采用等时刻权重；空间权重仅影响 RMS，比例按数量计数。',
             '缩放误差分母为零时，零误差记为0，非零误差记为∞。']
    lines.extend(f'- `{name}`：{describe(tree)}。' for name, tree in sorted(policy['fields'].items()))
    return '\n'.join(lines) + '\n'


def task_policy(task_dir, problem, *, read_bytes=None):
    """Resolve public policy or legacy tolerances; prohibit ambiguous sources."""
    task_dir = Path(task_dir)
    read = read_bytes or (lambda path: path.read_bytes())
    config_path = task_dir / 'judge-config.json'
    config = json.loads(read(config_path)) if config_path.is_file() else {}
    path = task_dir / 'grading.json'
    if path.is_file():
        if 'atol' in config or 'rtol' in config:
            raise ValueError('grading.json and legacy judge-config atol/rtol cannot coexist')
        policy = parse_policy(read(path))
    else:
        # Import here to keep grading's legacy public API independent of task assembly.
        from .grading import _tolerance, DEFAULT_ATOL, DEFAULT_RTOL
        tolerance = _tolerance(config.get('atol', DEFAULT_ATOL), config.get('rtol', DEFAULT_RTOL))
        policy = legacy_policy(problem, **tolerance)
    validate_policy(policy, problem)
    return policy
