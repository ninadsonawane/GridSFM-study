"""Original FP64 equations, distributions and native/DC scoring for12/14."""
import pathlib,sys,json,csv,hashlib,math
import numpy as np
import scipy.sparse as sp
from pypower.makeYbus import makeYbus
from pypower.makeBdc import makeBdc
R=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'scripts/python'))
from physics_metrics import branch_flows,evaluate,cost

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def serial(x):
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,np.generic):return x.item()
 if sp.issparse(x):return x.toarray().tolist()
 return str(x)
def save(p,x):pathlib.Path(p).write_text(json.dumps(x,indent=2,default=serial,allow_nan=False)+'\n')
def read(p):return json.loads(pathlib.Path(p).read_text())
def csvsave(p,rows):
 if not rows:return
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with pathlib.Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def stat(v):
 v=np.abs(np.asarray(v));return {'mean':float(v.mean()),'median':float(np.median(v)),'p95':float(np.percentile(v,95)),'max':float(v.max()),'count':len(v)}
def excess(x,lo,hi):return np.maximum(np.maximum(np.array(lo)-x,np.array(x)-hi),0)
def matrices(c):
 ids={int(b[0]):i for i,b in enumerate(c['bus'])};b=np.array(c['bus'],float);e=np.array(c['branch'],float);f=np.array([ids[int(z[0])] for z in e]);t=np.array([ids[int(z[1])] for z in e]);b[:,0]=np.arange(len(b));e[:,0]=f;e[:,1]=t;return ids,b,e,f,t

def dc_matrices(c):
 ids,b,e,f,t=matrices(c);B,F,pb,pf=makeBdc(c['baseMVA'],b,e);n=len(b);m=len(e);C=sp.csr_matrix((np.r_[np.ones(m),-np.ones(m)],(np.r_[np.arange(m),np.arange(m)],np.r_[f,t])),shape=(m,n));bb=e[:,10]/e[:,3]/np.where(e[:,8]!=0,e[:,8],1);want=sp.diags(bb)@C;shift=-bb*np.deg2rad(e[:,9]);err=max(abs((B-C.T@want).toarray()).max(),abs((F-want).toarray()).max(),abs(pb-C.T@shift).max(),abs(pf-shift).max());assert err<1e-10
 return B,F,pb,pf,float(err)
def terms(c,s):
 ids,b,e,f,t=matrices(c);Y,Yf,Yt=makeYbus(c['baseMVA'],b,e);V=np.array(s['vm'])*np.exp(1j*np.deg2rad(s['va_deg']));gen=np.zeros(len(b),complex)
 for j,g in enumerate(c['gen']):
  if g[7]>0:gen[ids[int(g[0])]]+=complex(s['pg_mw'][j],s['qg_mvar'][j])
 demand=b[:,2]+1j*b[:,3];shunt=(b[:,4]-1j*b[:,5])*abs(V)**2;sf,st=map(np.array,branch_flows(c,s['vm'],s['va_deg']));out=np.zeros(len(b),complex);np.add.at(out,f,sf);np.add.at(out,t,st);r=gen-demand-out-shunt;yr=gen-demand-c['baseMVA']*V*np.conj(Y@V);err=max(abs(r-yr).max(),abs(sf-c['baseMVA']*V[f]*np.conj(Yf@V)).max(),abs(st-c['baseMVA']*V[t]*np.conj(Yt@V)).max());assert err<1e-6,err
 return {'r':r,'gen':gen,'demand':demand,'shunt':shunt,'out':out,'sf':sf,'st':st,'V':V,'crosscheck_MW_MVAr':float(err)}
def identity(c,i):
 if 'diagnostic_bus_origins' in c:
  z=c['diagnostic_bus_origins'][i];return z['area'],z['original_id']
 bid=c.get('bus_ids',[int(b[0]) for b in c['bus']])[i]
 if isinstance(bid,str) and ':bus:' in bid:return bid[0],int(bid.split(':')[-1])
 return 'original',int(c['bus'][i][0])
def score(c,s,method,ref=None):
 ids,b,e,f,t=matrices(c);nb=len(b);base=c['baseMVA'];dc=method=='DC-OPF';pg=np.array(s['pg_mw']);online=np.array([g[7]>0 for g in c['gen']]);pv=np.where(online,excess(pg,[g[9] for g in c['gen']],[g[8] for g in c['gen']]),abs(pg));slack=next(i for i,bb in enumerate(b) if bb[1]==3);gids=np.array([ids[int(g[0])] for g in c['gen']]);gnet=np.zeros(nb);np.add.at(gnet,gids,np.where(online,pg,0));angle=np.array(s['va_deg']);diff=angle[f]-angle[t];av=[]
 for j,z in enumerate(e):
  lo,hi=z[11:13];active=((lo!=0 and lo>-360) or (hi!=0 and hi<360) or (lo!=0 and hi==0) or(lo==0 and hi!=0))
  av.append(max(0,lo-diff[j] if lo>=-360 else 0,diff[j]-hi if hi<=360 else 0) if active and z[10]>0 else 0)
 if dc:
  B,F,pb,pf,audit=dc_matrices(c);r=gnet-b[:,2]-b[:,4]-base*(B@np.deg2rad(angle)+pb);sf=np.array(s['pf_mw']).astype(complex);st=np.array(s['pt_mw']).astype(complex);assert max(abs(sf.real-base*(F@np.deg2rad(angle)+pf)))<1e-6;tr=None;qv=vv=None;ratevalue=np.maximum(abs(sf.real),abs(st.real))
 else:
  tr=terms(c,s);r=tr['r'];sf=tr['sf'];st=tr['st'];qv=np.where(online,excess(s['qg_mvar'],[g[4] for g in c['gen']],[g[3] for g in c['gen']]),abs(np.array(s['qg_mvar'])));vv=excess(s['vm'],b[:,12],b[:,11]);ratevalue=np.maximum(abs(sf),abs(st))
 rated=(e[:,5]>0)&(e[:,10]>0);texcess=np.maximum(ratevalue[rated]-e[rated,5],0);passphysical=bool(max(abs(r))<=1e-3) if dc else bool(max(abs(r.real).max(),abs(r.imag).max())<=1e-3)
 summary={'method':method,'P':stat(r.real),'Q':None if dc else stat(r.imag),'P_total_abs':float(abs(r.real).sum()),'Q_total_abs':None if dc else float(abs(r.imag).sum()),'P_violating_buses':int(sum(abs(r.real)>1e-3)),'Q_violating_buses':None if dc else int(sum(abs(r.imag)>1e-3)),'Pg_max_excess':float(max(pv)),'Pg_violating_count':int(sum(pv>1e-3)),'Qg_max_excess':None if dc else float(max(qv)),'Qg_violating_count':None if dc else int(sum(qv>1e-3)),'Vm_max_excess':None if dc else float(max(vv)),'Vm_violating_count':None if dc else int(sum(vv>1e-4)),'angle_max_excess_deg':float(max(av)),'angle_violating_count':int(sum(np.array(av)>1e-3)),'rated_online_branch_count':int(sum(rated)),'thermal_max_excess_MVA_or_DC_MW':float(max(texcess,default=0)) if any(rated) else None,'thermal_max_ratio':float(max(ratevalue[rated]/e[rated,5])) if any(rated) else None,'thermal_violating_count':int(sum(texcess>1e-3)) if any(rated) else None,'thermal_definition':'DC active-flow only; AC apparent thermal feasibility N/A' if dc else 'max both-end |P+jQ|; original RATE_A; zero unlimited','AC_joint_feasible':None if dc else bool(passphysical and max(pv)<=1e-3 and max(qv)<=1e-3 and max(vv)<=1e-4 and max(av)<=1e-3 and max(texcess,default=0)<=1e-3),'native_DC_constraints_pass':bool(passphysical and max(pv)<=1e-3 and max(av)<=1e-3 and max(texcess,default=0)<=1e-3) if dc else None,'physics_crosscheck':None if dc else tr['crosscheck_MW_MVAr'],'approximation':None}
 if ref is not None:
  rt=terms(c,ref);rp=np.array(ref['pg_mw']);rgnet=np.zeros(nb);np.add.at(rgnet,gids,np.where(online,rp,0));ang=(angle-angle[slack])-(np.array(ref['va_deg'])-ref['va_deg'][slack]);ang=(ang+180)%360-180;ap={'Pg_per_generator_MW':stat((pg-rp)[online]),'Pg_bus_aggregate_MW':stat(gnet[np.unique(gids[online])]-rgnet[np.unique(gids[online])]),'aligned_angle_deg':stat(ang),'branch_P_MW':stat(np.r_[sf.real-rt['sf'].real,st.real-rt['st'].real]),'Qg_per_generator_MVAr':None if dc else stat((np.array(s['qg_mvar'])-ref['qg_mvar'])[online]),'Qg_bus_aggregate_MVAr':None if dc else stat(tr['gen'].imag[np.unique(gids[online])]-rt['gen'].imag[np.unique(gids[online])]),'Vm_pu':None if dc else stat(np.array(s['vm'])-ref['vm']),'branch_Q_MVAr':None if dc else stat(np.r_[sf.imag-rt['sf'].imag,st.imag-rt['st'].imag])};summary['approximation']=ap
 busrows=[];branchrows=[];arearows=[]
 for i,z in enumerate(b):
  area,original=identity(c,i);row={'method':method,'bus_id':int(c['bus'][i][0]),'area':area,'original_bus_id':original,'bus_type':int(z[1]),'P_residual_MW':float(r[i].real),'Q_residual_MVAr':None if dc else float(r[i].imag),'Pg_bus_MW':float(gnet[i]),'Pd_MW':z[2],'Qg_bus_MVAr':None if dc else float(tr['gen'][i].imag),'Qd_MVAr':z[3],'branch_P_out_MW':None if dc else float(tr['out'][i].real),'branch_Q_out_MVAr':None if dc else float(tr['out'][i].imag),'bus_shunt_P_MW':None if dc else float(tr['shunt'][i].real),'bus_shunt_Q_MVAr':None if dc else float(tr['shunt'][i].imag),'Vm':None if dc else s['vm'][i],'angle_deg':s['va_deg'][i]};busrows.append(row)
 for j,z in enumerate(e):
  rr=z[5] if z[10]>0 and z[5]>0 else None;areaf,origf=identity(c,int(f[j]));areat,origt=identity(c,int(t[j]));value=float(ratevalue[j]);row={'method':method,'branch_row_1based':j+1,'from_bus':int(c['branch'][j][0]),'to_bus':int(c['branch'][j][1]),'from_area':areaf,'to_area':areat,'from_original_id':origf,'to_original_id':origt,'is_tie':areaf!=areat,'Pf_MW':float(sf[j].real),'Pt_MW':float(st[j].real),'Qf_MVAr':None if dc else float(sf[j].imag),'Qt_MVAr':None if dc else float(st[j].imag),'Sf_MVA':None if dc else float(abs(sf[j])),'St_MVA':None if dc else float(abs(st[j])),'rateA':rr,'controlling_end':'from' if abs(sf[j])>=abs(st[j]) else 'to','loading_ratio':None if rr is None else value/rr,'thermal_excess':None if rr is None else max(value-rr,0),'P_error_from':None if ref is None else float(sf[j].real-rt['sf'][j].real),'P_error_to':None if ref is None else float(st[j].real-rt['st'][j].real),'Q_error_from':None if ref is None or dc else float(sf[j].imag-rt['sf'][j].imag),'Q_error_to':None if ref is None or dc else float(st[j].imag-rt['st'][j].imag)};branchrows.append(row)
 for area in sorted({identity(c,i)[0] for i in range(nb)}):
  ii=np.array([i for i in range(nb) if identity(c,i)[0]==area]);internal=[j for j in range(len(e)) if f[j] in ii and t[j] in ii];interF=[j for j in range(len(e)) if f[j] in ii and t[j] not in ii];interT=[j for j in range(len(e)) if t[j] in ii and f[j] not in ii];tieout=sum(sf[interF])+sum(st[interT]);loss=sum((sf+st)[internal]);row={'method':method,'area':area,'P_residual_mean':float(abs(r[ii].real).mean()),'P_residual_p95':float(np.percentile(abs(r[ii].real),95)),'P_residual_max':float(abs(r[ii].real).max()),'Q_residual_mean':None if dc else float(abs(r[ii].imag).mean()),'Q_residual_p95':None if dc else float(np.percentile(abs(r[ii].imag),95)),'Q_residual_max':None if dc else float(abs(r[ii].imag).max()),'P_violating_buses':int(sum(abs(r[ii].real)>1e-3)),'Q_violating_buses':None if dc else int(sum(abs(r[ii].imag)>1e-3)),'generation_P_MW':float(gnet[ii].sum()),'demand_P_MW':float(b[ii,2].sum()),'generation_Q_MVAr':None if dc else float(tr['gen'][ii].imag.sum()),'demand_Q_MVAr':float(b[ii,3].sum()),'internal_branch_losses_P_MW':float(loss.real),'internal_branch_net_Q_MVAr':None if dc else float(loss.imag),'outward_tie_P_MW':float(tieout.real),'outward_tie_Q_MVAr':None if dc else float(tieout.imag),'bus_shunt_P_MW':float(b[ii,4].sum()) if dc else float(tr['shunt'][ii].real.sum()),'bus_shunt_Q_MVAr':None if dc else float(tr['shunt'][ii].imag.sum()),'signed_P_residual_sum':float(r[ii].real.sum()),'signed_Q_residual_sum':None if dc else float(r[ii].imag.sum())}
  assert abs(row['generation_P_MW']-row['demand_P_MW']-row['internal_branch_losses_P_MW']-row['outward_tie_P_MW']-row['bus_shunt_P_MW']-row['signed_P_residual_sum'])<1e-6
  if not dc:assert abs(row['generation_Q_MVAr']-row['demand_Q_MVAr']-row['internal_branch_net_Q_MVAr']-row['outward_tie_Q_MVAr']-row['bus_shunt_Q_MVAr']-row['signed_Q_residual_sum'])<1e-6
  if ref is not None:
   row['Pg_bus_MAE']=float(abs(gnet[ii]-rgnet[ii]).mean());row['angle_MAE_deg']=float(abs(ang[ii]).mean());row['Vm_MAE_pu']=None if dc else float(abs(np.array(s['vm'])[ii]-np.array(ref['vm'])[ii]).mean())
  arearows.append(row)
 #Signed area-interchange sum equals both-end tie losses including charging Q.
 tieidx=[j for j in range(len(e)) if identity(c,int(f[j]))[0]!=identity(c,int(t[j]))[0]]
 assert abs(sum(x['outward_tie_P_MW'] for x in arearows)-sum((sf+st)[tieidx]).real)<1e-6
 return summary,busrows,branchrows,arearows
