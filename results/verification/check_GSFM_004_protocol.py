"""Validate protocol links and proposed perturbation arithmetic; no OPF/training."""
from pathlib import Path
import collections
import hashlib
import json
import re
import sys
import numpy as np

repo = Path(__file__).resolve().parents[2]
# Repository-relative validation; source case must already be acquired.
sys.path.insert(0, str(repo / 'scripts' / 'python'))
from matpower_case import read_case

docs = [repo/'README.md', repo/'HANDOFF.md',
        repo/'docs/experiments/GSFM-003.md', repo/'docs/experiments/GSFM-004.md',
        repo/'docs/decisions/0003-bounded-discovery-pilot.md',
        repo/'docs/research/2026-10-21-publication-plan.md']
missing = []
for file in docs:
    for target in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):
            continue
        if not (file.parent / target.split('#')[0]).exists():
            missing.append((str(file), target))
assert not missing, missing

source = repo/'data/source/matpower-8.1/case300.m'
case = read_case(source)
bus = np.array(case['bus'])
ids = bus[:,0].astype(int)
eligible = np.flatnonzero(bus[:,2] > 0)
eligible_ids = ids[eligible]
adj = {int(i):set() for i in ids}
for branch in case['branch']:
    if branch[10] > 0:
        a,b = map(int,branch[:2]); adj[a].add(b); adj[b].add(a)
def distances(center):
    dist = {center:0}; q = collections.deque([center])
    while q:
        a = q.popleft()
        for b in adj[a]:
            if b not in dist:
                dist[b] = dist[a]+1; q.append(b)
    return dist
centers = [int(min(eligible_ids))]
distances_by_center = [distances(centers[0])]
while len(centers) < 4:
    center = min((int(i) for i in eligible_ids if i not in centers),
                 key=lambda i:(-min(d[i] for d in distances_by_center),i))
    centers.append(center); distances_by_center.append(distances(center))
k = int(np.ceil(len(eligible)/4))
regions = [set(sorted(map(int,eligible_ids), key=lambda i:(dist[i],i))[:k])
           for dist in distances_by_center]
rng = np.random.Generator(np.random.PCG64(30403))
errors = []; movements = []; ranks = []; bounds = []
for j in range(20):
    factors = rng.uniform(.90,1.03)*rng.uniform(.98,1.02,len(bus))
    base = bus[:,2:4]*factors[:,None]
    pq = base[eligible].T
    norms = np.linalg.norm(pq,axis=1)
    a = pq[norms>0]/norms[norms>0,None]
    _,s,vh = np.linalg.svd(a, full_matrices=False)
    vr = vh[s>1e-12*s.max()]
    region = regions[j%4]
    u = np.array([1. if int(i) in region else -1. for i in eligible_ids])
    d = u-vr.T@(vr@u)
    assert np.max(np.abs(d)) >= 1e-10
    sign = 1 if (j//4)%2 == 0 else -1
    f = 1+sign*.10*d/np.max(np.abs(d))
    shifted = base.copy(); shifted[eligible] *= f[:,None]
    err = np.abs(shifted.sum(0)-base.sum(0))
    assert np.all(err <= 1e-8*np.maximum(1,np.abs(base).sum(0)))
    assert np.all(f >= .9-1e-12) and np.all(f <= 1.1+1e-12)
    assert np.allclose(shifted[eligible,0]*base[eligible,1], shifted[eligible,1]*base[eligible,0])
    errors.append(err.tolist()); ranks.append(len(vr)); bounds.append([f.min(),f.max()])
    movements.append(float(np.abs(shifted[:,0]-base[:,0]).sum()/2))
record = {
    'scope':'Local document-link and arithmetic checks only; no AC-OPF solve, checkpoint inference or training',
    'documents_checked':len(docs), 'missing_links':missing,
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'spatial_candidates_checked':20, 'positive_Pd_bus_count':len(eligible),
    'centers':centers, 'region_sizes':[len(r) for r in regions],
    'row_space_ranks':sorted(set(ranks)),
    'max_total_PQ_roundoff':np.max(errors,axis=0).tolist(),
    'factor_min_max':[float(np.min(bounds)),float(np.max(bounds))],
    'redistributed_MW_min_max':[min(movements),max(movements)],
    'limitations':'These candidates are unfiltered mathematical perturbations, not accepted/feasible labels. Hardware worker must implement and validate its actual generator and solver.'
}
out = repo/'results/verification/2026-10-21-GSFM-004-protocol.json'
out.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,indent=2))
