import pathlib,json,hashlib,platform,os,subprocess,zipfile,datetime,ast
W=pathlib.Path(__file__).resolve().parent.parent
R=W/'outputs/GridSFM-loading-study'
old=pathlib.Path(r'C:\Users\Ninad\Documents\Codex\2026-10-26\don-t-wait-for-max-anything\work')
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
code=R/'experiments/loading/study.py';text=code.read_text()
text=text.replace("OLD=pathlib.Path(os.environ.get('GRIDSFM_RUNTIME_ROOT',r'C:\\Users\\Ninad\\Documents\\Codex\\2026-10-26\\don-t-wait-for-max-anything\\work'))","OLD=pathlib.Path(r'C:\\Users\\Ninad\\Documents\\Codex\\2026-10-26\\don-t-wait-for-max-anything\\work')")
text=text.replace("'--project='+str(EXP/'julia')","'--project='+str(OLD/'GridSFM-study/experiments/gsfm020/julia')")
dest=R/'experiments/executed-source';dest.mkdir(exist_ok=True);p=dest/'study.py';p.write_text(text,encoding='utf-8',newline='\n')
phase=read(R/'results/baseline-complete.json');expected=next(v for k,v in phase['code_sha256'].items() if k.replace('\\','/')=='experiments/loading/study.py');assert sha(p)==expected,(sha(p),expected)
source=old/'runtime/sources/newer';b=subprocess.check_output(['git','-C',str(source),'show','517a07531ea55a11bd81a89a6c6879695a2ba4b4:generate_finetune_dataset/topologies/pglib_opf_case500_goc.m']);assert b==(R/'sources/pglib_opf_case500_goc.m').read_bytes()
assert (R/'experiments/loading/julia/Project.toml').read_bytes()==(old/'GridSFM-study/experiments/gsfm020/julia/Project.toml').read_bytes()
assert (R/'experiments/loading/julia/Manifest.toml').read_bytes()==(old/'GridSFM-study/experiments/gsfm020/julia/Manifest.toml').read_bytes()
save(R/'manifest-addendum.json',{'date_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'frozen_manifest_sha256':sha(R/'manifest.json'),'training_exposure_file':'paper/training-exposure.json','training_exposure_sha256':sha(R/'paper/training-exposure.json'),'case500_source_exact_pinned_git_object':True,'bundled_Julia_environment_byte_identical_to_executed':True,'executed_study_py_sha256':sha(p),'executed_study_py_file':'experiments/executed-source/study.py','path_only_portability_update':'Final study.py accepts GRIDSFM_RUNTIME_ROOT and bundled Julia Project/Manifest. Original executed source retained with phase-matching hash.','hardware':{'processor':platform.processor(),'logical_cpus':os.cpu_count(),'platform':platform.platform(),'physical_core_count_and_RAM':'UNKNOWN: CIM read denied; no claim of exact model or RAM'},'paper':{'pdf':'paper/GridSFM-five-page-draft.pdf','pages':5,'all_five_pages_visually_inspected':True,'LaTeX_source_compiled':False,'conference_template_certified':False},'venue':{'user_specified':'IEEE PES, five pages, San Francisco','resolved':'2027 IEEE PES General Meeting','deadline_date':'2026-11-10','cutoff_time':'UNVERIFIED in this run','primary_source':'https://pes-gm.org/wp-content/uploads/2026/06/6.8.26-Flyer_2027-IEEE-PES-GM-CFP.pdf','direct_Dr_Li_confirmation':False},'publication_status':'Local draft and evidence only; not submitted; no external messages sent'})
files=sorted(p for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='artifact-sha256.json')
inventory={p.relative_to(R).as_posix():sha(p) for p in files};save(R/'artifact-sha256.json',inventory)
archive=W/'outputs/GridSFM-loading-study-evidence.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files+[R/'artifact-sha256.json']:z.write(p,'GridSFM-loading-study/'+p.relative_to(R).as_posix())
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,expected in inventory.items():assert hashlib.sha256(z.read('GridSFM-loading-study/'+name)).hexdigest()==expected
digest=sha(archive);(archive.with_suffix('.zip.sha256')).write_text(digest+'  '+archive.name+'\n')
save(W/'outputs/delivery-verification.json',{'status':'PASS','files_hashed':len(files),'archive_bytes':archive.stat().st_size,'archive_sha256':digest,'zip_CRC_and_all_file_SHA256_verified':True,'numerical_verification':read(R/'final-verification.json')['counts'],'paper_pages':5,'saved_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})
print(json.dumps({'status':'PASS','files':len(files),'archive_MB':round(archive.stat().st_size/1e6,2),'sha256':digest}))
