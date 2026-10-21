"""Translate stock Feel++ batched point-column names; no field calculation or PDE."""
def remap_batch_row(row, layout, dimension=3):
    result = {key: value for key, value in row.items() if not key.startswith('Points_')}
    consumed = set(result)
    for group, original_names in layout['groups'].items():
        for index, name in enumerate(original_names):
            suffixes = ['coordinates_' + str(k) for k in range(dimension)]
            suffixes += ['field_velocity_' + str(k) for k in range(dimension)]
            if group == 'midpoints':
                suffixes.append('field_pressure')
            for suffix in suffixes:
                native = f'Points_{group}_{index}_{suffix}'
                if native not in row:
                    raise ValueError('Missing native batch column: ' + native)
                result[f'Points_{name}_{suffix}'] = row[native]
                consumed.add(native)
    if consumed != set(row):
        raise ValueError('Unmapped native columns: ' + str(sorted(set(row) - consumed)[:8]))
    return result
