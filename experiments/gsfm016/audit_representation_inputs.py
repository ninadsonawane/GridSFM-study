"""No forwards: audit converter graph equivalence before interpreting row-order controls."""
from pathlib import Path
import json
R=Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=R/'results/comparisons/GSFM-016/20261024-electrical-mechanisms';S=R/'results/comparisons/GSFM-015/20261023-load-location-charging';m=json.loads((O/'scenario-manifest.json').read_text());out=[]
for x in m['scenarios']:
 if x['family']!='representation':continue
 mp=x['representation_mapping'];bm=mp['bus_to_base_rows'];gm=mp['gen_to_base_rows'];em=mp['branch_to_base_rows']
 for rel in ['microsoft-v1.1','newer-base-v2']:
  a=json.loads((O/x['id']/(rel+'-input.pyg.json')).read_text());b=json.loads((S/x['baseline']/(rel+'-input.pyg.json')).read_text());assert 'solution' not in a and 'solution' not in b;A=a['grid'];B=b['grid'];assert A['context']==B['context']
  for i,j in enumerate(bm):assert A['nodes']['bus'][i]==B['nodes']['bus'][j]
  ag=a['metadata']['gen_source_rows'];bg=b['metadata']['gen_source_rows'];bglook={j:i for i,j in enumerate(bg)}
  for i,src in enumerate(ag):
   j=bglook[gm[src]];assert A['nodes']['generator'][i]==B['nodes']['generator'][j];ea=A['edges']['generator_link'];eb=B['edges']['generator_link'];assert ea['senders'][i]==i and eb['senders'][j]==j;assert bm[ea['receivers'][i]]==eb['receivers'][j]
  for family in ['load','shunt']:
   ea=A['edges'][family+'_link'];eb=B['edges'][family+'_link'];aa={bm[v]:A['nodes'][family][u] for u,v in zip(ea['senders'],ea['receivers'])};bb={v:B['nodes'][family][u] for u,v in zip(eb['senders'],eb['receivers'])};assert aa==bb
  for family in ['ac_line','transformer']:
   ar=a['metadata'][family+'_source_rows'];br=b['metadata'][family+'_source_rows'];look={v:i for i,v in enumerate(br)};ea=A['edges'][family];eb=B['edges'][family]
   for i,v in enumerate(ar):
    j=look[em[v]];assert ea['features'][i]==eb['features'][j];assert [bm[ea['senders'][i]],bm[ea['receivers'][i]]]==[eb['senders'][j],eb['receivers'][j]]
  out.append({'scenario':x['id'],'release':rel,'status':'PASS','all_node_raw_features_exact_after_map':True,'all_branch_raw_features_and_direction_exact_after_map':True,'generator_load_shunt_link_endpoints_exact_after_map':True,'no_solution_fields':True,'new_forward_calls':0,'scope':'Raw converted graph. Differences arising in released positional/cycle feature preparation or model internals not isolated by this check.'})
(O/'representation-input-audit.json').write_text(json.dumps(out,indent=2)+'\n');print('8 RAW CONVERTED-GRAPH EQUIVALENCE AUDITS PASS; no forwards')
