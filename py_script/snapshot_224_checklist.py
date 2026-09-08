"""Preserve historical tree encoding; mark free-position nodes in revision 1."""
import json,subprocess,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=json.loads(subprocess.check_output(['git','show','ddf593be:data/baseline/atree_constants.json'],cwd=ROOT))
legacy={n['display_name']:n for n in old['Shaman']}
for filename in ['data/2.2.4.1/atree.json','data/baseline/atree_constants.json']:
 p=ROOT/filename; tree=json.loads(p.read_text()); nodes={n['display_name']:n for n in tree['Shaman']}
 for node in nodes.values():
  if node.get('snapshot_provisional') or node['display_name']=='Frog Dance':
   node['snapshot_checklist']=True
   node['desc']=node['desc'].replace('Provisional snapshot connection.','Position unknown: select from the checklist.')
 shatter=nodes['Totemic Shatter']
 shatter['effects']+=copy.deepcopy(legacy['Egomania']['effects'])
 shatter['desc']+=' </br>Inherited Egomania: +10% Neutral Aura damage. The snapshot mentions a correction without a replacement coefficient; +10% remains provisional.'
 shatter['desc']=shatter['desc'].replace('The Egomania damage increase is not quantified in the snapshot notes.','')
 awake=nodes['Awakened']
 awake['effects']+=copy.deepcopy(legacy['Corporeal Manifestation']['effects'])
 awake['desc']+=' </br>Inherited Corporeal Manifestation: orbiting masks use Mask Throw damage and apply Haunting Memory within 3 blocks. Rotation DPS retains the old one Mask Throw per second model while Awakened is active; ultimate uptime and Mantra scaling remain unmodeled.'
 p.write_text(json.dumps(tree,ensure_ascii=False,indent=4 if 'baseline' in filename else None)+'\n')

p=ROOT/'docs/snapshot-2.2.4/coverage.json'
coverage=json.loads(p.read_text())
coverage['checklist_nodes']=[n['display_name'] for n in tree['Shaman'] if n.get('snapshot_checklist')]
coverage['inherited_effects']={'Totemic Shatter':'Egomania +10% Neutral Aura; corrected snapshot value unknown','Awakened':'Corporeal Manifestation: one Mask Throw per second while active; Mantra and uptime excluded'}
p.write_text(json.dumps(coverage,indent=2)+'\n')
