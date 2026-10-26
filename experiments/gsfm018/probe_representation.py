"""No checkpoint/model-forward/OPF/PF probe of exact pinned feature functions.

Uses a minimal tensor holder because PyG is unavailable. Extracted function ASTs
are executed unchanged; no emulation of the neural model is claimed.
"""
from pathlib import Path
import argparse, ast, copy, hashlib, json, platform, sys
from types import SimpleNamespace
import numpy as np
import scipy
import scipy.sparse as sp
from scipy.sparse.linalg import factorized
from scipy.sparse.csgraph import minimum_spanning_tree
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'scripts/python'))
from matpower_case import read_case
from gridsfm_convert import convert, canonical_hash
torch.set_num_threads(1)
PINS={
    'v1.1':{'commit':'1ca775fd436d7ce013a1c0ab946e61ac7ef59ad6',
        'cycle_basis.py':'4f1a324975f27bc2341387994c7c8cfbd2f4901a2769717bff5ed20dfa0d0eeb',
        'pe_features.py':'51643d05e6b0d3b649043fac4c4801749abd2f70aa471416e9ee5a029de7b808',
        'schema.py':'9de2b4501f502650f19a394e560338c0aa7c09f5eb4adf82e3aee8230c18f8f3'},
    'v2':{'commit':'517a07531ea55a11bd81a89a6c6879695a2ba4b4',
        'cycle_basis.py':'4f1a324975f27bc2341387994c7c8cfbd2f4901a2769717bff5ed20dfa0d0eeb',
        'pe_features.py':'c097f8b2ab92ccfb9fa58c7af1a82c76e665389c70002a7632c4794f6a9de8af',
        'schema.py':'939b87fe8ecbbe5dc210b406a2429bbcdf1281edac731ca9861d8379bbacd459'}}

class Data(dict):
    def __missing__(self,key):
        self[key]=SimpleNamespace()
        return self[key]
    @property
    def edge_types(self): return [k for k in self if isinstance(k, tuple)]
    @property
    def node_types(self): return [k for k in self if isinstance(k, str)]

def tensor_data(obj):
    d=Data()
    for kind, rows in obj['grid']['nodes'].items():
        d[kind]=SimpleNamespace(x=torch.tensor(rows,dtype=torch.float32))
    for kind, e in obj['grid']['edges'].items():
        key=('bus',kind,'bus') if kind in ['ac_line','transformer'] else (kind[:-5],kind,'bus')
        v=SimpleNamespace(edge_index=torch.tensor([e['senders'],e['receivers']],dtype=torch.long))
        if 'features' in e:v.edge_attr=torch.tensor(e['features'],dtype=torch.float32)
        d[key]=v
    return d

def extract(folder):
    ns={'np':np,'sp':sp,'factorized':factorized,'torch':torch,
        '_csr_matrix':sp.csr_matrix,'_scipy_mst':minimum_spanning_tree}
    exec(compile((folder/'schema.py').read_text(),str(folder/'schema.py'),'exec'),ns)
    for dest,src in [('_AC_LINE_KEY','AC_LINE_KEY'),('_TRANSFORMER_KEY','TRANSFORMER_KEY'),
       ('_AC_LINE_R_IDX','AC_LINE_R_IDX'),('_AC_LINE_X_IDX','AC_LINE_X_IDX'),('_AC_LINE_RATE_A_IDX','AC_LINE_RATE_A_IDX'),
       ('_TRANSFORMER_R_IDX','TR_R_IDX'),('_TRANSFORMER_X_IDX','TR_X_IDX'),('_TRANSFORMER_RATE_A_IDX','TR_RATE_A_IDX')]:ns[dest]=ns[src]
    names={'_fundamental_cycles_fast','compute_cycle_basis','_build_topology_state','_empty_state','compute_er_landmark_moments','compute_dc_features','attach_branches_as_nodes_','_promote_to_branch_nodes'}
    for name in ['cycle_basis.py','pe_features.py']:
        tree=ast.parse((folder/name).read_text())
        body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]
        body.extend(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names)
        exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(folder/name),'exec'),ns)
    return ns

def physical_cycles(ns,d,obj,branch_map):
    raw=ns['_fundamental_cycles_fast'](d); result={}; invalid=0; wrong_signs=0; proper_invalid=0
    for cyc in raw:
        signed=[]; divergence=np.zeros(d['bus'].x.shape[0],dtype=int); proper_divergence=divergence.copy()
        for a,b,(kind,row) in cyc:
            orig=branch_map[obj['metadata'][kind+'_source_rows'][row]]
            key=('bus',kind,'bus');u,v=d[key].edge_index[:,row].tolist()
            shipped_sign=1 if a<b else -1
            correct_sign=1 if (a,b)==(u,v) else -1
            wrong_signs+=int(shipped_sign!=correct_sign)
            divergence[u]+=shipped_sign;divergence[v]-=shipped_sign
            proper_divergence[u]+=correct_sign;proper_divergence[v]-=correct_sign
            signed.append((orig,shipped_sign))
        invalid+=int(np.any(divergence))
        proper_invalid+=int(np.any(proper_divergence))
        signature=tuple(sorted(orig for orig,_ in signed))
        assert signature not in result
        result[signature]=dict(signed)
    return result,{'count':len(raw),'incidences':sum(len(c) for c in raw),
                   'nonzero_B1_times_B2_columns':invalid,'signs_disagreeing_with_stored_branch_orientation':wrong_signs,
                   'proper_orientation_nonzero_boundary_columns_diagnostic':proper_invalid,
                   'cycle_lengths':sorted(len(c) for c in raw)}

def raw_equivalence(obj,base,c,original,maps):
    a=obj['grid'];b=base['grid'];assert a['context']==b['context']
    for i,j in enumerate(maps['bus']):assert a['nodes']['bus'][i]==b['nodes']['bus'][j]
    for kind in ['generator','load','shunt']:
        ea=a['edges'][kind+'_link'];eb=b['edges'][kind+'_link']
        aa=sorted((maps['bus'][v],tuple(a['nodes'][kind][u])) for u,v in zip(ea['senders'],ea['receivers']))
        bb=sorted((v,tuple(b['nodes'][kind][u])) for u,v in zip(eb['senders'],eb['receivers']))
        assert aa==bb,kind
    for kind in ['ac_line','transformer']:
        ea=a['edges'][kind];eb=b['edges'][kind]
        look={v:i for i,v in enumerate(base['metadata'][kind+'_source_rows'])}
        for i,src in enumerate(obj['metadata'][kind+'_source_rows']):
            j=look[maps['branch'][src]]
            assert ea['features'][i]==eb['features'][j]
            assert [maps['bus'][ea['senders'][i]],maps['bus'][ea['receivers'][i]]]==[eb['senders'][j],eb['receivers'][j]]

def cycle_gram(cycles):
    b2=np.zeros((411,len(cycles)),dtype=np.int64)
    for j,c in enumerate(cycles.values()):
        for i,sign in c.items():b2[i,j]=sign
    return b2@b2.T

def exact_boundary_product(ns,d,obj):
    # Both B1 signs and B2 signs come from executed pinned functions, not a
    # hand-selected graph-orientation convention. Global sign flips are harmless
    # to the zero-product identity, but mismatched edge conventions are not.
    ns['attach_branches_as_nodes_'](d)
    cb=ns['compute_cycle_basis'](d)
    b1=np.zeros((300,411),dtype=np.int64); b2=np.zeros((411,cb['n_cycles']),dtype=np.int64)
    for family,node,prefix in [('ac_line','branch_ac','ac'),('transformer','branch_tr','tr')]:
        rows=obj['metadata'][family+'_source_rows']
        endpoint=d[(node,'endpoint_of','bus')]
        for (br,bus),sg in zip(endpoint.edge_index.T.tolist(),endpoint.edge_attr[:,0].tolist()):b1[bus,rows[br]]=int(sg)
        for (cyc,br),sg in zip(cb[prefix+'_ce_index'].T.tolist(),cb[prefix+'_ce_signs'].tolist()):b2[rows[br],cyc]=int(sg)
    prod=b1@b2
    return {'nonzero_columns':int(np.any(prod!=0,axis=0).sum()),'max_abs_entry':int(np.max(np.abs(prod))),
            'convention':'B1 from pinned _promote_to_branch_nodes endpoint edge_attr; B2 from pinned compute_cycle_basis ce_signs; exact integer matrix multiplication.'}

def diff(a,b):
    delta=np.abs(np.asarray(a,dtype=np.float64)-np.asarray(b,dtype=np.float64))
    return {'max_abs':float(delta.max(initial=0)),'mean_abs':float(delta.mean()),
            'rows_with_any_exact_difference':int(np.any(delta>0,axis=1).sum()),
            'rows_with_any_difference_above_1e-6':int(np.any(delta>1e-6,axis=1).sum())}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,required=True,help='Pinned original MATPOWER8.1 case300.m')
    parser.add_argument('--v11-source',type=Path,required=True,help='Directory of pinned Microsoft gridsfm source files')
    parser.add_argument('--v2-source',type=Path,required=True,help='Directory of pinned newer gridsfm source files')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Refusing to overwrite an existing result; choose a new output path.')
    case_path=args.case; case=read_case(case_path)
    assert hashlib.sha256(case_path.read_bytes()).hexdigest()=='69a90280e999ef533d94656e0fbc08311f1347c962dd2753ff2005ff5e3f9ac5'
    assert [len(case[k]) for k in ['bus','gen','branch']]==[300,69,411]
    output={'scope':'Exact pinned source feature functions only; no model forwards or checkpoints; feature linear systems only, no conventional PF/OPF.',
            'case_sha256':hashlib.sha256(case_path.read_bytes()).hexdigest(),
            'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'study_scripts_sha256':{n:hashlib.sha256((ROOT/'scripts/python'/n).read_bytes()).hexdigest() for n in ['matpower_case.py','gridsfm_convert.py']},
            'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'torch':torch.__version__},'releases':{}}
    variants={}
    for label,fields in [('baseline',[]),('bus_only',['bus']),('gen_only',['gen','gencost']),('branch_only',['branch']),('all_rows',['bus','gen','gencost','branch'])]:
        c=copy.deepcopy(case)
        for f in fields:c[f].reverse()
        variants[label]=(c,{'bus':list(reversed(range(300))) if 'bus' in fields else list(range(300)),
                           'branch':list(reversed(range(411))) if 'branch' in fields else list(range(411))})
    for release,folder in [('v1.1',args.v11_source),('v2',args.v2_source)]:
        for file,expected in PINS[release].items():
            if file!='commit':assert hashlib.sha256((folder/file).read_bytes()).hexdigest()==expected,(release,file,'source hash mismatch')
        ns=extract(folder); records={}; baseline=None
        for label,(c,maps) in variants.items():
            obj=convert(c)
            if release=='v2':
                for rows in obj['grid']['nodes'].values():
                    for row in rows:row.append(1.)
                for f in ['ac_line','transformer']:
                    for row in obj['grid']['edges'][f]['features']:row.append(1.)
            d=tensor_data(obj);cycles,summary=physical_cycles(ns,d,obj,maps['branch'])
            row={'input_canonical_sha256':canonical_hash(c),'cycle_summary':summary}
            row['exact_upstream_boundary_product']=exact_boundary_product(ns,d,obj)
            assert row['exact_upstream_boundary_product']['nonzero_columns']==summary['nonzero_B1_times_B2_columns']
            if release=='v1.1':
                state=ns['_build_topology_state'](d,64)
                moments=ns['compute_er_landmark_moments'](state)
                busdc,branchdc=ns['compute_dc_features'](d,state)
                physical_landmarks=[int(c['bus'][i][0]) for i in state['landmarks']]
                row['landmark_bus_ids']=physical_landmarks
                row['edge_offsets']={k:list(v) for k,v in state['edge_offsets'].items()}
                row['actual_ac_count']=len(obj['grid']['edges']['ac_line']['senders'])
                row['actual_transformer_count']=len(obj['grid']['edges']['transformer']['senders'])
            if baseline is None:
                baseline={'cycles':cycles,'obj':obj}
                if release=='v1.1':baseline.update(moments=moments,busdc=busdc,branchdc=branchdc,landmarks=physical_landmarks)
            else:
                raw_equivalence(obj,baseline['obj'],c,case,maps)
                row['raw_features_and_endpoints_exact_after_mapping']=True
                shared=set(cycles)&set(baseline['cycles'])
                identical_signs=sum(cycles[k]==baseline['cycles'][k] for k in shared)
                global_flips=sum(all(cycles[k][e]==-baseline['cycles'][k][e] for e in k) for k in shared)
                row['cycle_comparison']={'shared_physical_cycle_supports':len(shared),'total_each':len(cycles),
                    'same_signs_on_shared_cycles':identical_signs,'globally_flipped_shared_cycles':global_flips}
                delta=cycle_gram(cycles)-cycle_gram(baseline['cycles'])
                row['cycle_B2B2T_difference']={'nonzero_entries':int(np.count_nonzero(delta)),
                    'max_abs_entry':int(np.max(np.abs(delta))),'note':'Exact integer operator diagnostic; not model inference.'}
                if release=='v1.1':
                    order=np.argsort(maps['bus'])
                    row['landmarks_shared']=len(set(physical_landmarks)&set(baseline['landmarks']))
                    row['er_moments']=diff(moments[order],baseline['moments'])
                    row['bus_dc_features']=diff(busdc[order],baseline['busdc'])
                    row['branch_dc_features']={}
                    for f in ['ac_line','transformer']:
                        lookup={v:i for i,v in enumerate(baseline['obj']['metadata'][f+'_source_rows'])}
                        alignment=[lookup[maps['branch'][v]] for v in obj['metadata'][f+'_source_rows']]
                        row['branch_dc_features'][f]=diff(branchdc[f][np.argsort(alignment)],baseline['branchdc'][f])
                    # Isolated diagnostic: same physical landmarks, no model prediction.
                    fixed=state.copy();idx={int(b[0]):i for i,b in enumerate(c['bus'])}
                    fixed['landmarks']=np.array([idx[v] for v in baseline['landmarks']])
                    row['fixed_physical_landmarks_er_diagnostic']=diff(ns['compute_er_landmark_moments'](fixed)[order],baseline['moments'])
                    # Isolated offset diagnostic: compare correct own-branch PE after mapping.
                    fixed=state.copy();fixed['edge_offsets']=dict(state['edge_offsets']);fixed['edge_offsets']['transformer']=(row['actual_ac_count'],row['actual_transformer_count'])
                    _,proper=ns['compute_dc_features'](d,fixed)
                    if 'proper_branchdc' not in baseline:
                        db=tensor_data(baseline['obj']);bs=ns['_build_topology_state'](db,64);bs['edge_offsets']['transformer']=(row['actual_ac_count'],row['actual_transformer_count'])
                        baseline['proper_branchdc']=ns['compute_dc_features'](db,bs)[1]
                    alignment=[baseline['obj']['metadata']['transformer_source_rows'].index(maps['branch'][v]) for v in obj['metadata']['transformer_source_rows']]
                    row['correct_offset_transformer_pe_diagnostic']=diff(proper['transformer'][np.argsort(alignment)],baseline['proper_branchdc']['transformer'])
            # Identical source-function rerun checks order effects versus variation.
            repeat=ns['compute_cycle_basis'](d);repeat2=ns['compute_cycle_basis'](d)
            row['cycle_repeat_exact']=all(torch.equal(repeat[k],repeat2[k]) if torch.is_tensor(repeat[k]) else repeat[k]==repeat2[k] for k in repeat)
            if release=='v1.1':
                again=ns['_build_topology_state'](d,64)
                row['er_repeat_exact']=bool(np.array_equal(moments,ns['compute_er_landmark_moments'](again)))
            records[label]=row
        output['releases'][release]={'source_commit':PINS[release]['commit'],'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.glob('*.py'))},'variants':records}
    path=args.output;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(output,indent=2)+'\n')
    print(path)
    for release,item in output['releases'].items():
        for name,row in item['variants'].items():
            print(release,name,'cycles',row.get('cycle_comparison',row['cycle_summary']['count']),
                  'landmarks',row.get('landmarks_shared'),'ER',row.get('er_moments'),
                  'transformer PE',row.get('branch_dc_features',{}).get('transformer'),
                  'invalid B1B2',row['cycle_summary']['nonzero_B1_times_B2_columns'])
if __name__=='__main__':main()
