"""Run the functional environment gate, then optionally start a command."""
import importlib.metadata
import json
from pathlib import Path
import runpy
import subprocess
import sys

def main():
    if importlib.metadata.version('scipy') != '1.18.1':
        raise RuntimeError('RC5 patch requires scipy==1.18.1; install runtime-requirements.txt first')
    check=runpy.run_path(str(Path(__file__).with_name('check_environment.py')))['check']
    report=check()
    print(json.dumps(report,sort_keys=True),flush=True)
    arguments=sys.argv[1:]
    if arguments:
        if arguments[0]!='--' or len(arguments)==1:
            raise RuntimeError('Usage: python gate.py [-- COMMAND ARGUMENTS...]')
        return subprocess.call(arguments[1:])
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('RC5 ENVIRONMENT ERROR (not a candidate score): '+str(exc),file=sys.stderr)
        sys.exit(2)
