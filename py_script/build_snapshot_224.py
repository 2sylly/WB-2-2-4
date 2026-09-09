"""Reproduce the experimental 2.2.4 datasets from the pinned upstream source."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
for script in ['snapshot_224.py','snapshot_224_abilities.py']:
    args=[sys.executable,str(ROOT/'py_script'/script)]
    if script=='snapshot_224.py': args.append('--write')
    subprocess.run(args,cwd=ROOT,check=True)
result=subprocess.run([sys.executable,'atree-generateID.py'],cwd=ROOT/'py_script',capture_output=True,text=True,check=True)
print(result.stdout,end='')
if 'ERROR:' in result.stdout or 'WARNING:' in result.stdout:
    raise SystemExit('Resolve tree compiler diagnostics before promoting data.')
version=ROOT/'data/2.2.4.1'
version.mkdir(exist_ok=True)
for path in (ROOT/'data/2.2.3.0').iterdir():
    shutil.copy2(path,version/path.name)
for source,target in [('atree_constants_min','atree'),('major_ids_min','majid'),('aspects_min','aspects')]:
    shutil.copy2(ROOT/'data/temp'/f'{source}.json',version/f'{target}.json')
for source,target,compressed in [('clean','items','compress'),('ingreds_clean','ingreds','ingreds_compress')]:
    data=json.loads((ROOT/'data/baseline'/f'{source}.json').read_text())
    output=json.dumps(data,ensure_ascii=False,separators=(',',':'))
    (version/f'{target}.json').write_text(output)
    (ROOT/'data/baseline/compressed'/f'{compressed}.json').write_text(output)
subprocess.run([sys.executable,str(ROOT/'py_script/snapshot_224_checklist.py')],cwd=ROOT,check=True)
print('Snapshot datasets rebuilt; historical data and encoding constants preserved.')
