import hashlib,json,pathlib,urllib.request
locations=json.loads(pathlib.Path(__file__).with_name('pf-extension-locations.json').read_text())
root=pathlib.Path(locations['extension']); repo=pathlib.Path(locations['repo'])
revision='970a413556fd1dc8c843cafdb03b01f9f8ef6f44'
base='https://huggingface.co'
tree=json.load(urllib.request.urlopen(base+'/api/models/lukebhan/gridsfm/tree/'+revision+'/case500_goc/n0100',timeout=60))
entry=next(x for x in tree if x['path'].endswith('/control_model.pt'))
dest=repo/'work/checkpoints/case500_goc-n0100-control_model.pt'
dest.parent.mkdir(parents=True,exist_ok=True)
expected=entry['lfs']['oid']
if not dest.exists():
    url=base+'/lukebhan/gridsfm/resolve/'+revision+'/'+entry['path']
    with urllib.request.urlopen(url,timeout=180) as response,dest.open('wb') as stream:
        while block:=response.read(1024*1024):stream.write(block)
digest=hashlib.sha256(dest.read_bytes()).hexdigest()
assert digest==expected,(digest,expected)
record={'repository':'lukebhan/gridsfm','revision':revision,'path':entry['path'],'sha256':digest,'size':dest.stat().st_size,
        'published_lfs':entry['lfs'],'local_path':str(dest),
        'selection':'n0100 chosen before observing results, matching the published 100-label comparison; no selection across checkpoints',
        'topology_compatibility':'all baseMVA/bus/gen/branch/gencost matrices exactly equal pinned author case500_goc source (integration-inspection.json)',
        'case300_and_case300x2':'No compatible target-grid adapted checkpoint in released model roster; not substituted with case500 weights',
        'operating_point_exposure':'Exact training/validation/test membership of the 59 study scenarios is UNVERIFIED; do not claim held-out generalization'}
(root/'manifests/adapted-checkpoint.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
