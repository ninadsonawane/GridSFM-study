"""Standard scientific figures from saved tables, never solves or infers."""
import pathlib,sys,os,json,csv
os.environ['MPLCONFIGDIR']='/private/tmp/gsfm012-014-20261023/mplconfig';sys.path.insert(0,'/private/tmp/gsfm007-20261021T195824Z/plotdeps')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=pathlib.Path(__file__).resolve().parents[2];stage=int(sys.argv[1]);read=lambda p:json.loads(p.read_text());csvread=lambda p:list(csv.DictReader(p.open()));plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150});rels=['newer-base-v2','microsoft-v1.1'];colors={'newer-base-v2':'#67449a','microsoft-v1.1':'#bd512c'}
def end(fig,O,note,name):
 fig.text(.5,.008,note,ha='center',fontsize=8);fig.tight_layout(rect=(0,.055,1,.94));fig.savefig(O/(name+'.png'));fig.savefig(O/(name+'.pdf'));plt.close(fig)
if stage==12:
 O=R/'results/comparisons/GSFM-012/20261023-frozen-two-copy';rows=read(O/'method-summary.json');bus=csvread(O/'bus-metrics.csv');area=csvread(O/'area-exchange.csv');fig,ax=plt.subplots(1,3,figsize=(11,3.8));scenarios=['S0','Splus','Sminus']
 for panel,(key,unit) in enumerate([('P','Maximum P imbalance (MW)'),('Q','Maximum Q imbalance (MVAr)'),('thermal','Maximum tie excess (MVA)')]):
  for j,rel in enumerate(rels):
   v=[next(r for r in rows if r['scenario']==s and r['method']==rel) for s in scenarios];y=[r[key]['max'] if key!='thermal' else r['thermal_max_excess_MVA_or_DC_MW'] for r in v];ax[panel].bar(np.arange(3)+(j-.5)*.32,y,width=.3,label=rel,color=colors[rel])
  ax[panel].set_xticks(range(3),scenarios);ax[panel].set_ylabel(unit);ax[panel].grid(axis='y',alpha=.2)
 ax[0].legend(fontsize=7);fig.suptitle('Experiment12: native frozen states — balance failures persist; Splus overloads both ties');end(fig,O,'All3 AC references feasible. DC passes its own constraints; DC AC-Q/thermal feasibility is N/A. Only2 ties have finite ratings.','01-constraints')
 fig,ax=plt.subplots(2,2,figsize=(9,6))
 for j,rel in enumerate(rels):
  a=sorted([r for r in bus if r['scenario']=='S0' and r['method']==rel and r['area']=='A'],key=lambda r:int(r['original_bus_id']));b=sorted([r for r in bus if r['scenario']=='S0' and r['method']==rel and r['area']=='B'],key=lambda r:int(r['original_bus_id']))
  for i,co in enumerate(['P','Q']):
   key=co+'_residual_'+('MW' if co=='P' else 'MVAr');xx=np.array([float(r[key]) for r in a]);yy=np.array([float(r[key]) for r in b]);ax[i,j].scatter(xx,yy,s=9,c=colors[rel],alpha=.55);lo=min(xx.min(),yy.min());hi=max(xx.max(),yy.max());ax[i,j].plot([lo,hi],[lo,hi],':',c='#555');ax[i,j].set(title=rel+' — '+co,xlabel='Area A signed residual',ylabel='Area B signed residual');ax[i,j].grid(alpha=.15)
   for k,r in enumerate(a):
    if int(r['original_bus_id']) in [238,231,137]:ax[i,j].annotate(r['original_bus_id'],(xx[k],yy[k]),fontsize=7)
 fig.suptitle('Experiment12 S0: homologous A/B buses (P MW, Q MVAr)');end(fig,O,'One reference angle; source REF/PV distinction retained. Unequal outputs alone do not establish their cause.','02-AB-buses')
 fig,ax=plt.subplots(2,4,figsize=(12,6));methods=['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2']
 for j,m in enumerate(methods):
  for i,co in enumerate(['P','Q']):
   for a,color in [('A','#227a91'),('B','#ce7439')]:
    vals=[next(r for r in area if r['scenario']==s and r['method']==m and r['area']==a)['outward_tie_'+co+'_'+('MW' if co=='P' else 'MVAr')] for s in scenarios];ax[i,j].plot(scenarios,[float(v) if v else np.nan for v in vals],'o-',c=color,label='Area'+a)
   ax[i,j].axhline(0,c='#888',lw=.6);ax[i,j].set(title=m+' '+co,ylabel='Outward '+co+' ('+('MW' if co=='P' else 'MVAr')+')');ax[i,j].grid(alpha=.2)
   if m=='DC-OPF' and co=='Q':ax[i,j].text(.5,.5,'N/A: no DC Q prediction',transform=ax[i,j].transAxes,ha='center',fontsize=7)
 ax[0,0].legend(fontsize=7);fig.suptitle('Experiment12: signed inter-area power, summed over two physical ties');end(fig,O,'Area outward active powers sum to tie losses, not zero. Charging is included; all ties and parameters unchanged.','03-exchange')
if stage==13:
 O=R/'results/diagnosis/GSFM-013/20261023-accuracy-sensitivity';allrows=csvread(O/'bus-decomposition.csv');rows=[r for r in allrows if r['scenario'] in ['base','S0']];cols=[(n,r) for n in ['original300','constructed600'] for r in rels]
 for kind,name in [('accuracy','01-state-error'),('sensitivity','02-sensitivity'),('cancellation','03-gross-net')]:
  fig,ax=plt.subplots(2,4,figsize=(12,6));sc=None
  for j,(net,rel) in enumerate(cols):
   rr=[r for r in rows if r['network']==net and r['release']==rel]
   for i,co in enumerate(['P','Q']):
    z=ax[i,j]
    if kind=='accuracy':x=[float(r['incident_angle_difference_error_max_deg'])*np.pi/180 if co=='P' else float(r['onehop_Vm_error_mean_pu']) for r in rr];y=[abs(float(r[co+'_native_residual'])) for r in rr];xl='Incident angle error max (rad)' if co=='P' else 'Neighbor Vm error MAE (pu)';yl='|r'+co+'| ('+('MW' if co=='P' else 'MVAr')+')'
    elif kind=='sensitivity':x=[float(r[co+('_H_theta_0_001rad' if co=='P' else '_H_V_0_001pu')]) for r in rr];y=[abs(float(r[co+'_network_injection_error'])) for r in rr];xl='Hθ for0.001rad' if co=='P' else 'HV for0.001pu';yl='|Network '+co+' error|'
    else:x=[float(r[co+'_gross_individual_error']) for r in rr];y=[float(r[co+'_net_error']) for r in rr];xl='Gross individual error';yl='Net residual error'
    xx=np.maximum(x,1e-9);yy=np.maximum(y,1e-9)
    if kind=='cancellation':sc=z.scatter(xx,yy,c=[float(r[co+'_cancellation']) if r[co+'_cancellation'] else np.nan for r in rr],cmap='viridis',vmin=0,vmax=1,s=8);lim=[min(min(xx),min(yy)),max(max(xx),max(yy))];z.plot(lim,lim,':',c='#777',lw=.6)
    else:z.scatter(xx,yy,s=8,c=colors[rel],alpha=.5)
    z.set(xscale='log',yscale='log',xlabel=xl,ylabel=yl,title=('Original300' if net=='original300' else 'Copy600')+' / '+('v2' if rel=='newer-base-v2' else 'MS1.1')+' / '+co);z.grid(alpha=.15)
  if kind=='cancellation':fig.subplots_adjust(left=.065,right=.88,wspace=.60,hspace=.60,top=.87,bottom=.15);cax=fig.add_axes([.92,.25,.012,.5]);fig.colorbar(sc,cax=cax,label='Cancellation fraction (individual terms)');fig.text(.5,.02,'MW for P; MVAr for Q. C is N/A when gross<=0.001. Buses/areas are dependent development observations.',ha='center',fontsize=8);fig.suptitle('Experiment13: gross versus net error; small nets can conceal cancellation');fig.savefig(O/(name+'.png'));fig.savefig(O/(name+'.pdf'));plt.close(fig)
  else:fig.suptitle('Experiment13: '+('state/neighborhood error and native imbalance' if kind=='accuracy' else 'standardized electrical sensitivity and actual injection error'));end(fig,O,'Base/S0 saved states only. MW for P and MVAr for Q. Scatter associations are descriptive, not causal or probability estimates.',name)
 pairs=csvread(O/'matched-examples.csv');fig,ax=plt.subplots(2,2,figsize=(10,6))
 for z,(net,rel) in zip(ax.ravel(),cols):
  pair=next((p for p in pairs if p['network']==net and p['release']==rel and p['component']=='Q'),None)
  if pair is None:z.text(.5,.5,'No illustrative Q pair selected\nComplete admissible table retained',transform=z.transAxes,ha='center');continue
  rr=[next(r for r in rows if r['network']==net and r['release']==rel and r['bus_id']==pair[k]) for k in ['high_bus','low_bus']];pos=np.zeros(2);neg=np.zeros(2)
  for key,col,label in [('Q_generation_contribution','#76469c','Generation'),('Q_positive_branch_contributions','#197d91','Positive branch terms'),('Q_negative_branch_contributions','#d18444','Negative branch terms'),('Q_shunt_contribution','#999999','Bus shunt')]:
   vv=np.array([float(r[key]) for r in rr]);z.bar(range(2),vv,bottom=np.where(vv>=0,pos,neg),color=col,label=label);pos+=np.maximum(vv,0);neg+=np.minimum(vv,0)
  z.scatter(range(2),[float(r['Q_residual_error']) for r in rr],marker='D',c='black',s=18,label='Net');z.set_xticks(range(2),['High '+pair['high_bus'],'Low '+pair['low_bus']]);z.set_yscale('symlog',linthresh=1);z.set(title=net+' / '+rel+' / Q',ylabel='Signed MVAr error');z.grid(axis='y',alpha=.15)
 h,l=ax[0,0].get_legend_handles_labels();fig.legend(h,l,loc='lower center',bbox_to_anchor=(.5,.035),ncol=5,fontsize=7);fig.suptitle('Experiment13: first admissible matched Q pair per network/release');end(fig,O,'Selection frozen by source-feature distance then original IDs; full24 examples and all admissible pairs retained.','04-matched-budgets')
print('FIGURES COMPLETE',stage)
if stage==14:
 O=R/'results/comparisons/GSFM-014/20261023-rated-variants';rr=read(O/'method-summary.json');names=[x['id'] for x in read(O/'scenario-manifest.json')['scenarios']];methods=['AC-OPF','DC-OPF','microsoft-v1.1','newer-base-v2'];fig,ax=plt.subplots(1,2,figsize=(12,4.5));joint=np.full((4,8),np.nan);thermal=np.full((4,8),np.nan)
 for i,m in enumerate(methods):
  for j,n in enumerate(names):
   r=next(x for x in rr if x['method']==m and x['scenario']==n)
   if m!='DC-OPF' and (m!='AC-OPF' or r['reference_valid']):joint[i,j]=int(r['AC_joint_feasible'])
   if r['thermal_violating_count'] is not None:thermal[i,j]=r['thermal_violating_count']
 cmap=matplotlib.colors.ListedColormap(['#d78476','#83b89b']);cmap.set_bad('#dddddd');ax[0].imshow(joint,cmap=cmap,vmin=0,vmax=1,aspect='auto');im=ax[1].imshow(thermal,cmap='YlOrRd',aspect='auto');fig.colorbar(im,ax=ax[1],shrink=.65,label='Violating rated branches')
 for a in ax:
  a.set_xticks(range(8),names,rotation=55,ha='right');a.set_yticks(range(4),methods)
 for i in range(4):
  for j in range(8):ax[0].text(j,i,'N/A' if np.isnan(joint[i,j]) else ('PASS' if joint[i,j] else 'FAIL'),ha='center',va='center',fontsize=7);ax[1].text(j,i,'N/A' if np.isnan(thermal[i,j]) else str(int(thermal[i,j])),ha='center',va='center',fontsize=8)
 ax[0].set_title('Joint native AC feasibility');ax[1].set_title('Thermal test (DC row: active flow only)');fig.suptitle('Experiment14: rated validity remains distinct from individual thermal checks');end(fig,O,'Gray: N/A or unknown AC reference. U300 has no finite ratings; U600 has only2 ties. DC is never a complete native AC state.','01-rated-feasibility')
 branches=csvread(O/'branch-flows.csv');fig,ax=plt.subplots(1,3,figsize=(11,4));cl={'AC-OPF':'#277c71','DC-OPF':'#333333',**colors}
 for a,n in zip(ax,['R300-base','R600-base','R300-low']):
  for m in methods:
   values=sorted([float(r['loading_ratio']) for r in branches if r['scenario']==n and r['method']==m and r['loading_ratio']],reverse=True);a.plot(range(1,len(values)+1),values,label=m,c=cl[m],ls='--' if m=='DC-OPF' else '-')
  a.axhline(1,c='#999',ls=':');a.set(xscale='log',xlabel='Independently ranked branch',ylabel='Loading ratio',title=n);a.grid(alpha=.15)
 ax[0].legend(fontsize=7);fig.suptitle('Experiment14: both-end apparent power relative to published ratings');end(fig,O,'DC dashed curves are |P|/RATE_A only; all other curves use max(|Sf|,|St|)/RATE_A. Each curve ranked independently.','02-ranked-ratios')
 response=csvread(O/'reference-relevant-rating-response.csv');fig,ax=plt.subplots(1,2,figsize=(11,4))
 for a,net in zip(ax,['300','600']):
  reference=[r for r in response if r['network']==net and r['method']=='AC-OPF'];chosen=sorted(reference,key=lambda r:(-abs(float(r['reference_delta_maxS_R_minus_U'])),int(r['branch_row_1based'])))[:8];ids=[r['branch_row_1based'] for r in chosen]
  for k,m in enumerate(['AC-OPF','microsoft-v1.1','newer-base-v2']):
   values=[next(float(r['method_delta_maxS_R_minus_U']) for r in response if r['network']==net and r['method']==m and r['branch_row_1based']==j) for j in ids];a.bar(np.arange(len(ids))+(k-1)*.24,values,width=.23,color=cl[m],label=m)
  a.axhline(0,c='#888',lw=.6);a.set_xticks(range(len(ids)),ids);a.set(title='PGLib'+net+' paired R−U response',xlabel='Original branch row',ylabel='Change in max both-end |S| (MVA)');a.grid(axis='y',alpha=.2)
 ax[0].legend(fontsize=7);fig.suptitle('Experiment14: supplying ratings changes outputs, but not necessarily appropriately');end(fig,O,'Branches selected only from near-binding R reference or overloaded U reference, ordered by |reference change|; first8 shown.','03-rating-response')
 print('14 FIGURES COMPLETE')
