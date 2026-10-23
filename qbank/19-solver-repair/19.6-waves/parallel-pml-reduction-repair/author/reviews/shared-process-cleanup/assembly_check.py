"""Verify the real prepare_harbor fixture copy, outside active qbank tasks."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tests'))
import test_harbor
case=test_harbor.HarborTests('test_build_context_contains_only_public_release')
try:
    case.setUp()
    staged=case.prepared()/'tests/judge.py'
    source=ROOT/'src/utils/harbor/tests/judge.py'
    expected=source.read_bytes().replace(b'\r\n',b'\n')
    assert staged.read_bytes()==expected
    assert b"'--supervise'" in staged.read_bytes()
    print(json.dumps({'passed':True,'fixture_only':True,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'staged_lf_sha256':hashlib.sha256(staged.read_bytes()).hexdigest(),'bytes_equal_after_documented_lf_normalization':True}))
finally:case.doCleanups()
