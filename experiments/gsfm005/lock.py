"""Finalize the complete hash lock before opening fresh reference generation."""
from common import *
def main():
    if (RUN/'evaluation-open.json').exists():raise RuntimeError('Evaluation already opened; no configuration changes allowed')
    p=RUN/'freeze.json';f=read(p);assert f['config_sha256']==sha(RUN/'config.json');assert f['calibration_sha256']==sha(RUN/'calibration.json');assert f['training_summary_sha256']==sha(RUN/'training-summary.json')
    f['evaluation_code_sha256']={str(s.relative_to(REPO)):sha(s) for s in (REPO/'experiments/gsfm005').iterdir() if s.is_file()};f['locked_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();f['code_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip();save(p,f);log('EVALUATION_LOCKED',freeze_sha256=sha(p))
if __name__=='__main__':main()
