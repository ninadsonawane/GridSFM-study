"""Scientific figures only; isolated matplotlib directory, no training imports."""
import os,sys,json
from pathlib import Path
os.environ['MPLCONFIGDIR']='/private/tmp/gsfm007-20261021T195824Z/mpl-cache'
sys.path.insert(0,'/private/tmp/gsfm007-20261021T195824Z/plotdeps')
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(os.environ['GSFM007_RUN']);F=R/'figures';F.mkdir(exist_ok=True)
read=lambda p:json.loads(Path(p).read_text())
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
colors={11:'#1765a0',22:'#bd5b16',33:'#568341'}
fig,ax=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for i,net in enumerate(['case300','pglib118']):
 for seed in [11,22,33]:
  p=R/f'fits/{net}-s{seed}';v=read(p/'validation.json');summary=read(p/'summary.json');xx=[r['update'] for r in v];yy=[r['score'] for r in v]
  ax[i,0].plot(xx,yy,label=f'Seed {seed}',color=colors[seed]);ax[i,1].plot(xx,[r['fraction_converged'] for r in v],color=colors[seed],label=f'Seed {seed}')
  if summary['selected']:
   s=summary['selected'];ax[i,0].scatter(s['update'],s['score'],color=colors[seed],s=40,marker='*',zorder=5)
 for j in [0,1]:
  for step in [200,1250,1500]:ax[i,j].axvline(step,color='0.65',lw=.7,ls='--')
  ax[i,j].set_xlabel('Optimizer updates');ax[i,j].grid(alpha=.15)
 ax[i,0].set_yscale('log');ax[i,0].set_title(net+': released validation objective');ax[i,0].set_ylabel('Elastic + 32 × control loss');ax[i,0].legend()
 ax[i,1].set_title(net+': cold validation PF convergence');ax[i,1].set_ylabel('Converged fraction (10 cases)');ax[i,1].set_ylim(-.02,1.04);ax[i,1].axhline(.99,color='black',ls=':',lw=1)
fig.suptitle('Bounded adaptation: selected checkpoints marked ★; tight PF tolerance reached in epoch 25 (updates 1201–1250)',fontsize=11)
for suffix in ['pdf','png']:fig.savefig(F/f'01-learning-curves.{suffix}')
plt.close(fig)
fig,ax=plt.subplots(2,4,figsize=(13,6.8),layout='constrained');arms=['FT_P_ridge_V','ridge_P_FT_V','ridge_P_ridge_V'];labels=['FT P / ridge V','ridge P / FT V','ridge P / ridge V'];metrics=[('max_Pg_violation_MW','P-generation excess (MW)'),('max_Qg_violation_MVAr','Q-generation excess (MVAr)'),('max_voltage_violation_pu','Voltage excess (pu)'),('max_branch_violation_mva','Branch excess (MVA)')]
for i,net in enumerate(['case300','pglib118']):
 rr=[r for r in read(R/'factorial-paired-effects.json') if r['network']==net]
 for j,(metric,title) in enumerate(metrics):
  for offset,seed in zip([-.17,0,.17],[11,22,33]):
   yy=[float(np.median([r['change_relative_to_FT_P_FT_V'][metric] for r in rr if r['seed']==seed and r['controls']==a])) for a in arms]
   ax[i,j].scatter(np.arange(3)+offset,yy,color=colors[seed],label=f'Seed {seed}',s=30)
  ax[i,j].set_yscale('symlog',linthresh=1e-5 if metric=='max_voltage_violation_pu' else 1e-3);ax[i,j].axhline(0,color='0.4',lw=.8);ax[i,j].set_xticks(range(3),labels,rotation=45,ha='right');ax[i,j].set_title(net+': '+title);ax[i,j].grid(axis='y',alpha=.15)
  if net=='case300' and metric=='max_branch_violation_mva':ax[i,j].text(.5,.5,'Thermal N/A\nOriginal RATE_A=0',transform=ax[i,j].transAxes,ha='center',bbox=dict(facecolor='white',edgecolor='0.7'))
ax[0,0].legend(fontsize=8);fig.suptitle('Prespecified first 10 ordinary IDs: paired change versus FT P / FT V; common PQ initial magnitude 1 pu\nDots: median within-scenario change per seed; negative values reduce violations',fontsize=11)
for suffix in ['pdf','png']:fig.savefig(F/f'02-control-substitutions.{suffix}')
plt.close(fig)
rows=[r for r in read(R/'online-all.json') if r['repeat']>=0];fig,ax=plt.subplots(1,2,figsize=(12,5.8),layout='constrained');methods=['conventional','ridge','frozen','FT-s11-selected','FT-s22-selected','FT-s33-selected'];stages=[('preprocessing_seconds','Input preparation','#9ac4dd'),('inference_seconds','Inference','#1765a0'),('PF_seconds','Native PF','#de9854'),('solver_total_seconds','OPF incl. retry','#719658'),('independent_validation_seconds','Validation','#a27bb7')]
for i,net in enumerate(['case300','pglib118']):
 left=np.zeros(len(methods))
 for key,label,col in stages:
  yy=np.array([np.mean([r['times'].get(key,0) for r in rows if r['network']==net and r['method']==m]) for m in methods]);ax[i].barh(range(len(methods)),yy,left=left,label=label,color=col);left+=yy
 ax[i].set_yticks(range(len(methods)),methods);ax[i].invert_yaxis();ax[i].set_xlabel('Mean seconds per complete online request');ax[i].set_title(net);ax[i].grid(axis='x',alpha=.15)
ax[1].legend(loc='lower right',fontsize=8);fig.suptitle('Resident models, fresh per-request input preparation; all three interleaved repeats\nFinal quality/failure coverage must be read alongside timing; no inference-only speedup claim',fontsize=11)
for suffix in ['pdf','png']:fig.savefig(F/f'03-online-stages.{suffix}')
plt.close(fig)
print(json.dumps(dict(status='COMPLETE',matplotlib=matplotlib.__version__,figures=3,paths=[str(p) for p in F.iterdir()]),indent=2))
