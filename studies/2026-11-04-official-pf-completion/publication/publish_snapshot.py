"""Narrow GitHub release helper for the explicitly requested official PF extension snapshot upload."""
import argparse, hashlib, json, os, pathlib, subprocess, sys, urllib.error, urllib.parse, urllib.request

REPO='ninadsonawane/GridSFM-study'
TAG='official-pf-completion-checkpoint-2026-11-04'
BASE='https://api.github.com/repos/'+REPO
WORK=pathlib.Path(__file__).resolve().parent

def credentials():
    env=os.environ.copy(); env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
    p=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',text=True,capture_output=True,env=env,cwd=pathlib.Path(r'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work\GridSFM-study'))
    if p.returncode:
        raise RuntimeError('Git credential manager did not provide authentication; no credential output is displayed.')
    fields=dict(line.split('=',1) for line in p.stdout.splitlines() if '=' in line)
    if not fields.get('password'):raise RuntimeError('No GitHub credential available')
    return fields['password']

def request(path,method='GET',body=None,kind='application/json'):
    url=path if path.startswith('https://') else BASE+path
    assert url.startswith((BASE,'https://uploads.github.com/repos/'+REPO+'/'))
    headers={'Authorization':'Bearer '+TOKEN,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'GridSFM-PF-snapshot-user-authorized-publication'}
    data=None
    if body is not None:
        data=body if isinstance(body,bytes) else json.dumps(body).encode()
        headers['Content-Type']=kind
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)
    except urllib.error.HTTPError as e:
        message=e.read().decode('utf-8',errors='replace')
        raise RuntimeError('GitHub API HTTP '+str(e.code)+': '+message[:1500]) from None

p=argparse.ArgumentParser();p.add_argument('action',choices=['inspect','create','upload','verify']);p.add_argument('--commit');p.add_argument('--body-file',type=pathlib.Path);p.add_argument('--file',type=pathlib.Path);p.add_argument('--receipt',type=pathlib.Path);args=p.parse_args()
TOKEN=credentials()
if args.action=='inspect':
    repo=request(''); releases=request('/releases?per_page=20')
    print(json.dumps({'repository':repo['full_name'],'private':repo['private'],'default_branch':repo['default_branch'],'permissions':repo.get('permissions'),'releases':[{'tag':x['tag_name'],'url':x['html_url'],'assets':[{'name':a['name'],'size':a['size']} for a in x['assets']]} for x in releases]},indent=2))
elif args.action=='create':
    assert args.commit and args.body_file
    releases=request('/releases?per_page=100'); assert not any(x['tag_name']==TAG for x in releases),'Release already exists; inspect before changing'
    release=request('/releases',method='POST',body={'tag_name':TAG,'target_commitish':args.commit,'name':'Official PF extension: all current code and raw evidence','body':args.body_file.read_text(encoding='utf-8'),'draft':False,'prerelease':True,'make_latest':'false'})
    print(json.dumps({'id':release['id'],'tag':release['tag_name'],'url':release['html_url']},indent=2))
elif args.action=='upload':
    assert args.file and args.file.is_file();release=request('/releases/tags/'+TAG)
    assert not any(x['name']==args.file.name for x in release['assets']),'Asset already exists; do not replace'
    content=args.file.read_bytes();url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(args.file.name)
    asset=request(url,method='POST',body=content,kind='application/zip' if args.file.suffix=='.zip' else 'application/octet-stream')
    print(json.dumps({'id':asset['id'],'name':asset['name'],'bytes':asset['size'],'url':asset['browser_download_url'],'github_digest':asset.get('digest'),'local_sha256':hashlib.sha256(content).hexdigest()},indent=2))
else:
    release=request('/releases/tags/'+TAG);remote=request('/git/ref/heads/main');tag=request('/git/ref/tags/'+TAG)
    assert args.commit and args.file
    assert remote['object']['sha']==args.commit and tag['object']['sha']==args.commit
    assert not release['draft']
    expected=hashlib.sha256(args.file.read_bytes()).hexdigest()
    asset=next(x for x in release['assets'] if x['name']==args.file.name)
    assert asset['size']==args.file.stat().st_size and asset['state']=='uploaded'
    if asset.get('digest'):
        assert asset['digest']=='sha256:'+expected
        mode='GitHub asset SHA-256 digest compared to exact local archive'
    else:
        digest=hashlib.sha256()
        with urllib.request.urlopen(asset['browser_download_url'],timeout=180) as response:
            while chunk:=response.read(1024*1024):digest.update(chunk)
        assert digest.hexdigest()==expected
        mode='Downloaded public asset bytes SHA-256 compared to exact local archive'
    assert any(x['name']==args.file.name+'.sha256' and x['state']=='uploaded' for x in release['assets'])
    result={'status':'PASS','release_url':release['html_url'],'draft':release['draft'],'main_commit':remote['object']['sha'],'tag_commit':tag['object']['sha'],'verification':mode,'archive_sha256':expected,'assets':[{'name':x['name'],'bytes':x['size'],'url':x['browser_download_url'],'digest':x.get('digest'),'state':x['state']} for x in release['assets']]}
    if args.receipt:args.receipt.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(result,indent=2))

