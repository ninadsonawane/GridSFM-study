"""All requested loading metrics and focused paper figures from saved CSV/JSON."""
import csv, json, pathlib, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=ROOT/'paper'; OUT=P/'figures'; OUT.mkdir(exist_ok=True)
FULL=OUT/'all-metrics'; FULL.mkdir(exist_ok=True)
rows=list(csv.DictReader((P/'all-metrics.csv').open(newline='',encoding='utf-8')))
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':8,'axes.titlesize':9,'axes.labelsize':8,'pdf.fonttype':42,'ps.fonttype':42,'savefig.dpi':180})
METHODS={'AC-OPF':('AC reference','#171717'), 'DC-OPF':('DC (own applicability)','#888888'),
 'microsoft-v1.1':('V1 native','#0072B2'),'newer-base-v2':('V2 native','#D55E00'),
 'V2-frozen+official-PF':('Frozen + PF','#CC79A7'),'V2-frozen+official-PF-exact-matrix':('Frozen + PF exact','#7A5195'),
 'V2-adapted-native':('Adapted native','#E69F00'),'V2-adapted+official-PF':('Adapted + PF','#009E73'),
 'V2-adapted+official-PF-exact-matrix':('Adapted + PF exact','#336633')}
def num(r,key):
    v=r.get(key,'')
    if v in ['',None]:return None
    if v in ['True','False']:return float(v=='True')
    try:return float(v)
    except (TypeError,ValueError):return None
def save(fig,name,folder=OUT):
    fig.savefig(folder/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(folder/(name+'.png'),bbox_inches='tight')
    plt.close(fig)
def alpha(r,path):return float(r['absolute_Q_factor'] if path=='Q' else r['absolute_P_factor'])
def all_metrics():
    metrics=[]
    for var,unit in [('Pg_MW','MW'),('Qg_MVAr','MVAr'),('V_pu','p.u.'),('aligned_angle_deg','degrees')]:
        for stat in ['MAE','RMSE']:metrics.append(('accuracy.'+var+'.'+stat,unit))
    for var,unit in [('P_balance_MW','MW'),('Q_balance_MVAr','MVAr')]:
        for stat in ['max_abs','mean_abs','p95_abs','violating_bus_count']:metrics.append((var+'.'+stat,'buses' if 'count' in stat else unit))
    for var,unit in [('Pg_MW','MW'),('Qg_MVAr','MVAr'),('voltage_pu','p.u.'),('branch_thermal_MVA','MVA'),('branch_angle_deg','degrees'),('branch_active_MW','MW (DC)')]:
        for stat in ['violating_count','maximum','mean_all']:metrics.append(('constraints.'+var+'.'+stat,'items' if 'count' in stat else unit))
    metrics += [('AC_joint_pass','pass = 1'),('DC_own_constraints_pass','pass = 1')]
    index=[]
    for key,unit in metrics:
        fig,axes=plt.subplots(3,3,figsize=(10.5,7.7),sharex=True,sharey=True)
        plotted=[];handles={}
        for i,net in enumerate(['case300','case300x2','case500goc']):
            for j,path in enumerate(['P','Q','PQ']):
                ax=axes[i,j]; data=[r for r in rows if r['network']==net and r['group'] in ['baseline',path]]
                count=0
                for method,(label,color) in METHODS.items():
                    if method=='DC-OPF' and key.startswith(('P_balance','Q_balance')):continue
                    rr=sorted([r for r in data if r['method']==method and num(r,key) is not None],key=lambda r:alpha(r,path))
                    if not rr:continue
                    xx=[alpha(r,path) for r in rr]; yy=[num(r,key) for r in rr]
                    if key=='AC_joint_pass':yy=[float(num(r,key)==1 and r.get('PF_converged')!='False') for r in rr]
                    line,=ax.plot(xx,yy,color=color,ls='--' if 'official-PF' in method else '-',marker='.' if 'official-PF' not in method else 'o',ms=3,lw=1,label=label)
                    handles[method]=line
                    bad=[k for k,r in enumerate(rr) if r.get('PF_converged')=='False']
                    if bad:ax.scatter(np.asarray(xx)[bad],np.asarray(yy)[bad],marker='x',c=color,s=30,zorder=5)
                    count+=len(rr);plotted += [{'scenario':r['id'],'method':method,'value':v} for r,v in zip(rr,yy)]
                ax.set_title(net+' | '+path+' only' if path!='PQ' else net+' | combined')
                ax.grid(alpha=.22);ax.set_xlim(.998,1.102);ax.set_xticks([1,1.02,1.05,1.10])
                if not count:ax.text(.5,.5,'N/A',ha='center',va='center',transform=ax.transAxes)
                if i==2:ax.set_xlabel('Absolute demand factor')
                if j==0:ax.set_ylabel(unit)
        if unit not in ['buses','items','pass = 1']:
            for ax in axes.flat:ax.set_yscale('symlog',linthresh=1e-4 if unit=='p.u.' else 1e-3)
            axes[0,0].set_ylim(bottom=0)
        elif unit=='pass = 1':axes[0,0].set_ylim(-.08,1.08)
        fig.suptitle(key.replace('_',' '),fontsize=11)
        fig.legend(list(handles.values()),[METHODS[m][0] for m in handles],loc='lower center',ncol=3,fontsize=7,bbox_to_anchor=(.5,.025))
        fig.text(.5,.006,'Crosses = failed finite PF iterates, not operating solutions. Shared baseline appears on each path. Blank values are N/A/UNKNOWN.',ha='center',fontsize=7)
        fig.tight_layout(rect=(0,.13,1,.96))
        slug=key.replace('.','-');save(fig,slug,FULL)
        index.append({'metric':key,'unit':unit,'pdf':'all-metrics/'+slug+'.pdf','png':'all-metrics/'+slug+'.png','plotted_points_with_path_duplicates':len(plotted),'data':plotted})
    (OUT/'metric-plot-index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
    print('METRIC_FIGURES',len(index),flush=True)
def case3_curves():
    index=[]
    for path in ['P','Q','PQ']:
        fig,axes=plt.subplots(2,2,figsize=(7.1,5.0))
        data=[r for r in rows if r['group']=='case3-'+path or (r['group']=='case3-PQ' and float(r['absolute_P_factor'])==.93)]
        methods=['AC-OPF','microsoft-v1.1','newer-base-v2','V2-frozen+official-PF','V2-frozen+official-PF-exact-matrix']
        for method in methods:
            rr=sorted([r for r in data if r['method']==method],key=lambda r:alpha(r,path))
            for ax,key,label in zip(axes.flat,['max_abs','mean_abs','p95_abs','violating_bus_count'],['Maximum (MVAr)','Mean (MVAr)','p95 (MVAr)','Violating buses']):
                xx=[alpha(r,path) for r in rr];yy=[num(r,'Q_balance_MVAr.'+key) for r in rr]
                ax.plot(xx,yy,c=METHODS[method][1],ls='--' if 'official-PF' in method else '-',marker='x' if 'official-PF' in method else '.',label=METHODS[method][0],lw=1)
                ax.set_ylabel(label);ax.set_xlabel('Absolute '+path+' demand factor');ax.grid(alpha=.2)
        for ax in list(axes.flat)[:3]:
            ax.set_yscale('symlog',linthresh=.001)
            ax.set_ylim(bottom=0)
        fig.suptitle('case300 case 3 | '+path+' path | crosses are failed PF iterates',fontsize=10)
        handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=7)
        fig.tight_layout(rect=(0,.10,1,.95));save(fig,'case3-'+path)
        index.append({'path':path,'scenarios':sorted({r['id'] for r in data}),'pdf':'case3-'+path+'.pdf'})
    (OUT/'case3-plot-index.json').write_text(json.dumps(index,indent=2)+'\n',encoding='utf-8')
def workflow():
    fig,ax=plt.subplots(figsize=(7.1,1.7));ax.set_xlim(0,10);ax.set_ylim(0,3);ax.axis('off')
    boxes=[(.05,1.3,2.0,'Original case\nPrescribed P/Q loads'),(2.65,1.3,2.0,'Released checkpoint\nNative state / controls'),(5.25,1.3,2.0,'Author Newton PF\nFix non-slack Pg\nand controlled |V|'),(7.85,1.3,2.05,'Original-case audit\nBalance + equipment')]
    for x,y,w,t in boxes:
        ax.add_patch(FancyBboxPatch((x,y),w,.95,boxstyle='round,pad=.06',fc='#f2f4f7',ec='#465464',lw=.8));ax.text(x+w/2,y+.475,t,ha='center',va='center',fontsize=6.5)
    for x in [2.15,4.75,7.35]:ax.annotate('',xy=(x+.42,1.78),xytext=(x,1.78),arrowprops={'arrowstyle':'->','lw':1})
    ax.annotate('Native audit',xy=(8.4,2.25),xytext=(3.65,2.72),ha='center',fontsize=7,arrowprops={'arrowstyle':'->','connectionstyle':'arc3,rad=-.13','lw':.8})
    ax.text(3.65,.8,'Frozen weights or verified case500 adaptation\n(separate rows; no new training)',ha='center',va='center',fontsize=7)
    ax.text(6.25,.36,'Exact-matrix PF: separate numerical diagnostic',ha='center',va='center',fontsize=7)
    ax.text(8.9,.9,'Projection / warm-started OPF:\nseparate downstream stages, unrun',ha='center',va='center',fontsize=7)
    save(fig,'workflow')
def paper_results():
    fig,axes=plt.subplots(2,2,figsize=(7.1,4.35))
    a=axes[0,0]
    for key,ls,label in [('constraints.Pg_MW.maximum','-','Slack P excess (MW)'),('constraints.Qg_MVAr.maximum','--','Max Q excess (MVAr)'),('constraints.branch_thermal_MVA.maximum',':','Thermal excess (MVA)')]:
        for path,col in [('Q','#D55E00'),('PQ','#0072B2')]:
            rr=sorted([r for r in rows if r['network']=='case500goc' and r['method']=='V2-adapted+official-PF' and r['group'] in ['baseline',path]],key=lambda r:alpha(r,path))
            a.plot([alpha(r,path) for r in rr],[num(r,key) for r in rr],ls=ls,c=col,marker='.',label=path+': '+label,lw=1)
    a.set_title('(a) case500goc: adapted + PF');a.set_ylabel('Maximum limit excess');a.set_xlabel('Absolute demand factor');a.legend(fontsize=5.8,ncol=1,loc='upper left');a.grid(alpha=.2)
    b=axes[0,1]
    ss=json.loads((P/'case3/summary.json').read_text());rr=next(r for r in ss if r['method']=='newer-base-v2')
    for k,label,col in [('max','Maximum','#D55E00'),('p95','p95','#0072B2'),('mean','Mean','#009E73')]:
        b.plot([.93,.94],[rr['Q_093'][k],rr['Q_094'][k]],marker='o',label=label,c=col)
    b.set_yscale('log');b.set_xticks([.93,.94]);b.set_xlabel('Absolute combined demand factor');b.set_ylabel('|Q residual| (MVAr)');b.set_title('(b) case300 case 3: native V2');b.legend(fontsize=7);b.grid(alpha=.2)
    sense=json.loads((P/'sensitivity-summary.json').read_text()); intervals=[(1,1.005),(1,1.01),(1.01,1.02)]
    for method in ['newer-base-v2','V2-adapted-native','V2-adapted+official-PF']:
        rr=[next(r for r in sense if r['network']=='case500goc' and r['component']=='Q' and r['variable']=='qg_mvar' and r['method']==method and r['left']==l and r['right']==h) for l,h in intervals]
        label,col=METHODS[method]
        axes[1,0].plot(range(3),[r['direction_agreement_percent'] for r in rr],c=col,marker='o',label=label)
        axes[1,1].plot(range(3),[r['response_derivative_RMSE'] for r in rr],c=col,marker='o',label=label)
    for ax in axes[1]:ax.set_xticks(range(3),['0 to +0.5%','0 to +1%','+1 to +2%']);ax.set_xlabel('Q-only interval from nominal');ax.grid(alpha=.2)
    axes[1,0].set_title('(c) case500goc: Qg direction');axes[1,0].set_ylabel('Agreement with AC reference (%)');axes[1,0].set_ylim(0,100);axes[1,0].legend(fontsize=6)
    axes[1,1].set_title('(d) case500goc: Qg response error');axes[1,1].set_ylabel('RMSE (MVAr per unit load factor)')
    fig.tight_layout(pad=.9);save(fig,'focused-results')

if __name__=='__main__':
    all_metrics();case3_curves();workflow();paper_results()
