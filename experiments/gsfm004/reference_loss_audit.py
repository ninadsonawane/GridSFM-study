"""Complete the reference-point contribution inventory; no model fit/forward."""
from neural import *
manifest=read(RUN/'data/manifest.json');item=Item(next(r for r in manifest['smoke_train'] if r['accepted']));out=item.batch();T=lambda x:torch.tensor(x,dtype=torch.float64)
out['bus'].pred=torch.stack([T(np.deg2rad(item.ref['va_deg'])),T(item.ref['vm'])],1);out['bus'].y=out['bus'].pred.clone();out['generator'].pred=torch.stack([T(np.array(item.ref['pg_mw'])/100),T(np.array(item.ref['qg_mvar'])/100)],1);out['generator'].y=out['generator'].pred.clone()
inventory={}
for arm in ['S','C','E']:
    loss,parts=objective(out,item.physics,arm);inventory[arm]=parts
save(RUN/'reference-loss-contributions.json',{'scenario_id':item.record['scenario_id'],'precision':'original accepted reference values FP64, original physics FP64; shared feature cost coefficients as released; identical prediction and target make supervised/cost terms zero','coefficient_policy':'all supervised/cost1; C/E KCL1 withlog1p; auxiliary0 skipped; eligiblebranch0','arms':inventory})
log('REFERENCE_LOSS_INVENTORY_COMPLETE',totals={k:v['total'] for k,v in inventory.items()})
