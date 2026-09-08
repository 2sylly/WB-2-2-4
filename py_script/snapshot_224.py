"""Apply the published 2.2.4 item/ingredient patch; no live API dependency.

Run from any directory. Defaults to a dry run; --write updates baseline data.
Every nonzero before-value is checked, including fixed-ID wrappers.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / 'docs/snapshot-2.2.4/changelog.md'

def norm(s):
    return s.replace('’', "'").strip().lower()

STATS = {
    'max mana': 'maxMana', 'health': 'hp', 'health bonus': 'hpBonus',
    'health regeneration': 'hprPct', 'health regen': 'hprPct',
    'raw health regeneration': 'hprRaw', 'raw health regen': 'hprRaw', 'health regen raw': 'hprRaw',
    'mana regeneration': 'mr', 'mana regen': 'mr', 'mana steal': 'ms', 'life steal': 'ls',
    'damage bonus': 'damPct', 'damage': 'damPct', 'raw damage bonus': 'damRaw',
    'spell damage bonus': 'sdPct', 'spell damage': 'sdPct', 'spell damage raw': 'sdRaw',
    'main attack damage bonus': 'mdPct', 'main attack damage': 'mdPct', 'raw main attack damage bonus': 'mdRaw',
    'attack speed bonus': 'atkTier', 'walk speed': 'spd', 'walk speed bonus': 'spd',
    'main attack range': 'mainAttackRange', 'jump height': 'jh', 'slow enemy': 'slowEnemy',
    'healing efficiency': 'healPct', 'sprint': 'sprint', 'sprint regeneration': 'sprintReg', 'sprint regen': 'sprintReg',
    'xp bonus': 'xpb', 'combat experience': 'xpb', 'exploding': 'expd', 'thorns': 'thorns', 'reflection': 'ref',
    'elemental defense': 'rDefPct', 'elemental defense bonus': 'rDefPct',
    'elemental damage bonus': 'rDamPct', 'all damage bonuses': 'damPct',
    'spell elemental damage bonus': 'rSdPct', 'elemental spell damage bonus': 'rSdPct',
    'raw spell elemental damage bonus': 'rSdRaw', 'spell elemental damage bonus raw': 'rSdRaw',
    'raw elemental spell damage bonus': 'rSdRaw', 'elemental main attack damage bonus': 'rMdPct',
    'durability': 'dura',
}
for label, stat in [('strength','str'),('dexterity','dex'),('intelligence','int'),('defense','def'),('defence','def'),('agility','agi')]:
    for suffix in ['points', 'bonus']:
        STATS[f'{label} {suffix}'] = stat
    STATS[f'{label} requirement'] = stat+'Req'
for label, stat in [('neutral','n'),('earth','e'),('thunder','t'),('water','w'),('fire','f'),('air','a')]:
    STATS.update({f'{label} damage':stat+'Dam', f'{label} damage bonus':stat+'DamPct',
        f'{label} defense':stat+'Def', f'{label} defense bonus':stat+'DefPct',
        f'{label} spell damage bonus':stat+'SdPct', f'spell {label} damage bonus':stat+'SdPct',
        f'{label} main attack damage bonus':stat+'MdPct', f'main attack {label} damage bonus':stat+'MdPct',
        f'raw {label} spell damage bonus':stat+'SdRaw', f'{label} spell damage raw':stat+'SdRaw',
        f'raw main attack {label} damage bonus':stat+'MdRaw', f'{label} damage raw':stat+'DamRaw'})
STATS['thunder damamge bonus'] = 'tDamPct'  # Literal typo in the published notes.
STATS['earth spell damage'] = 'eSdRaw'  # Heart of the Forest: raw 192 -> 165.

# Explicit disambiguation against the existing item's before-value. These notes
# call an existing elemental damage ID "spell"; do not add a second damage ID.
OVERRIDES = {('space dust','spell elemental damage bonus raw'):'rDamRaw', ('tattered magic cloth','fire damage bonus'):'fSdPct', ('dernic hydroid','water damage raw'):'wSdRaw'}

def values(text, kind):
    text = re.sub(r'(?<=\d)-(?=\d)', ' to ', text)
    nums = [int(x) for x in re.findall(r'[+-]?\d+', text)]
    if kind == 'range':
        # Damage ranges use a hyphen separator, not a negative upper bound.
        return '-'.join(str(abs(x)) for x in nums)
    if kind == 'ingredient':
        return {'minimum':nums[0], 'maximum':nums[-1]}
    if len(nums) != 1:
        raise ValueError(text)
    return nums[0]

def build_patch():
    text = NOTES.read_text().replace('-7Dexterity Bonus:', '-7\n- Dexterity Bonus:')
    source = json.loads(subprocess.check_output(['git','show','ddf593be:data/baseline/clean.json'],cwd=ROOT))
    ingreds = json.loads(subprocess.check_output(['git','show','ddf593be:data/baseline/ingreds_clean.json'],cwd=ROOT))
    items_by_name = {norm(i.get('displayName',i['name'])):i for i in source['items']}
    ings_by_name = {norm(i['name']):i for i in ingreds}
    aliases = {"kaas' furr":"kaas' fur", 'quickclaw':'quick claw', 'marsh scale':'exquisite marsh scale', 'cerulean retrix':'cerulean rectrix', 'urdar stone':"urdar's stone"}
    patches, issues = [], []
    current = []
    ingredient_section = False
    for line in text.splitlines():
        line = line.strip()
        if 'Ingredient Changes' in line and line.startswith('#'):
            ingredient_section = True
        if line.startswith('#'):
            current = []
        header = re.match(r'(?:Rebalanced )?(.+?)\s*[\[(](?:Mythic|Fabled|Legendary|Rare|Unique|Tier|T3)', line, re.I)
        if header and not line.startswith(('**','Renamed ')):
            name = norm(header[1])
            name = aliases.get(name,name)
            if name == 'infused hive bow/spear/wand/dagger/relik':
                current = [('item',items_by_name['infused hive '+k]) for k in ['bow','spear','wand','dagger','relik']]
            elif name in items_by_name:
                current = [('item',items_by_name[name])]
            elif name in ings_by_name:
                current = [('ingredient',ings_by_name[name])]
            else:
                issues.append('Unknown name: '+header[1]); current = []
        if ingredient_section and norm(line.rstrip(':')) in ings_by_name:
            current = [('ingredient',ings_by_name[norm(line.rstrip(':'))])]
        if line.startswith(('Rebalanced the ', 'Renamed ', 'Added ')):
            current = []
        if not current or not line.startswith('- ') or '->' not in line:
            continue
        change = re.match(r'- (.+?):\s*([+-]?\d.*?)\s*->\s*(.*)', line)
        if not change:
            change = re.match(r'- (.+? spell cost)\s+([+-]?\d.*?)\s*->\s*(.*)', line,re.I)
        if not change:
            issues.append('Cannot parse: '+line); continue
        label, before, after = change.groups()
        label = norm(label)
        for typ,obj in current:
            if re.match(r'(?:raw )?[1-4](?:st|nd|rd|th) spell cost',label):
                n = re.search(r'[1-4]',label)[0]
                stat = 'sp'+('Pct' if '%' in before or '%' in after else 'Raw')+n
            else:
                stat = OVERRIDES.get((norm(obj['name']),label), STATS.get(label))
            if typ == 'ingredient' and label == 'all damage bonuses':
                for element in 'etwfa':
                    field=element+'DamPct'
                    old,new=values(before,'ingredient'),values(after,'ingredient')
                    actual=obj['ids'].get(field)
                    if actual not in (old,new):
                        issues.append(f"Mismatch: {obj['name']} {field}: {actual}")
                    else:
                        patches.append({'kind':typ,'name':obj['name'],'path':['ids',field],'before':actual,'after':new})
                continue
            if stat is None:
                issues.append(f'Unknown stat: {obj["name"]}: {label}'); continue
            path = [stat]
            kind = 'range' if stat in ['nDam','eDam','tDam','wDam','fDam','aDam'] else 'item'
            if typ == 'ingredient':
                if stat.endswith('Req') or stat == 'dura':
                    path = ['itemIDs',stat]
                else:
                    path = ['ids',stat]; kind = 'ingredient'
            old,new = values(before,kind),values(after,kind)
            target = obj
            for p in path[:-1]: target = target[p]
            actual = target.get(stat, {'minimum':0,'maximum':0} if kind=='ingredient' else 0)
            raw = actual.get('raw') if isinstance(actual,dict) and 'raw' in actual else actual
            accepted_old = {('Last Stand','hp'):6550, ('Wilted Orchard','hprPct'):-70, ('Cerulean Rectrix','aDamPct'):{'minimum':8,'maximum':11}}
            if raw != old and raw != new and raw != accepted_old.get((obj['name'],stat), object()):
                issues.append(f'Mismatch: {obj["name"]} {stat}: existing={actual}, notes={old} -> {new}')
                continue
            if isinstance(actual,dict) and 'raw' in actual:
                new = dict(actual,raw=new)
            record = {'kind':typ,'name':obj['name'],'path':path,'before':actual,'after':new}
            if record not in patches: patches.append(record)
    return source,ingreds,patches,issues

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    source,ingreds,patches,issues=build_patch()
    print(f'{len(patches)} verified changes; {len(issues)} discrepancies')
    for issue in issues: print(issue)
    if args.write:
        if issues: raise SystemExit('Resolve discrepancies before writing.')
        objs={'item':{i['name']:i for i in source['items']},'ingredient':{i['name']:i for i in ingreds}}
        for p in patches:
            target=objs[p['kind']][p['name']]
            for key in p['path'][:-1]: target=target[key]
            target[p['path'][-1]]=p['after']
        # Ritual Catalyst is a full rework, including removal of its old IDs.
        rc=objs['ingredient']['Ritual Catalyst']
        rc['ids']={k:{'minimum':v,'maximum':v} for k,v in {'ms':8,'sdPct':6,'ls':-100,'mdPct':-12}.items()}
        if 'TAILORING' not in objs['ingredient']['Psionic Quill']['skills']:
            objs['ingredient']['Psionic Quill']['skills'].append('TAILORING')
        volatility=objs['item'].get('Volatility')
        if volatility:
            volatility['displayName']='Ionic Spark'
        # Published set bonuses are final values, not rolled item IDs.
        bonuses=source['sets']['Synch Core']['bonuses']
        stats={'hpBonus':[0,0,-1200,1200], 'damPct':[0,-8,20,-10], 'spd':[0,0,20,-10], 'jh':[0,0,0,0], 'sprint':[0,0,0,0], 'hprRaw':[0,-100,195,300], 'mr':[0,0,-6,-6], 'ms':[0,0,-6,-6]}
        for element in 'etwfa': stats[element+'DefPct']=[0,-25,-40,50]
        for i,bonus in enumerate(bonuses):
            bonus.pop('sdPct',None); bonus.pop('mdPct',None)
            for key,vals in stats.items(): bonus[key]=vals[i]
        # Recompute the search-only DPS summary for changed weapon ranges.
        speed={'SUPER_SLOW':0.51,'VERY_SLOW':0.83,'SLOW':1.5,'NORMAL':2.05,'FAST':2.5,'VERY_FAST':3.1,'SUPER_FAST':4.3}
        changed={p['name'] for p in patches if p['path'][-1] in [e+'Dam' for e in 'netwfa']}
        for item in source['items']:
            if item['name'] in changed:
                item['averageDps']=round(sum(sum(map(int,item.get(e+'Dam','0-0').split('-')))/2 for e in 'netwfa')*speed[item['atkSpd']])
        for filename,data in [('clean.json',source),('ingreds_clean.json',ingreds)]:
            (ROOT/'data/baseline'/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        (ROOT/'docs/snapshot-2.2.4/applied-item-patch.json').write_text(json.dumps(patches,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__': main()
