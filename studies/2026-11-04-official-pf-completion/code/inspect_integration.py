from paths import *
import hashlib, json, numpy as np, torch
from torch_geometric.data import HeteroData
import closure
from gridsfm.data import load_pyg_json
from study import read, save, evaluate
from electrical import matrices, makeYbus
from matpower_case import read_case

torch.set_num_threads(4)
records = []
for net in ['case500goc', 'case300', 'case300x2']:
    d = PRIOR/'results'/f'{net}-base'
    c = read(d/'input.json')
    native = read(d/'newer-base-v2-native.json')
    ref = read(d/'ac-native.json')
    raw = load_pyg_json(d/'newer-base-v2-input.pyg.json')
    prepared = HeteroData.from_dict(torch.load(d/'newer-base-v2-prepared-used.pt', weights_only=True, map_location='cpu'))
    a = closure.extract_case(raw)
    p = closure.extract_case(prepared)
    ids,b,e,f,t = matrices(c)
    Y,_,_ = makeYbus(c['baseMVA'], b, e)
    V = np.asarray(ref['vm'])*np.exp(1j*np.deg2rad(ref['va_deg']))
    original_ref = int(a.ref[0])
    row = dict(network=net,baseMVA=c['baseMVA'], original_ref_bus=int(c['bus'][original_ref][0]),
               online_generators_at_original_ref=int(sum(a.gen2bus==original_ref)),
               first_online_generator_bus=int(c['bus'][a.gen2bus[0]][0]),
               multi_generator_buses={str(c['bus'][i][0]):int(sum(a.gen2bus==i)) for i in np.unique(a.gen2bus) if sum(a.gen2bus==i)>1},
               generators_at_PQ_buses=[int(c['bus'][i][0]) for i in a.pq if i in a.gen2bus],
               raw_Y_max_difference=float(abs((a.Ybus-Y).toarray()).max()),
               prepared_Y_max_difference=float(abs((p.Ybus-Y).toarray()).max()),
               raw_vs_original_injection_MVA=float(abs(c['baseMVA']*V*np.conj((a.Ybus-Y)@V)).max()),
               prepared_vs_original_injection_MVA=float(abs(c['baseMVA']*V*np.conj((p.Ybus-Y)@V)).max()),
               raw_load_P_max_MW=float(abs(a.Pd*c['baseMVA']-b[:,2]).max()),
               raw_load_Q_max_MVAr=float(abs(a.Qd*c['baseMVA']-b[:,3]).max()),
               raw_prepared_Y_equal=bool(np.array_equal(a.Ybus.toarray(),p.Ybus.toarray())),
               reference_evaluator_pass=evaluate(c,ref,'AC-OPF')[0]['AC_joint_pass'])
    if net=='case500goc':
        author = read_case(SOURCE/'generate_finetune_dataset/topologies/pglib_opf_case500_goc.m')
        row['author_topology_exact_matrix_match']={k:author[k]==c[k] for k in ['baseMVA','bus','gen','branch','gencost']}
    records.append(row)
save(ROOT/'validation/integration-inspection.json', {'records':records,'closure_sha256':hashlib.sha256((SOURCE/'finetune_model/src/closure.py').read_bytes()).hexdigest(),'status':'INSPECTION_ONLY_NO_PF_RUN'})
print(json.dumps(records,indent=2))
