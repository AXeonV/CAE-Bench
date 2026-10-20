"""Build a read-only Elmer input reader and map supplied P0 KE data to P1."""
import os
from pathlib import Path
import shutil
import subprocess
import time
import numpy as np
from native_closed_cavity import SOCKET, save, digest
from native_gas_film import IMAGE
from native_lowmach import cell_source
from titan_resources import reservation


def build(root):
    work = root/'maintenance/initial-ke-reader'; work.mkdir(exist_ok=True)
    source = Path(__file__).with_name('InitialKE.F90')
    library = work/'CAEInitialFields.so'
    if library.exists():
        import json
        record = json.loads((work/'build.json').read_text())
        assert record['source_sha256'] == digest(source) and record['library_sha256'] == digest(library)
        return library
    shutil.copy2(source, work/source.name)
    name = 'ch02-initial-ke-build-'+str(time.time_ns())
    with reservation(root, name):
        command = ['docker', '--host', SOCKET, 'run', '--name', name, '--network', 'none', '--cpus', '1', '--memory', '768m', '--user', f'{os.getuid()}:{os.getgid()}', '-v', f'{work.resolve()}:/work', '-w', '/work', IMAGE, 'bash', '-c', '/opt/elmer/bin/elmerf90 -shared InitialKE.F90 -o CAEInitialFields.so']
        with (work/'build.log').open('w') as log: cp = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        assert cp.returncode == 0 and library.exists(), 'native input reader build failed; inspect build.log'
    save(work/'build.json', {'image': IMAGE, 'command': command, 'source_sha256': digest(source), 'library_sha256': digest(library), 'scope': 'Read-only input adapter; no physical evolution or PDE implementation', 'numerical_validation': False})
    return library


def apply(job, e, data, text):
    m = data[0]; x = m['x']; c = m['c']; volume = m['volume']; initial = e['detailed_spec']['initial']
    values = {q: cell_source(initial[q]['expression'], x, c, 0, e['detailed_spec']) for q in ('turbulent_kinetic_energy', 'turbulence_length_scale')}
    assert all(np.isfinite(a).all() and np.min(a) > 0 for a in values.values())
    np.savez(job/'initial-ke-input.npz', **values)
    weights = np.zeros(len(x)); nodes = {}
    for j in range(c.shape[1]): np.add.at(weights, c[:, j], volume/c.shape[1])
    assert np.min(weights) > 0
    for q, a in values.items():
        numerator = np.zeros(len(x))
        for j in range(c.shape[1]): np.add.at(numerator, c[:, j], a*volume/c.shape[1])
        nodes[q] = numerator/weights
    k = nodes['turbulent_kinetic_energy']; eps = .09**.75*k**1.5/nodes['turbulence_length_scale']
    with (job/'native/initial-ke.dat').open('w') as f:
        f.write(str(len(x))+'\n')
        for i, (a,b) in enumerate(zip(k,eps)): f.write(f'{i+1} {a:.17g} {b:.17g}\n')
    library = job.parents[1]/'maintenance/initial-ke-reader/CAEInitialFields.so'
    shutil.copy2(library, job/'native/CAEInitialFields.so')
    lines = text.splitlines(); result = []
    for line in lines:
        if line.startswith('Kinetic Energy = Real '): result += ['Kinetic Energy = Variable Coordinate 1', 'Real Procedure "./CAEInitialFields" "InitialK"']
        elif line.startswith('Kinetic Dissipation = Real '): result += ['Kinetic Dissipation = Variable Coordinate 1', 'Real Procedure "./CAEInitialFields" "InitialEpsilon"']
        else: result.append(line)
    save(job/'initial-ke-mapping.json', {'input_sha256': digest(job/'initial-ke-input.npz'), 'native_data_sha256': digest(job/'native/initial-ke.dat'), 'library_sha256': digest(library), 'source_sha256': digest(Path(__file__).with_name('InitialKE.F90')), 'mapping': 'Frozen expressions construct supplied P0 simplex values using the existing fixed barycentric quadrature. Volume-lumped P0-to-P1 projection initializes native nodal k and length; epsilon=.09^.75*k^1.5/length. Reader only returns stored nodal values. Projection and near-wall initialization error unvalidated.', 'numerical_validation': False})
    return '\n'.join(result)+'\n'
