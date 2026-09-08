"""Screenshot-sourced ascensions supplied by the user on 2026-09-08."""
import copy
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/baseline/clean.json'
data=json.loads(p.read_text())
# IDs are reserved locally for this experimental dataset, not official API IDs.
specs=[('Divzer',5429,dict(lvl=110,nDam='26-27',tDam='215-215',ls=1087,ms=24,sdRaw=302,spd=23)),
       ('Sunstar',5430,dict(lvl=109,nDam='295-385',tDam='850-1055',ls=825,tDamPct=25,mdPct=11)),
       ('Warp',5431,dict(lvl=111,nDam='40-65',aDam='140-160',mr=-35,aDamPct=23,spRaw2=-375,majorIds=['VORTEX'],
           snapshotRolls={'mr':[-46,-25],'spRaw2':[-113,-488]}))]
for name,item_id,changes in specs:
    item=copy.deepcopy(next(i for i in data['items'] if i['name']==name))
    assert not any(i['id']==item_id or i['name']=='Masterwork '+name for i in data['items'])
    item.update(changes)
    item.update(id=item_id,name='Masterwork '+name,displayName='Masterwork '+name)
    item['lore']+=' Snapshot preview: visible stats transcribed from user screenshots. Powder slots are inherited from the base weapon and unverified.'
    speed={'SUPER_FAST':4.3,'VERY_SLOW':0.83,'VERY_FAST':3.1}[item['atkSpd']]
    item['averageDps']=round(sum(sum(map(int,item.get(e+'Dam','0-0').split('-')))/2 for e in 'netwfa')*speed)
    data['items'].append(item)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
p=ROOT/'data/baseline/major_ids_clean.json'
majors=json.loads(p.read_text())
majors['VORTEX']={'displayName':'Vortex','description':'Teleport pulls nearby enemies to you and blasts them away, dealing [neutral]200% and [air]20% area damage.',
    'abilities':[{'class':'Mage','base_abil':'Teleport','dependencies':['Teleport'],'effects':[
        {'type':'add_spell_prop','base_spell':2,'target_part':'Vortex','behavior':'merge','multipliers':[200,0,0,0,0,20]},
        {'type':'add_spell_prop','base_spell':2,'target_part':'Single Teleport','hits':{'Vortex':1},'display':'Total Damage'}]}]}
p.write_text(json.dumps(majors,ensure_ascii=False,indent=4)+'\n')
print('Added screenshot ascensions: Masterwork Divzer, Sunstar, Warp; Vortex.')
