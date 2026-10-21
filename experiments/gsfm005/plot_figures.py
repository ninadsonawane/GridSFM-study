"""Scientific figures using existing bundled ReportLab charts and PDFium; no training imports."""
import os,json,csv
from pathlib import Path
from reportlab.graphics.shapes import Drawing,String,Line
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
from reportlab.lib import colors
import pypdfium2 as pdfium
REPO=Path(os.environ.get('GSFM005_ROOT','/Users/ninadsonawane/workspace/research-dev/GridSFM-study'))
RUN=REPO/'results/pilots/GSFM-005'/os.environ.get('GSFM005_RUN_ID','20261021T120300Z-m5-seeds11-22-33')
read=lambda p:json.loads(p.read_text())
C=[colors.HexColor(x) for x in ['#66717e','#d07942','#3c6faf','#34855d']]
W,H=900,340

def title(d,t,sub):d.add(String(W/2,H-22,t,fontName='Helvetica-Bold',fontSize=18,textAnchor='middle'));d.add(String(W/2,H-39,sub,fontSize=13,textAnchor='middle'))
def save(d,name):
 p=RUN/'figures'/name;p.parent.mkdir(exist_ok=True);renderPDF.drawToFile(d,str(p.with_suffix('.pdf')))
 doc=pdfium.PdfDocument(str(p.with_suffix('.pdf')));doc[0].render(scale=2).to_pil().save(p.with_suffix('.png'));doc.close()
def linepanel(d,x,data,heading,ylabel,xlabel='Optimizer updates',xsteps=None):
 chart=LinePlot();chart.x=x+48;chart.y=73;chart.width=220;chart.height=190;chart.data=data;chart.joinedLines=1
 chart.xValueAxis.labels.fontSize=12;chart.yValueAxis.labels.fontSize=12;chart.xValueAxis.visibleGrid=0;chart.yValueAxis.visibleGrid=1;chart.yValueAxis.gridStrokeColor=colors.HexColor('#dddddd');chart.yValueAxis.gridStrokeWidth=.35
 vals=[y for series in data for _,y in series];lo=min(vals);hi=max(vals);span=max(hi-lo,.01)
 if xlabel=='Training seed':lo=min(lo,0);hi=max(hi,0);span=max(hi-lo,.01);chart.xValueAxis.valueMin=9;chart.xValueAxis.valueMax=35;chart.xValueAxis.valueSteps=[11,22,33]
 else:chart.xValueAxis.valueMin=0;chart.xValueAxis.valueMax=1000;chart.xValueAxis.valueSteps=[0,250,500,750,1000]
 chart.yValueAxis.valueMin=lo-.12*span;chart.yValueAxis.valueMax=hi+.12*span
 for i in range(len(data)):chart.lines[i].strokeColor=C[i];chart.lines[i].strokeWidth=1.5
 d.add(chart);d.add(String(x+156,280,heading,fontName='Helvetica-Bold',fontSize=15,textAnchor='middle'));d.add(String(x+156,54,xlabel,fontSize=13,textAnchor='middle'));d.add(String(x+48,269,ylabel,fontSize=13))
 if xlabel=='Training seed':
  yy=chart.y+chart.height*(0-chart.yValueAxis.valueMin)/(chart.yValueAxis.valueMax-chart.yValueAxis.valueMin);d.add(Line(chart.x,yy,chart.x+chart.width,yy,strokeColor=colors.black,strokeWidth=.6))
def legend(d,names):
 for i,name in enumerate(names):
  x=260+100*i;d.add(Line(x,26,x+20,26,strokeColor=C[i],strokeWidth=2));d.add(String(x+26,23,name,fontSize=13))
def main():
 fits=read(RUN/'training-summary.json');contrasts=read(RUN/'contrasts.json')['all_contrasts'];arms=['S','C','E','C_m'];d=Drawing(W,H);title(d,'Validation learning curves','Original 10 validation cases; lower joint log-balance is better')
 for j,seed in enumerate([11,22,33]):
  data=[[(v['update'],v['key'][0]) for v in next(f for f in fits if (f['seed'],f['arm'])==(seed,arm))['validation']] for arm in arms];linepanel(d,j*300,data,f'Seed {seed}','Joint log-balance')
 legend(d,arms);save(d,'01-validation-curves')
 d=Drawing(W,H);title(d,'Exact KCL minus magnitude-matched stock control','Ordinary evaluation; paired scenario mean differences; negative favors E; no independence or significance claim')
 for j,(key,label) in enumerate([('joint_log_balance','Mean change in J'),('max_p_residual_mw','Mean change in Pmax (MW)'),('max_q_residual_mvar','Mean change in Qmax (MVAr)')]):
  data=[[(seed,next(c for c in contrasts if (c['seed'],c['endpoint'],c['split'],c['contrast'])==(seed,ep,'ordinary','E-minus-C_m'))[key+'_paired_mean_change']) for seed in [11,22,33]] for ep in ['selected','200','500','1000']];linepanel(d,j*300,data,['Joint score','Active imbalance','Reactive imbalance'][j],label,'Training seed')
 legend(d,['selected','200','500','1000']);save(d,'02-E-minus-Cm')
 with (RUN/'paired-summary.csv').open(newline='') as f:pairs=list(csv.DictReader(f))
 d=Drawing(W,H);title(d,'Paired deterioration after relocating demand','Spatial minus ordinary; same total P/Q; validation-selected snapshots; mean of accepted pairs')
 groups=[('ridge','')]+[(arm,str(seed)) for seed in [11,22,33] for arm in ['C','E','C_m']];labels=['ridge']+[f'{a}/{s}' for a,s in groups[1:]]
 for j,(key,label) in enumerate([('joint_log_balance','Mean change in J'),('max_p_residual_mw','Mean change in Pmax (MW)'),('max_q_residual_mvar','Mean change in Qmax (MVAr)')]):
  vals=[]
  for arm,seed in groups:
   vv=[float(p[key+'_change']) for p in pairs if (p['method'],p['seed'],p['endpoint'])==(arm,seed,'selected' if seed else 'baseline')];vals.append(sum(vv)/len(vv))
  chart=VerticalBarChart();chart.x=j*300+48;chart.y=95;chart.width=220;chart.height=170;chart.data=[vals];chart.categoryAxis.categoryNames=labels;chart.categoryAxis.labels.angle=55;chart.categoryAxis.labels.boxAnchor='ne';chart.categoryAxis.labels.fontSize=10;chart.valueAxis.labels.fontSize=12;chart.valueAxis.visibleGrid=1;chart.valueAxis.gridStrokeColor=colors.HexColor('#dddddd');chart.valueAxis.gridStrokeWidth=.35
  lo=min(min(vals),0);hi=max(max(vals),0);span=max(hi-lo,.01);chart.valueAxis.valueMin=lo-.08*span;chart.valueAxis.valueMax=hi+.08*span
  for i,(a,s) in enumerate(groups):chart.bars[(0,i)].fillColor=colors.HexColor('#8172b3') if a=='ridge' else C[arms.index(a)];chart.bars[(0,i)].strokeColor=None
  d.add(chart);d.add(String(j*300+48,280,label,fontSize=13));d.add(String(j*300+156,20,'Method / training seed',fontSize=13,textAnchor='middle'))
 save(d,'03-spatial-deterioration')
 print('THREE_FIGURES_GENERATED')
if __name__=='__main__':main()
