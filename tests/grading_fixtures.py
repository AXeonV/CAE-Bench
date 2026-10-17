"""Disposable case assets for numerical tests; use the actual case evaluator."""
from copy import copy
import json
from pathlib import Path
import shutil
import tempfile

from caeoj.case_grading import direct_config, prepare_case
from caeoj.grading_policy import validate_policy
from caeoj.storage import write_hdf5
from caeoj.validation import ContractError


def pointwise_policy(*, atol, rtol):
    return {'version': 2, 'default': {'metric': 'pointwise', 'time': 'per_time',
            'components': 'per_component', 'atol': atol, 'rtol': rtol}}


def evaluate_arrays(problem, actual, reference, *, policy):
    """Materialize a test case; preflight configuration errors propagate."""
    validate_policy(policy, problem)
    with tempfile.TemporaryDirectory(prefix='caeoj-grading-fixture-') as temporary:
        root = Path(temporary)
        snapshot = copy(problem)
        snapshot.path = root/'input/problem.json'
        snapshot.path.parent.mkdir()
        snapshot.path.write_text(json.dumps(problem.manifest), encoding='utf-8')
        write_hdf5(snapshot.path.parent/problem.manifest['data_file'], problem.arrays)
        for table in ('meshes', 'geometries'):
            for spec in problem.manifest[table].values():
                target = snapshot.path.parent/spec['file']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(problem.path.parent/spec['file'], target)
        assets = root/'reference'
        assets.mkdir()
        write_hdf5(assets/'reference.h5', reference)
        config = assets/'grading.json'
        config.write_text(json.dumps(direct_config(policy)), encoding='utf-8')
        try:
            return prepare_case(snapshot, config).evaluate(actual)
        except ContractError as exc:
            return {'status': 'evaluation_error', 'score': None, 'contract': exc.report}
