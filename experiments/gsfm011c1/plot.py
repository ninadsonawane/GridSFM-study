"""Plots from saved metrics only; no scientific calls."""
import pathlib,sys,json,os
os.environ['MPLCONFIGDIR']='/private/tmp/gsfm011c1-20261022/mplconfig'
sys.path.insert(0,'/private/tmp/gsfm007-20261021T195824Z/plotdeps')
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
R=pathlib.Path('/Users/ninadsonawane/workspace/research-dev/GridSFM-study');O=pathlib.Path(os.environ.get('GSFM011C1_OUTPUT',str(R/'results/comparisons/GSFM-011C-1/20261022-loading-only')));A=json.loads((O/'approximation.json').read_text());P=json.loads((O/'physical-validity.json').read_text());colors={'AC-OPF':'#5a6571','DC-OPF':'#2274a5','Microsoft v1.1':'#c4512d','Newer v2':'#6a4897'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
fig,axes=plt.subplots(1,2,figsize=(10,4.4))
for ax,key,title in zip(axes,['Pg_MW','Qg_MVAr'],['Active generation error (MW)','Reactive generation error (MVAr)']):
 for method in ['AC-OPF','DC-OPF','Microsoft v1.1','Newer v2']:
  if key=='Qg_MVAr' and method=='DC-OPF':continue
  rows=[r for r in A if r['method']==method];xx=[r['loading'] for r in rows];yy=[np.nan if r[key] is None else r[key]['MAE'] for r in rows];ax.plot(xx,yy,'o-',color=colors[method],label=method,markersize=4)
 ax.axvline(1,color='#999',ls=':',lw=1);ax.axvspan(1.085,1.115,color='#dddddd',alpha=.55);ax.set(xlabel='Original Pd and Qd multiplier',ylabel='MAE',title=title,xlim=(.785,1.115));ax.grid(alpha=.2)
axes[0].legend(fontsize=8);fig.suptitle('11C-1: approximation to independently validated AC-OPF references',fontsize=12);fig.text(.5,.015,'1.00 reused from 11B. At 1.10 AC reference unavailable: errors N/A for all methods. DC Qg is N/A.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.045,1,.94));fig.savefig(O/'generation-error.png');fig.savefig(O/'generation-error.pdf');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,4.5))
for ax,key,title in zip(axes,['max_P_imbalance_MW','max_Q_imbalance_MVAr'],['Maximum nodal P imbalance (MW)','Maximum nodal Q imbalance (MVAr)']):
 for method in ['AC-OPF','Microsoft v1.1','Newer v2']:
  rows=[r for r in P if r['method']==method];ax.plot([r['loading'] for r in rows],[r[key] for r in rows],'o-',color=colors[method],label=method,markersize=4)
 ax.axvline(1,color='#999',ls=':',lw=1);ax.axvspan(1.085,1.115,color='#dddddd',alpha=.55);ax.set(xlabel='Original Pd and Qd multiplier',ylabel='Maximum absolute residual',title=title,xlim=(.785,1.115));ax.grid(alpha=.2)
axes[0].legend(fontsize=8);fig.suptitle('11C-1: native states evaluated with unchanged original FP64 AC physics',fontsize=12);fig.text(.5,.04,'1.00 reused. AC at 1.10 is a failed returned iterate, not a reference. No PF completion or OPF repair.',ha='center',fontsize=9);fig.text(.5,.008,'DC AC balance is N/A; its separate DC-law P residual is below 1.1e-11 MW at every displayed loading.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.08,1,.94));fig.savefig(O/'power-imbalance.png');fig.savefig(O/'power-imbalance.pdf');plt.close(fig)
