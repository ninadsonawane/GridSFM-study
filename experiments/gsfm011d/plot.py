"""11D four compact figures, saved diagnostics only; no scientific runs."""
import pathlib,os,sys,json,csv
os.environ['MPLCONFIGDIR']='/private/tmp/gsfm011d-20261022/mplconfig'
sys.path.insert(0,'/private/tmp/gsfm007-20261021T195824Z/plotdeps')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=R/'results/diagnosis/GSFM-011D/20261022-saved-states';read=lambda n:json.loads((O/n).read_text());csvread=lambda n:list(csv.DictReader((O/n).open()));releases=['microsoft-v1.1','newer-base-v2'];titles={'microsoft-v1.1':'Microsoft v1.1','newer-base-v2':'Newer v2'};colors={'microsoft-v1.1':'#bd4d2b','newer-base-v2':'#6946a1'}
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':170,'axes.titleweight':'normal'})
def finish(fig,name,foot,rect=(0,.07,1,.94)):
 fig.text(.5,.012,foot,ha='center',fontsize=8);fig.tight_layout(rect=rect);fig.savefig(O/(name+'.png'));fig.savefig(O/(name+'.pdf'));plt.close(fig)
#1: cumulative concentration, all300 buses and top10 remainder.
rank=csvread('base-ranked-residuals.csv');fig,axes=plt.subplots(1,2,figsize=(9.4,3.9))
for ax,comp in zip(axes,['P','Q']):
 for release in releases:
  rr=[r for r in rank if r['release']==release and r['component']==comp];vals=np.array([float(r['absolute_imbalance']) for r in rr]);ax.plot(range(1,301),100*np.cumsum(vals)/sum(vals),color=colors[release],label=titles[release],lw=2)
 for k in [1,5,10]:ax.axvline(k,color='#999999',ls=':',lw=.7)
 ax.set(xscale='log',xlim=(1,300),ylim=(0,102),xlabel='Number of highest-imbalance buses (ranked separately)',ylabel='Share of total absolute imbalance (%)',title=f'Base case: {comp} imbalance concentration');ax.grid(alpha=.18)
axes[0].legend(fontsize=8);fig.suptitle('11D: hotspots do not account for all native imbalance',fontsize=12);finish(fig,'01-concentration','Top1/5/10 ranks marked. P and Q ranked separately; total is sum of absolute nodal residuals.')
#2: positive and negative branch-error terms kept separate to expose cancellation.
rows=csvread('base-bus-terms.csv');br=csvread('incident-branches.csv');fig,axes=plt.subplots(2,2,figsize=(10,6))
for col,release in enumerate(releases):
 bids=[238,231,137]+([98,44,61] if col==0 else [8,15,61]);xx=np.arange(6)
 for row,comp in enumerate(['P','Q']):
  ax=axes[row,col];vectors=[];net=[]
  for bid in bids:
   r=next(r for r in rows if r['release']==release and int(r['bus_id'])==bid);errors=[-float(z[f"out_{comp}_delta_{'MW' if comp=='P' else 'MVAr'}"]) for z in br if z['release']==release and float(z['loading'])==1 and int(z['focus_bus'])==bid];vectors.append([float(r['generation_'+comp+'_delta']),sum(max(e,0) for e in errors),sum(min(e,0) for e in errors),-float(r['shunt_consumption_'+comp+'_delta'])]);net.append(float(r['residual_'+comp+'_pred']))
  vv=np.array(vectors);pos=np.zeros(6);neg=np.zeros(6)
  for k,(label,color) in enumerate([('Generation error','#7044a0'),('Positive branch-error contributions','#197b98'),('Negative branch-error contributions','#da8646'),('Bus-shunt contribution','#8b9198')]):
   values=vv[:,k];ax.bar(xx,values,bottom=np.where(values>=0,pos,neg),color=color,label=label,width=.65);pos+=np.maximum(values,0);neg+=np.minimum(values,0)
  ax.scatter(xx,net,c='black',marker='D',s=20,label='Net signed residual',zorder=5);ax.axhline(0,c='#555',lw=.6);ax.set_xticks(xx,[str(x)+(' L' if i>=3 else '') for i,x in enumerate(bids)]);ax.set_yscale('symlog',linthresh=10);ax.set(title=titles[release]+f' — {comp}',ylabel='Signed error contribution ('+('MW' if comp=='P' else 'MVAr')+')');ax.grid(axis='y',alpha=.15)
handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=7,bbox_to_anchor=(.5,.035));fig.suptitle('11D base case: signed budgets and cancellation',fontsize=12);finish(fig,'02-signed-budgets','L = deterministic lower-error comparator; most matches are poor. Symlog axes expose small nets; Δ demand = 0.',rect=(0,.15,1,.94))
#3: all8 complete-network substitutions, oracle-only; maxima and means separately.
cs=read('oracle-combinations.json');fig,axes=plt.subplots(2,2,figsize=(9.5,5.6));masks=['000','001','010','011','100','101','110','111']
for col,release in enumerate(releases):
 for row,comp in enumerate(['P','Q']):
  ax=axes[row,col];rr=[next(r for r in cs if r['release']==release and r['loading']==1 and r['blocks_reference_G_V_A']==mask) for mask in masks];mx=[r[comp+'_max_'+('MW' if comp=='P' else 'MVAr')] for r in rr];mean=[r[comp+'_mean_abs_'+('MW' if comp=='P' else 'MVAr')] for r in rr];mx=[0 if x<1e-6 else x for x in mx];mean=[0 if x<1e-6 else x for x in mean];ax.bar(range(8),mean,color=colors[release],alpha=.4,label='Mean absolute');ax.plot(range(8),mx,'o-',color=colors[release],label='Maximum absolute',markersize=4);ax.set_xticks(range(8),masks);ax.set_yscale('symlog',linthresh=1);ax.set_ylim(0,max(mx)*1.6);ax.set(title=titles[release]+f' — {comp}',ylabel=('MW' if comp=='P' else 'MVAr'));ax.grid(axis='y',alpha=.2)
axes[0,0].legend(fontsize=8);fig.suptitle('11D: known-answer block substitutions — diagnostics only',fontsize=12);finish(fig,'03-oracle-blocks','Mask G V A: 1 = reference, 0 = native. G includes Pg and Qg together. All-reference residuals <1e−6 shown as 0.\nNot practical repairs; changes interact and can worsen imbalance.',rect=(0,.09,1,.94))
#4: fixed-bus loading traces, plus the precise90→95 branch-state change.
tr=csvread('fixed-bus-loading-terms.csv');ib=csvread('incident-branches.csv');fig,axes=plt.subplots(2,2,figsize=(10,6.2));scales=[.8,.9,.95,1.,1.03,1.06,1.1];buscols={238:'#b3472d',231:'#177e91',137:'#7141a0'}
for col,release in enumerate(releases):
 ax=axes[0,col]
 for bid in [238,231,137]:
  rr=sorted([r for r in tr if r['release']==release and int(r['bus_id'])==bid],key=lambda r:float(r['loading']));ax.plot([float(r['loading']) for r in rr],[float(r['residual_Q_pred']) for r in rr],'o-',c=buscols[bid],label=f'Bus{bid}',markersize=3)
 low=44 if col==0 else 15;rr=sorted([r for r in tr if r['release']==release and int(r['bus_id'])==low],key=lambda r:float(r['loading']));ax.plot([float(r['loading']) for r in rr],[float(r['residual_Q_pred']) for r in rr],':',c='#333333',label=f'Low comparator{low}');ax.axhline(0,c='#888',lw=.6);ax.axvspan(.90,.95,color='#dddddd',alpha=.4);ax.axvline(1.,ls=':',c='#999',lw=.7);ax.set(title=titles[release]+' — fixed bus Q residuals',ylabel='Signed Q imbalance (MVAr)',xlabel='Original Pd/Qd multiplier');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.15)
rr=sorted([r for r in ib if r['release']=='newer-base-v2' and int(r['focus_bus'])==238 and int(r['branch_row_1based'])==321],key=lambda r:float(r['loading']));x=[float(r['loading']) for r in rr];ax=axes[1,0]
for key,label,color in [('Vm_from_pred','Native235','#b3472d'),('Vm_to_pred','Native238','#177e91')]:ax.plot(x,[float(r[key]) for r in rr],'o-',label=label,color=color,markersize=3)
for key,label,color in [('Vm_from_ref','Reference235','#b3472d'),('Vm_to_ref','Reference238','#177e91')]:ax.plot(x,[float(r[key]) if r[key] else np.nan for r in rr],'--',label=label,color=color,alpha=.7)
ax.axvspan(.90,.95,color='#dddddd',alpha=.4);ax.set(title='Newer v2: endpoint magnitudes on row321',ylabel='Vm (pu)',xlabel='Original Pd/Qd multiplier');ax.legend(fontsize=7,ncol=2);ax.grid(alpha=.15)
ax=axes[1,1];ax.plot(x,[float(r['out_Q_pred_MVAr']) for r in rr],'o-',color='#b3472d',label='Native Q at238 end',markersize=3);ax.plot(x,[float(r['out_Q_ref_MVAr']) if r['out_Q_ref_MVAr'] else np.nan for r in rr],'--',c='#777',label='Reference Q at238 end');ax.axvspan(.90,.95,color='#dddddd',alpha=.4);ax.set(title='Original row321 (235→238): Q outgoing at238',ylabel='MVAr',xlabel='Original Pd/Qd multiplier');ax.legend(fontsize=7);ax.grid(alpha=.15)
fig.suptitle('11D: loading changes the location and mechanism of failure',fontsize=12);finish(fig,'04-loading-transition','All points were already saved. 1.00 is11B. 1.10 is reference-free; dashed reference traces stop at1.06.\nShaded90→95 interval: Vm235 leaves its lower bound, but bus137 Q imbalance worsens.',rect=(0,.085,1,.94))
print('FOUR FIGURES READY')
