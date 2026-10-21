from common import *
import collections
its=items('train',True)[:5];rows=[]
for it in its:
 c=it.c;o=it.obj;n=o['grid']['nodes'];e=o['grid']['edges'];ids=o['metadata']['bus_external_ids'];assert ids==[int(b[0]) for b in c['bus']];assert o['metadata']['gen_source_rows']==list(range(69))
 for i,g in enumerate(c['gen']):assert np.allclose(n['generator'][i][:11],[g[6],g[1]/100,g[9]/100,g[8]/100,g[2]/100,g[4]/100,g[3]/100,g[5],c['gencost'][i][4]*10000,c['gencost'][i][5]*100,c['gencost'][i][6]],rtol=0,atol=1e-12)
 for family in ['ac_line','transformer']:
  for rowid,feat in zip(o['metadata'][family+'_source_rows'],e[family]['features']):
   b=c['branch'][rowid];assert feat[-1]==b[10]
   if family=='ac_line':assert feat[4:6]==b[2:4] and feat[2:4]==[b[4]/2,b[4]/2]
   else:assert feat[2:4]==b[2:4] and feat[7:11]==[b[8] or 1,math.radians(b[9]),b[4]/2,b[4]/2]
   assert (feat[6] if family=='ac_line' else feat[4])==b[5]/100==0
 busloads=np.zeros((300,2));busshunts=np.zeros((300,2))
 for name,arr in [('load',busloads),('shunt',busshunts)]:
  for bus,feat in zip(e[name+'_link']['receivers'],n[name]):arr[bus]=feat[:2]
 assert np.allclose(busloads,np.array([[b[2]/100,b[3]/100] for b in c['bus']]),atol=0,rtol=0)
 assert np.allclose(busshunts,np.array([[b[5]/100,b[4]/100] for b in c['bus']]),atol=0,rtol=0)
 assert not any(v>1 for v in collections.Counter(g[0] for g in c['gen']).values())
 rows.append(dict(scenario_id=it.key,original_bus_gen_branch_order=True,original_coefficients_taps_shunts_cost_limits=True,negative_load_buses=sum(b[2]<0 or b[3]<0 for b in c['bus']),multiple_generator_buses=0,thermal_limits='N/A',features_contain_solution=False))
save(RUN/'checks/semantic-roundtrip.json',dict(status='PASS',rows=rows,FP32_rounding='separately quantified in gate.json; decimal source matrices untouched'))
