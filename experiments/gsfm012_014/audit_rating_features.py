"""Preprocessing audit only; no checkpoint loading or neural forward."""
import pathlib,sys,json
import numpy as np
R=pathlib.Path(__file__).resolve().parents[2];rel=sys.argv[1];SRC=pathlib.Path('/private/tmp/gsfm011b-20261022/microsoft-source/model') if rel=='microsoft-v1.1' else R/'work/GSFM-006-source-517a075/model';sys.path.insert(0,str(SRC));from gridsfm.data import load_pyg_json,prepare_for_inference
O=R/'results/comparisons/GSFM-014/20261023-rated-variants';audit=[]
for name in ['R300-base','R600-base','U300-base','U600-base']:
 d=O/name;c=json.loads((d/'input.json').read_text());md=json.loads((d/(rel+'-metadata.json')).read_text())['mapping'];p=d/(rel+'-input.pyg.json');data=prepare_for_inference(load_pyg_json(p));maxerr=0
 for family,cols in [('ac_line',[6,7,8]),('transformer',[4,5,6])]:
  a=data['bus',family,'bus'].edge_attr[:,cols].numpy();expected=np.array([c['branch'][i][5:8] for i in md[family+'_source_rows']])/c['baseMVA'];err=abs(a-expected).max(initial=0);assert np.allclose(a,expected,atol=1e-6,rtol=1e-7);maxerr=max(maxerr,float(err))
 fixed=[i for i,g in enumerate(c['gen']) if g[8]==g[9]];native=json.loads((d/(rel+'-native.json')).read_text());assert max(abs(native['pg_mw'][i]-c['gen'][i][8]) for i in fixed)<1e-3;audit.append({'scenario':name,'fixed_Pg_rows':len(fixed),'fixed_Pg_limits_preserved_and_native_pass':True,'all_RATE_A_B_C_FP32_features_match_original_div_baseMVA':True,'max_FP32_roundoff_pu':maxerr})
(O/(rel+'-rating-feature-audit.json')).write_text(json.dumps({'status':'PASS','release':rel,'audits':audit,'source_path_notes':'data.py wires all raw edge features; pe_features.py promotes branch attributes to branch nodes; model.py input_proj encodes full node x. RATE_A also feeds global/stress features. No hard output thermal projection. Zero-rate stress denominator clamp is a feature computation, not authoritative thermal scoring.','new_model_forward_calls':0},indent=2)+'\n');print(rel,'rating features and fixed Pg PASS')
