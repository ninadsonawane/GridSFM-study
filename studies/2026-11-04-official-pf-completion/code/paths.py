import os, pathlib, sys
os.environ.update(PYTHONDONTWRITEBYTECODE='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='4', MKL_NUM_THREADS='1')
ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
PRIOR = pathlib.Path(os.environ.get('GRIDSFM_PRIOR_EVIDENCE_ROOT', r'C:\Users\Ninad\Documents\Codex\2026-11-03\follow-this-order-start-the-paper\outputs\GridSFM-loading-study'))
SOURCE = pathlib.Path(os.environ.get('GRIDSFM_OFFICIAL_SOURCE_ROOT', str(REPO/'work/official-v2-517a075')))
RUNTIME = REPO.parent/'runtime'
os.environ['XDG_CACHE_HOME'] = str(REPO.parent/'pf-cache')
sys.path[:0] = [str(PRIOR/'experiments/loading'), str(PRIOR/'scripts/python'), str(SOURCE/'model'), str(SOURCE/'finetune_model/src')]
