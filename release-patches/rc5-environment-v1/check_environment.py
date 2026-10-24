"""Fail closed when the numerical execution environment lacks promised tools."""
import importlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

MODULES = ('numpy', 'scipy', 'h5py', 'gmsh', 'jsonschema')
COMMANDS = ('bash', 'git', 'curl', 'g++', 'mpic++', 'mpirun', 'h5cc', 'h5c++', 'setpriv')


def command(arguments, cwd=None):
    result = subprocess.run(arguments, cwd=cwd, text=True, capture_output=True, timeout=30)
    if result.returncode:
        raise RuntimeError(f'Environment command failed: {arguments[0]}: {result.stderr}')
    return result.stdout.strip()


def check():
    versions = {}
    for name in MODULES:
        importlib.import_module(name)
        versions[name] = importlib.metadata.version(name)
    binaries = {}
    for name in COMMANDS:
        path = shutil.which(name)
        if path is None:
            raise RuntimeError('Missing promised environment command: ' + name)
        binaries[name] = path
    import numpy as np
    from scipy.sparse import csc_matrix
    from scipy.sparse.linalg import spsolve
    import h5py
    import gmsh
    if not np.allclose(spsolve(csc_matrix([[2., 0.], [0., 4.]]), [2., 8.]), [1., 2.]):
        raise RuntimeError('SciPy sparse solve functional check failed')
    with tempfile.TemporaryDirectory(prefix='caeoj-environment-') as directory:
        root = Path(directory)
        with h5py.File(root/'probe.h5', 'w') as output:
            output['values'] = np.array([1., 2.])
        with h5py.File(root/'probe.h5') as data:
            if not np.array_equal(data['values'][...], [1., 2.]):
                raise RuntimeError('HDF5 read/write functional check failed')
        (root/'openmp.cpp').write_text('#include <omp.h>\nint main(){int n=0;\n#pragma omp parallel num_threads(2) reduction(+:n)\n{n+=1;}\nreturn n!=2;}\n')
        command(['g++', '-fopenmp', 'openmp.cpp', '-o', 'openmp'], root)
        command([str(root/'openmp')], root)
        (root/'hdf5.cpp').write_text('#include <hdf5.h>\nint main(){hid_t f=H5Fcreate("native.h5",H5F_ACC_TRUNC,H5P_DEFAULT,H5P_DEFAULT);if(f<0)return 1;H5Fclose(f);f=H5Fopen("native.h5",H5F_ACC_RDONLY,H5P_DEFAULT);if(f<0)return 2;return H5Fclose(f)<0;}\n')
        command(['h5c++', 'hdf5.cpp', '-o', 'hdf5'], root)
        command([str(root/'hdf5')], root)
        (root/'mpi.cpp').write_text('#include <mpi.h>\nint main(int n,char**v){MPI_Init(&n,&v);int s=0,r=0,total=0;MPI_Comm_size(MPI_COMM_WORLD,&s);MPI_Comm_rank(MPI_COMM_WORLD,&r);MPI_Allreduce(&r,&total,1,MPI_INT,MPI_SUM,MPI_COMM_WORLD);MPI_Finalize();return s!=2||total!=1;}\n')
        command(['mpic++', 'mpi.cpp', '-o', 'mpi'], root)
        command(['mpirun', '--allow-run-as-root', '--oversubscribe', '-n', '2', str(root/'mpi')], root)
    gmsh.initialize(['caeoj-environment-check', '-nopopup'])
    try:
        gmsh.model.add('environment-check')
        gmsh.model.geo.addPoint(0, 0, 0)
        gmsh.model.geo.synchronize()
    finally:
        gmsh.finalize()
    return {'status': 'passed', 'modules': versions, 'commands': binaries,
            'functional_checks': ['scipy-sparse', 'hdf5-read-write', 'gmsh-api', 'cxx-openmp-two-threads', 'hdf5-native-file-io', 'mpi-two-rank-reduction']}


if __name__ == '__main__':
    print(json.dumps(check(), sort_keys=True))
