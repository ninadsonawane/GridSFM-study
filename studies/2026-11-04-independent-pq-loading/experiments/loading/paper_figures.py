from study import *
from focused import state,locate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':7,'axes.labelsize':7,'axes.titlesize':8,'legend.fontsize':6,'xtick.labelsize':6,'ytick.labelsize':6})
out=ROOT/'paper/figures';plan=read(ROOT/'scenario-plan.json')['scenarios']
fig,axes=plt.subplots(3,1,figsize=(3.35,4.7))
for ax,net in zip(axes,['case300','case300x2','case500goc']):
 for method,color in [('microsoft-v1.1','#1874b8'),('newer-base-v2','#d34d39')]:
  for group,ls in [('P','-'),('Q','--'),('PQ',':')]:
   items=[{'id':net+'-base','absolute_P_factor':1.,'absolute_Q_factor':1.}]+[s for s in plan if s['network']==net and s['group']==group]
   x=[];y=[]
   for item in items:
    m=next(m for m in read(ROOT/'results'/item['id']/'metrics.json') if m['method']==method);x.append(max(item['absolute_P_factor'],item['absolute_Q_factor']));y.append(m['Q_balance_MVAr']['max_abs'])
   ax.plot(x,y,ls,color=color,linewidth=1.1,label=('V1' if method.startswith('microsoft') else 'V2')+' '+group)
 ax.set_title(net);ax.set_ylabel('Max |Q residual| (MVAr)');ax.grid(alpha=.2)
axes[-1].set_xlabel('Absolute loading factor');h,l=axes[0].get_legend_handles_labels();fig.legend(h,l,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.));fig.tight_layout(rect=[0,0,1,.93]);fig.savefig(out/'paper-loading.png',dpi=300);plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(3.35,3.1))
for method,color in [('microsoft-v1.1','#1874b8'),('newer-base-v2','#d34d39')]:
 pts=sorted([s for s in plan if s['group']=='case3-PQ'],key=lambda s:s['absolute_P_factor']);x=[];v=[[],[],[],[]]
 for p in pts:
  d=ROOT/'results'/p['id'];m=next(m for m in read(d/'metrics.json') if m['method']==method);s=state(d,method);c=read(d/'input.json');i=next(i for i,b in enumerate(c['bus']) if b[0]==235);x.append(p['absolute_P_factor'])
  for ar,z in zip(v,[m['Q_balance_MVAr']['max_abs'],m['Q_balance_MVAr']['p95_abs'],m['Q_balance_MVAr']['violating_bus_count'],s['vm'][i]]):ar.append(z)
 for ax,y in zip(axes.flat,v):ax.plot(x,y,'.-',color=color,markersize=2,label='V1' if method.startswith('microsoft') else 'V2')
for ax,label in zip(axes.flat,['Q max (MVAr)','Q p95 (MVAr)','Q violating buses','V at bus 235 (pu)']):ax.set_title(label);ax.grid(alpha=.2);ax.set_xticks([.92,.93,.94,.95])
axes[0,0].legend();axes[1,0].set_xlabel('Absolute P/Q factor');axes[1,1].set_xlabel('Absolute P/Q factor');fig.tight_layout(pad=.7);fig.savefig(out/'paper-case3.png',dpi=300);plt.close(fig)
