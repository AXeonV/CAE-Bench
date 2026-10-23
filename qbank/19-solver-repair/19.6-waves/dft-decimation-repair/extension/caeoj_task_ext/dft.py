"""Check the public finite-window DFT declaration; never compute a spectrum."""
import numpy as np
PARAMETERS={'length','resolution','pml_width','source_frequency','envelope_width','source_amplitude','cutoff','after_sources','chi2','chi3','nonlinear_lo','nonlinear_hi','num_chunks','decimation','monitor_index'}
INTEGERS={'resolution','envelope_width','cutoff','after_sources','num_chunks','decimation','monitor_index'}
def descriptor(name,quantity,components,output=False):
 return {'array':name,'quantity':quantity,'unit':'1','location':'probes','time_axis':'instant','dtype':'float64','kind':'scalar' if len(components)==1 else 'components','component_shape':[len(components)],'components':components,'value_kind':'point'}
def descriptions():
 return {'frequency':descriptor('frequency','normalized_frequency',['value'])},{'observed_dft':descriptor('observed_dft','normalized_finite_dft',['Ex_real','Ex_imag','Hy_real','Hy_imag'],True),'sampling_stride':descriptor('sampling_stride','sampling_stride',['value'],True),'time_step':descriptor('time_step','normalized_time_step',['value'],True),'window_end':descriptor('window_end','normalized_window_end',['value'],True)}
def check(problem,errors):
 from caeoj.validation import issue
 m=problem.manifest;a=problem.arrays
 def fail(path,expected,actual):errors.append(issue('E_DFT_WINDOW',path,expected,actual,'Outside the public finite-window DFT DATA contract.'))
 physics=m.get('physics',{});par=physics.get('parameters',{})
 if m.get('task')!='dft-decimation-repair' or m['spatial_dimension']!=1 or physics.get('model')!='finite-window-dft-v1' or set(par)!=PARAMETERS:
  fail('$.physics','finite-window-dft-v1 and exact normalized parameters',physics);return
 values={}
 for n,item in par.items():
  if set(item)!= {'value','unit'} or item.get('unit')!='1' or type(item.get('value')) not in (int,float) or not np.isfinite(item['value']) or n in INTEGERS and type(item['value']) is not int:
   fail('$.physics.parameters.'+n,'normalized finite scalar; specified integers are JSON integers',item);return
  values[n]=item['value']
 v=values;bounds={'length':(20,100),'resolution':(10,30),'pml_width':(1,5),'source_frequency':(.2,.5),'envelope_width':(20,80),'cutoff':(5,6),'after_sources':(20,160),'chi2':(-.03,.03),'chi3':(0,.03),'num_chunks':(1,3),'decimation':(0,8)}
 for n,(lo,hi) in bounds.items():
  if not lo<=v[n]<=hi:fail('$.physics.parameters.'+n,f'{lo}..{hi}',v[n])
 if errors:return
 n=v['length']*v['resolution'];pml=v['pml_width']*v['resolution']
 if n!=round(n) or int(round(n))%2 or n>3000 or pml!=round(pml) or 2*v['pml_width']+2>=v['length']:fail('$.physics.parameters','even integral cells<=3000; integral PML cells and nonempty interior',v)
 if not .25<=abs(v['source_amplitude'])<=1:fail('$.physics.parameters.source_amplitude','absolute amplitude in[.25,1]',v['source_amplitude'])
 if not -v['length']/2<=v['nonlinear_lo']<v['nonlinear_hi']<=v['length']/2:fail('$.physics.parameters','ordered nonlinear interval within cell',v)
 if not pml+2<=v['monitor_index']<=n-pml-2:fail('$.physics.parameters.monitor_index','centered sample strictly inside non-PML region',v['monitor_index'])
 if m['geometries'] or m['meshes'] or m['conditions']:fail('$.geometries','no explicit geometry, mesh or conditions',m['geometries'])
 if m['locations']!={'probes':{'kind':'points','ids':'probe_ids','coordinates':'probe_coordinates'}} or m['time_axes']!={'instant':'times'} or not np.array_equal(a.get('times'),[0.]):fail('$.locations','one probes table and zero static label',m['locations']);return
 inputs,outputs=descriptions()
 if m['fields']!=inputs or m['outputs']!=outputs:fail('$.fields/outputs','exact finite-window descriptors',{'fields':m['fields'],'outputs':m['outputs']});return
 if set(a)!= {'probe_ids','probe_coordinates','times','frequency'} or not 3<=len(a['probe_ids'])<=128:fail('$.data_file','3..128 frequency-labelled probes, exact input keys',list(a));return
 frequency=a['frequency'][0,:,0]
 if frequency.min()<.05 or frequency.max()>2 or np.any(np.diff(frequency)<=0):fail('$.fields.frequency','strictly increasing normalized frequencies .05..2',frequency)
 point=(2*v['monitor_index']+1-int(round(n)))/(2*v['resolution'])
 if not np.all(a['probe_coordinates'][:,0]==point):fail('$.locations.probes','all frequency-labelled requests at declared centered point',a['probe_coordinates'])
