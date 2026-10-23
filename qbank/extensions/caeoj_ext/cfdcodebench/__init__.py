"""Public declarations for the fixed CFDCodeBench compatibility models."""
from functools import lru_cache
from importlib.resources import files
import json
import numpy as np

@lru_cache(None)
def models():return json.loads(files(__package__).joinpath('models.json').read_text(encoding='utf-8'))

def check(problem,errors):
    from caeoj.validation import issue
    m,a=problem.manifest,problem.arrays
    cfg=models().get(m.get('physics',{}).get('model'))
    def fail(path,expected,actual):errors.append(issue('E_CFDCODEBENCH',path,expected,actual,'Declaration violates this task DATA.'))
    if cfg is None:fail('$.physics.model','registered CFDCodeBench model',m.get('physics'));return
    if m.get('task')!=cfg['task']:fail('$.task',cfg['task'],m.get('task'))
    if m['spatial_dimension']!=cfg['dimension']:fail('$.spatial_dimension',cfg['dimension'],m['spatial_dimension'])
    if m['physics'].get('parameters',{})!={}:fail('$.physics.parameters',{},m['physics'].get('parameters'))
    if m['meshes'] or m['geometries'] or m['conditions']:fail('$','analytic domain and conditions fixed in DATA','extra geometry/conditions')
    if set(m['locations'])!={'observations'} or set(m['time_axes'])!={'output'}:fail('$','one observations location and output time axis','wrong axes');return
    if not np.array_equal(a[m['time_axes']['output']],np.array([cfg['time']])):fail('$.time_axes.output',[cfg['time']],'wrong time')
    loc=m['locations']['observations'];ids=a[loc['ids']]
    if loc['kind']!=('entities' if cfg['index']==23 else 'points'):fail('$.locations.observations.kind','task observation kind',loc['kind']);return
    if not 1<=len(ids)<=65536 or cfg['index']==23 and len(ids)!=1:fail('$.locations.observations','1..65536 points, or one EVP entity',len(ids))
    if loc['kind']=='points':
        xy=a[loc['coordinates']];d=cfg['domain'];index=cfg['index']
        if index==19:
            r=np.hypot(xy[:,0],xy[:,1]);inside=np.all((r>.5)&(r<10))
        elif cfg['dimension']==2:
            inside=np.all((xy[:,0]>d[0])&(xy[:,0]<d[1])&(xy[:,1]>d[2])&(xy[:,1]<d[3]))
        else:inside=np.all((xy[:,0]>=d[0])&(xy[:,0]<=d[1]))
        if not inside:fail('$.locations.observations','points in declared domain','outside / forbidden 2D boundary sample')
    if set(m['fields'])!={'weights'}:fail('$.fields',['weights'],list(m['fields']));return
    if set(m['outputs'])!=set(cfg['fields']):fail('$.outputs',cfg['fields'],list(m['outputs']));return
    for name,spec in {**m['fields'],**m['outputs']}.items():
        expected=dict(kind='scalar',component_shape=[1],components=['value'],dtype='float64',unit='1',
                      location='observations',time_axis='output',value_kind='point',
                      quantity='observation_weight' if name=='weights' else name)
        for key,value in expected.items():
            if spec.get(key)!=value:fail('$.fields_or_outputs.'+name+'.'+key,value,spec.get(key))
    w=a[m['fields']['weights']['array']]
    if np.any(w<=0):fail('$.fields.weights','strictly positive quadrature weights','nonpositive')
