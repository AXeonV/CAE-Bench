"""Exercise the actual public SDK installed by the fixed verifier image, from /tmp.

The image contains the genuine defective baseline: both public numerical grades
must be zero, while all input/output validation and native execution must work.
"""
import json
from pathlib import Path
import subprocess
import sys

import caeoj
import caeoj_bundle
import h5py
import numpy

PUBLIC=Path('/app/qbank/19-solver-repair/19.2-operators/grand-potential-derivatives-repair')


def main():
    assert '/site-packages/' in caeoj.__file__ and '/site-packages/' in caeoj_bundle.__file__
    assert numpy.__version__=='2.4.6' and h5py.__version__=='3.16.0'
    report={'installed_core':caeoj.__file__,'installed_bundle':caeoj_bundle.__file__,
            'python':sys.executable,'numpy':numpy.__version__,'h5py':h5py.__version__,
            'meaning':'Original defective baseline, not a repaired candidate. Numeric score zero is required; CLI input/output validity and actual native runs succeed.', 'samples':[]}
    def run(command,expected):
        actual=['setpriv','--reuid=1000','--regid=1000','--clear-groups','--no-new-privs',
                'env','-i','PATH=/usr/local/bin:/usr/bin:/bin','HOME=/home/solver',*command]
        r=subprocess.run(actual,cwd='/tmp',capture_output=True,text=True,timeout=40)
        assert r.returncode==expected,(command,r.returncode,r.stdout[-1000:],r.stderr[-1000:])
        return {'command':command,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
    for sample in ['01','02']:
        source=PUBLIC/'samples'/sample/'input/problem.json';target=f'/tmp/public-sample-{sample}.h5'
        commands=[]
        commands.append(run(['/usr/local/bin/python','-m','caeoj','validate-input',str(source)],0))
        commands.append(run(['/usr/local/bin/python',str(PUBLIC/'public/run_case.py'),'--input',str(source),'--output',target],0))
        commands.append(run(['/usr/local/bin/python','-m','caeoj','validate-output','--input',str(source),'--output',target],0))
        commands.append(run(['/usr/local/bin/python','-m','caeoj','grade','--input',str(source),'--output',target,'--grading',str(PUBLIC/'samples'/sample/'reference/grading.json')],1))
        assert json.loads(commands[-1]['stdout'])['score']==0
        report['samples'].append({'sample':sample,'commands':commands})
    print(json.dumps(report))


if __name__=='__main__':main()
