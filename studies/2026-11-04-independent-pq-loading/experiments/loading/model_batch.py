"""One pinned model per process; immutable unsolved inputs only."""
import os,sys,pathlib,json
from model_worker import FrozenWorker
plan=json.loads(pathlib.Path(sys.argv[1]).read_text()); release=sys.argv[2]
w=FrozenWorker(release,plan['source'],plan['checkpoint'],plan['cache'])
for folder in plan['folders']:
 d=pathlib.Path(folder)
 if (d/(release+'-metadata.json')).exists():continue
 w.run(json.loads((d/'input.json').read_text()),d)
