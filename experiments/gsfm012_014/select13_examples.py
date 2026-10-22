"""Apply literal protocol cap: six examples per component/release across networks."""
from electrical import *
O=R/'results/diagnosis/GSFM-013/20261023-accuracy-sensitivity';eligible=list(csv.DictReader((O/'eligible-high-low-pairs.csv').open()));selections=[]
for rel in ['newer-base-v2','microsoft-v1.1']:
 for co in ['P','Q']:
  matches=[x for x in eligible if x['release']==rel and x['component']==co];matches.sort(key=lambda x:(float(x['normalized_source_distance']),int(x['high_bus']),int(x['low_bus']),x['network']));selections+=matches[:6]
csvsave(O/'matched-examples.csv',selections);rows=list(csv.DictReader((O/'bus-decomposition.csv').open()));tracking=[]
for p in selections:
 for r in rows:
  if r['network']==p['network'] and r['release']==p['release'] and r['bus_id'] in [p['high_bus'],p['low_bus']]:tracking.append(dict(pair_high=p['high_bus'],pair_low=p['low_bus'],pair_component=p['component'],**r))
csvsave(O/'load-tracking.csv',tracking);g=read(O/'gates.json');g['selected_example_pairs']=len(selections);g['example_cap']='Six per component/release across both networks combined; distance then high/low IDs, network final tie';save(O/'gates.json',g);print('PROTOCOL EXAMPLES',len(selections),[(r['network'],r['release'],r['component'],r['high_bus'],r['low_bus']) for r in selections])
