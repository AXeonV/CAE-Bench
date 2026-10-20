"""Disposable public-runtime installation inputs; no numerical reference claim."""
from test_cfdcodebench import fixture as _fixture
from caeoj_ext.cfdcodebench import models

def fixture(path,slug):
    cfg=next(c for c in models().values() if c['task']==slug)
    _fixture(path,cfg['index'])
