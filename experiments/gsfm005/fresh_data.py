from data_helpers import *
def main():
    (RUN/'data').mkdir(parents=True,exist_ok=True)
    if (RUN/'data/manifest.json').exists():raise RuntimeError('Existing data must be reused, not regenerated')
    assert (RUN/'freeze.json').exists();base=read(BASE/'case300-input.json');reg=read(OLD/'data/regions.json');assert reg==regions(base);save(RUN/'data/regions.json',reg);generation_start=time.time()
    manifests={};seen={content_hash(base)}
    for previous in (REPO/'results').rglob('*input.json'):
        if RUN not in previous.parents:seen.add(content_hash(read(previous)))
    save(RUN/'evaluation-open.json',dict(freeze_sha256=sha(RUN/'freeze.json'),opened_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),previous_input_count=len(seen)))
    server=LabelServer()
    try:
        streams=[('ordinary',30,30503,.90,1.03,90),('higher_load',30,30505,1.035,1.06,90)]
        for split,n,seed,lo,hi,cap in streams:
            rng=np.random.Generator(np.random.PCG64(seed));recs=[];accepted=0
            for i in range(cap):
                if accepted>=n:break
                if time.time()-generation_start>=35*60:break
                globalfactor=float(rng.uniform(lo,hi));jit=rng.uniform(.98,1.02,len(base['bus']));factors=globalfactor*jit;c=copy.deepcopy(base)
                for b,original,f in zip(c['bus'],base['bus'],factors):b[2]=original[2]*f;b[3]=original[3]*f
                hc=content_hash(c)
                if hc in seen:
                    recs.append(dict(scenario_id=f'{split}-{i:03d}',accepted=False,status='DUPLICATE',input_content_hash=hc));continue
                seen.add(hc);sid=f'{split}-{i:03d}'
                rec=label(server,c,sid,split,{'seed':seed if seed else 3002026,'global_scale':globalfactor,'bus_jitter':jit.tolist(),'actual_combined_factors':factors.tolist(),'bus_order':[int(b[0]) for b in base['bus']]})
                recs.append(rec);accepted+=int(rec['accepted'])
                if (i+1)%10==0 or accepted==n:log('labels_progress',split=split,accepted=accepted,attempted=len(recs))
            manifests[split]=recs;save(RUN/'data/partial-manifest.json',manifests)

        recs=[];pairs=[r for r in manifests['ordinary'] if r['accepted']][:30]
        for j,original in enumerate(pairs):
            if time.time()-generation_start>=35*60:break
            c=read(Path(original['path'])/'input.json');eligible=[i for i,b in enumerate(c['bus']) if b[2]>0];region=set(reg['memberships'][j%4]);u=np.array([1. if int(c['bus'][i][0]) in region else -1. for i in eligible]);A=np.array([[c['bus'][i][k] for i in eligible] for k in [2,3]],dtype=float);norms=np.linalg.norm(A,axis=1);An=A[norms>0]/norms[norms>0,None];_,s,Vh=np.linalg.svd(An,full_matrices=False);tol=1e-12*s[0];Vr=Vh[s>tol];d=u-Vr.T@(Vr@u)
            if max(abs(d))<1e-10:recs.append({'scenario_id':f'spatial-{j:03d}','accepted':False,'status':'DEGENERATE','pair_id':original['scenario_id']});continue
            sign=1 if (j//4)%2==0 else -1;f=1+sign*.10*d/max(abs(d));before=np.array([[b[2],b[3]] for b in c['bus']]);total_before=before.sum(axis=0)
            for i,ff in zip(eligible,f):c['bus'][i][2]*=float(ff);c['bus'][i][3]*=float(ff)
            after=np.array([[b[2],b[3]] for b in c['bus']]);delta=after-before;res=after.sum(axis=0)-total_before;scale=np.maximum(1,np.abs(before).sum(axis=0));assert np.all(abs(res)<=1e-8*scale)
            extra={'pair_id':original['scenario_id'],'region_index':j%4,'rank':int(sum(s>tol)),'singular_values':s.tolist(),'svd_tolerance':float(tol),'P_Q_total_difference':res.tolist(),'demand_absolute_moved_MW_MVAr':(np.abs(delta).sum(axis=0)/2).tolist(),'region_net_change_MW_MVAr':delta[[int(b[0]) in region for b in c['bus']]].sum(axis=0).tolist()}
            combined=np.ones(300);combined[eligible]=f
            hc=content_hash(c)
            if hc in seen:
                recs.append(dict(scenario_id=f'spatial-{j:03d}',accepted=False,status='DUPLICATE',pair_id=original['scenario_id']));continue
            seen.add(hc)
            rec=label(server,c,f'spatial-{j:03d}','spatial',{'seed':30504,'seed_note':'deterministic SVD projection; no random draws required','region':j%4,'actual_factors':combined.tolist(),'eligible_indices':eligible},extra);recs.append(rec)
        manifests['spatial']=recs;save(RUN/'data/manifest.json',manifests)
        counts={k:{'accepted':sum(r['accepted'] for r in rs),'attempted':len(rs)} for k,rs in manifests.items()};save(RUN/'data/counts.json',counts);log('DATA_COMPLETE',counts=counts)
    finally:server.close()
if __name__=='__main__':main()
