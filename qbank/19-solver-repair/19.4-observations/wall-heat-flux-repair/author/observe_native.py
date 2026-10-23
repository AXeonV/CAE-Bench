"""Author-only observation: retain temporary native files without changing values."""
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import shutil
import sys

spec = importlib.util.spec_from_file_location('public_driver', '/task/public/run_case.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
original_temp = driver.tempfile.TemporaryDirectory
original_run = driver.subprocess.run
destination = Path('/outputs/native')


@contextmanager
def observed_temp(*args, **kwargs):
    with original_temp(*args, **kwargs) as directory:
        try:
            yield directory
        finally:
            shutil.copytree(directory, destination, dirs_exist_ok=True)


def observed_run(*args, **kwargs):
    result = original_run(*args, **kwargs)
    directory = Path(kwargs['cwd'])
    (directory/'stdout.log').write_text(result.stdout)
    (directory/'stderr.log').write_text(result.stderr)
    return result


driver.tempfile.TemporaryDirectory = observed_temp
driver.subprocess.run = observed_run
driver.run(Path(sys.argv[1]), Path('/outputs/result.h5'), '/opt/su2-build/SU2_CFD/src/SU2_CFD')
