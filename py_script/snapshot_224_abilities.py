"""Rebuild the provisional 2.2.4 tree from the pinned upstream source.

Connections for changed Ritualist nodes are provisional. Missing coefficients
are explicitly marked and excluded from totals, never fabricated.
"""
import copy
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def source(name):
    return json.loads(subprocess.check_output(['git','show',f'ddf593be:data/baseline/{name}.json'],cwd=ROOT))

def spell_prop(spell,part,**kw):
    return dict(type='add_spell_prop',base_spell=spell,target_part=part,**kw)

def bonus(name,value,toggle=None):
    effect={'type':'raw_stat','bonuses':[{'type':'stat','name':name,'value':value}]}
    if toggle: effect['toggle']=toggle
    return effect

def main():
    tree=source('atree_constants'); majors=source('major_ids_clean'); aspects=source('aspects')
    lookup={c:{n['display_name']:n for n in nodes} for c,nodes in tree.items()}
    s=lookup['Shaman']; m=lookup['Mage']
    f=m['Freezing Sigil']; f['effects'][0]['parts'][0]['multipliers']=[40,0,0,10,0,0]
    f['desc']=f['desc'].replace('20% (of your DPS)','50% (of your DPS)').replace('Damage</span>: 15%','Damage</span>: 40%').replace('Water</span>: 5%','Water</span>: 10%')
    t=s['Twisted Tether']; t['effects'][0]['parts'][0]['multipliers']=[35,0,0,0,0,15]
    t['desc']=t['desc'].replace('Max 20','Max 10').replace('65% (of','50% (of').replace('Damage</span>: 45%','Damage</span>: 35%').replace('Air</span>: 20%','Air</span>: 15%')
    s['Bloodletting']['effects'][0]['multipliers']=[10,0,0,0,0,5]
    s['Bloodletting']['desc']='Increase Twisted Tether damage by +10% Neutral and +5% Air (15% total).'
    s['Eldritch Call']['effects'][0]['parts'][0]['multipliers']=[650,0,100,0,100,0]
    s['Eldritch Call']['desc']=s['Eldritch Call']['desc'].replace('700% (of','850% (of').replace('540%','650%').replace('80%','100%')
    s['Rupture']['effects'][0]['bonuses'][0]['value']=30
    s['Rupture']['desc']=s['Rupture']['desc'].replace('+15%','+30%')
    s['Effuse']['desc']='Flaming Tongue grants +1.2 Blood Pool per hit and deals +20% Neutral and +5% Fire damage.'
    s['Effuse']['effects']=[spell_prop(4,'Single Hit',multipliers=[20,0,0,0,5,0])]
    s['Sanguine Strike']['desc']=s['Sanguine Strike']['desc'].replace('Greatly reduce Main Attack spread. </br> ','')
    s['Flaming Tongue']['desc']=s['Flaming Tongue']['desc'].replace('Haunting Memory will no longer attach Masks to enemies. </br> ','')
    for name in ['Storm Dance','Frog Dance','Totemic Shatter',"Artist's Immersion"]:
        s[name]['cost']=1; s[name]['display']['icon']='node_1'
    s['Storm Dance']['desc']+=' </br> Applies Weathering, slowing and weakening enemies. Strength is not specified in the snapshot notes and is not calculated.'
    s['Mystic Masks']['desc']=s['Mystic Masks']['desc'].replace('(Shift + Uproot to remove it)','(Lunatic → Heretic → Fanatic; Shift + Uproot cycles backwards)')
    s['Haunting Memory']['desc']=s['Haunting Memory']['desc'].replace('If it hits an enemy, it will attach for a short time and debuff them. You will not receive the effects of your Mask until it returns.','Masks pass through enemies with an increased hitbox, applying their debuffs without attaching.')
    s["Artist's Immersion"]['properties']['lunatic_cost']=-50
    s["Artist's Immersion"]['desc']=s["Artist's Immersion"]['desc'].replace('-30%','-50%')
    frog=s['Frog Dance']
    frog['desc']='When wearing the Heretic Mask, Haul bounces once, dealing 300% total damage. Totem is not required. Snapshot notes do not specify the new elemental split; the calculator provisionally preserves the previous 3:1 Neutral/Water ratio.'
    frog['snapshot_assumptions']=['300% damage allocated 225% Neutral / 75% Water, preserving the previous split.']
    frog['effects'][0]['multipliers']=[225,0,0,75,0,0]
    frog['effects'][1]['hits']['Hop Damage']=1
    shatter=s['Totemic Shatter']
    shatter['desc']='While wearing the Fanatic Mask, Totem shatters on impact, triggering 4s of its effects without reduced healing. Aura radiates from you (merged Egomania). The Egomania damage increase is not quantified in the snapshot notes.'
    shatter['effects'][1]['bonuses'][0]['value']=900  # 4s / 0.4s = ten ticks.
    # Regeneration: ten ticks at full strength still equals 10% max health.
    # Tether shatter count is ten drains, bounded by the new activation cap.
    next(p for p in t['effects'][0]['parts'] if p['name']=='Shatter Tether per Totem')['hits']['Tether Drain Threshold']=10
    s['Tribal Chants']['desc']='Nearby allies gain mask-dependent buffs while a mask is worn. Stacks build while equipped and decay after removal. Stack strengths, caps and timings are not published; these ally buffs are excluded from totals.'
    s['Tribal Chants']['properties']={}; s['Tribal Chants']['effects']=[]
    s['Tribal Chants']['snapshot_unmodeled']=True

    # Replacement slots and paths are a provisional layout requested by the user.
    replacements={'Masquerade':'Strides of Heresy','Seeking Totem':'Transmute','Meticulous Act':'Doom',
        'Chorus of the Ancients':'Ritual Circle','Totemic Hammer':'Charged Ritual','Egomania':'Malediction',
        'Depersonalization':'Mantra','Corporeal Manifestation':'Synchrony','Awakened':'Acid Rain',
        'Sundered Skies':'Awakened'}
    specs={
        'Eye of the Storm':(2,'node_4','Lunatic Aura casts grant Surge. Nearby enemies take damage every 1.5s, increasing with Surge. Damage coefficients and the Surge cap are unpublished.', ['Mystic Masks']),
        'Strides of Heresy':(2,'node_2','Switching to the Heretic Mask restores 30% of maximum mana and grants a decaying speed burst. Speed and duration are unpublished.', ['Mystic Masks']),
        'Mantra':(2,'node_3','Unworn masks grow up to +200% stronger over time; the boost decays while worn. Timing and which bonuses scale are not fully specified.', ['Mystic Masks']),
        'Transmute':(1,'node_1','Main Attacks gain different effects for each Mask. Their details and damage are not published.', ['Mystic Masks']),
        'Charged Ritual':(2,'node_2','Eye of the Storm applies Static. Shift + Totem while wearing Lunatic detonates Static. Damage and stack limits are unpublished.', ['Eye of the Storm']),
        'Doom':(1,'node_0','Increases Eye of the Storm damage. The increase is not published.', ['Eye of the Storm']),
        'Malediction':(1,'node_1','Main Attacks consume Static to deal extra damage and have reduced spread. Damage is unpublished.', ['Eye of the Storm']),
        'Acid Rain':(2,'node_4','Totemic Shatter causes Rain Dance to apply Corroded, increasing damage taken. Additional stacks extend duration. Base strength and timing are unpublished.', ['Totemic Shatter','Rain Dance']),
        'Ritual Circle':(2,'node_3',"Spells discounted by Artist's Immersion grow a Ritual Circle: +1 radius and hit per cast. Switching masks detonates it and applies Static. Damage and base caps are unpublished.", ["Artist's Immersion"]),
        'Synchrony':(2,'node_2','Certain actions with different masks grow Ritual Circle radius and hit count. Trigger details are unpublished.', ['Ritual Circle']),
        'Overcharge':(2,'node_2','Switching from a mask above 150% Mantra instantly charges the next mask to 250% Mantra.', ['Mantra']),
        'Awakened':(2,'node_3','Ultimate: gain all Mask effects, set Mantra to 250%, and gain Corporeal Manifestation. Duration and the exact scaled effects are not fully published.', ['Mantra','Haunting Memory']),
    }
    def make_node(name,display,parents,req=0):
        cost,icon,desc,deps=specs[name]
        return dict(display_name=name,desc=desc+' </br><b>Provisional snapshot connection. Unpublished effects are excluded from calculated totals.</b>',parents=parents,dependencies=deps,blockers=[],cost=cost,archetype='Ritualist',archetype_req=req,display=dict(display,icon=icon),properties={},effects=[],snapshot_unmodeled=True,snapshot_provisional=True)
    new=[]
    for node in tree['Shaman']:
        old_name=node['display_name']
        parents=[replacements.get(p,p) for p in node['parents']]
        if old_name in replacements:
            node=make_node(replacements[old_name],node['display'],parents,15 if old_name=='Sundered Skies' else 0)
        else:
            for key in ['parents','dependencies','blockers']:
                node[key]=[replacements.get(p,p) for p in node[key]]
        new.append(node)
    tree['Shaman']=new
    s={n['display_name']:n for n in new}
    s['Frog Dance']['display'].update(row=19,col=5)
    s['Frog Dance']['parents']=['Totemic Reach']
    for name in ['Strides of Heresy','Totemic Shatter',"Artist's Immersion"]:
        s[name]['parents']=['Eye of the Storm']
    new.append(make_node('Eye of the Storm',dict(row=20,col=4),['Haunting Memory','Cheaper Uproot I']))
    s['Strides of Heresy']['parents'].append('Lashing Lance')
    s['Doom']['parents']=['Mantra']; s['Doom']['dependencies']=['Eye of the Storm']
    new.append(make_node('Overcharge',dict(row=43,col=4),['Synchrony']))
    s['Awakened']['parents']=['Overcharge']; s['Awakened']['archetype_req']=15
    # Ritual Circle requires Mantra's branch, but Frog Dance remains optional.
    s['Ritual Circle']['parents']=['Mantra','Invigorating Wave']
    s['Mantra']['parents']=['Tribal Chants','Imbued Totem']
    s['Synchrony']['parents']=['Pool of Rejuvenation']
    new.append(dict(display_name='Greater Sacrifice',desc='Sacrificial Shrine siphons +1% of your health every 0.4s and boosts Aura damage by +20%. Blocks Double Totem. AP cost is provisionally 1.',parents=['Bloodier'],dependencies=['Sacrificial Shrine'],blockers=['Double Totem'],cost=1,archetype='Acolyte',display=dict(row=35,col=8,icon='node_0'),properties={},effects=[bonus('damMult.BloodPool:3.Single Wave',20,'Activate Boosted Aura')],snapshot_provisional=True))
    s['Double Totem']['blockers'].append('Greater Sacrifice')
    # Major IDs: only published, calculable changes.
    majors['WAVEBREAK']['abilities'][0]['effects']=[e for e in majors['WAVEBREAK']['abilities'][0]['effects'] if not(e.get('target_part')=='Meteor Damage' and e.get('type')=='add_spell_prop')]
    majors['WAVEBREAK']['description']=majors['WAVEBREAK']['description'].split('\n',1)[1]
    majors['DIVINE_RIGHT']['description']=majors['DIVINE_RIGHT']['description'].replace('3%','2%')
    majors['DIVINE_RIGHT']['abilities'][0]['effects'][0]['scaling']=[0.015,0.015]
    majors['FISSURE']['abilities'][0]['effects'][0]['multipliers']=[350,0,0,200,0,0]
    majors['FISSURE']['description']=majors['FISSURE']['description'].replace('275%','350%').replace('155%','200%')
    majors['GENTLE_GLOW']['abilities'][0]['properties']['rate']=0.4-(1/1.5)
    majors['GENTLE_GLOW']['description']="Orphion's Pulse restores 10% more max health per pulse, with a 2.5s interval."
    majors['OLD_SPARK']['abilities']=[{'class':'Warrior','base_abil':'Uppercut','effects':[spell_prop(3,'Uppercut',multipliers=[0,0,40,0,0,0])]}]
    majors['OLD_SPARK']['description']+=' Projectile travel speed increased by about 50%; Uppercut gains +40% Thunder damage.'
    majors['FOREST_BLESSING']['abilities'][0]['dependencies']=['Call of the Hound']
    majors['SLOW_BOIL']['description']=majors['SLOW_BOIL']['description'].replace('20%','40%')
    majors['SLOW_BOIL']['abilities']=[{'class':'Warrior','base_abil':"Bak'al's Grasp",'dependencies':["Bak'al's Grasp"],'effects':[{'type':'stat_scaling','slider':True,'slider_name':'Corrupted','behavior':'overwrite','scaling':[2],'max':240,'output':{'type':'stat','name':'damRaw'}}]}, {'class':'Warrior','base_abil':"Bak'al's Grasp",'dependencies':['Enraged Blow'],'properties':{'max_damage_bonus':55},'effects':[]}]
    majors['SOLAR_WIND']['description']="Thunderstorm disables Meteor and casts +2 thunderbolts with the previous total damage, adds +2 Mana Bank per hit, and gains +300% damage from Unstable."
    wind=majors['SOLAR_WIND']['abilities'][0]['effects']
    next(e for e in wind if e.get('target_part')=='Lightning Damage')['multipliers']=[400/3,0,440/3,0,0,0]
    next(e for e in wind if e.get('target_part')=='Total Damage')['hits']['Lightning Damage']=2
    wind.append({'type':'add_spell_prop','base_spell':3,'mana_gained':22})  # Three hits × (8+2) mana, minus base 8.
    majors['SOLAR_WIND']['abilities'][1]['effects'][0]['bonuses'][0]['value']=300
    majors['JUGGLE']['description']='Mutilate adds 12 hits. Each hit loses 8% Neutral and 2% Water damage. Finality damage scaling is halved.'
    majors['JUGGLE']['abilities'][0]['effects'][0]['multipliers']=[-8,0,0,-2,0,0]
    for abil in majors['JUGGLE']['abilities']:
        for effect in abil['effects']:
            if effect.get('target_part')=='Finality Bonus':
                effect['multipliers']=[v/2 for v in effect['multipliers']]
    majors['JUGGLE']['abilities'].append({'class':'Assassin','base_abil':'Multihit','dependencies':['Finality'],'effects':[bonus('damMult.Juggle:3.Finality Bonus',-50)]})
    # Keep original extra-hit compensation at full size; a single multiplier
    # halves the entire Finality contribution, including other aspect bonuses.
    for abil in majors['JUGGLE']['abilities']:
        for effect in abil['effects']:
            if effect.get('target_part')=='Finality Bonus': effect['multipliers']=[v*2 for v in effect['multipliers']]
    majors['CINDERCURSE']['description']='Burning Sigil and Flaming Uppercut deal 7x damage. Meteor, Ophanim and Uppercut deal 60% less damage.'
    majors['CINDERCURSE']['abilities']=[
        {'class':'Mage','base_abil':'Meteor','effects':[bonus('damMult.Cindercurse:3.Meteor Damage',-60),bonus('damMult.Cindercurse:3.Per Orb',-60),bonus('damMult.Cindercurse:6.Tick Damage',600)]},
        {'class':'Warrior','base_abil':'Uppercut','effects':[bonus('damMult.Cindercurse:3.Uppercut',-60),bonus('damMult.Cindercurse:8.Damage Tick',600)]}]
    majors['HAWKEYE']['description']+=' Feedback Loop maximum extra arrows is reduced by 90%.'
    # Upstream currently exposes only Feedback Loop steady firing DPS, not its
    # finite-arrow capacity. Preserve that model and disclose the cap in text.
    majors['WORMHOLE']['description']+=' Does not affect Mirage clones.'
    for key in ['BRAChIATE','BRACHIATE']:
        if key in majors: majors[key]['description']=majors[key]['description'].replace('25%','50%')
    majors['ALTEREGO']['description']='Mantra boosts unworn masks 150% faster, but worn boosts decay 100% faster.'
    majors['ALTEREGO']['abilities']=[]
    majors['FIND_THYSELF']['description']='With Mystic Masks unlocked, switching between Masks three times restores 25 mana.'
    majors['FIND_THYSELF']['abilities']=[]  # Event interval cannot be inferred from a spell cycle.
    majors['FAUSTIAN_GAMBIT']['description']='Frog Dance bounces instantly, retains increased knockback, and deals +400% Thunder damage.'
    majors['SUBLIMATION']['description']="Totemic Shatter heals 150% of Regeneration's usual amount, at the cost of 2 blocks of radius."
    majors['SUBLIMATION']['abilities'][0]['effects'][0]['power']=0.05
    majors['STARCROSSED']['description']='Haunting Memory links up to 8 enemies. Linked enemies take 50% more Malediction damage and share it with nearby linked enemies.'
    majors['STARCROSSED']['abilities']=[]

    # Aspect IDs remain unchanged so saved aspect slots keep their identity.
    asp={a['displayName']:a for a in aspects['Shaman']}
    def replace_aspect(old,new,descriptions):
        a=asp[old]; a['displayName']=new
        a.setdefault('aliases',[]).append(old)
        for tier,description in zip(a['tiers'],descriptions):
            tier['description']=description; tier['abilities']=[]
    replace_aspect('Aspect of the Blurred Line','Aspect of Bile Waters',[f'Corroded is +{v}% stronger. Base Corroded strength is unpublished and excluded from totals.' for v in [0.5,1,1.5,2]])
    replace_aspect('Aspect of Summer Storms','Aspect of Damnation',['Increases Malediction damage. Tier coefficient is unpublished and excluded from totals.']*4)
    replace_aspect('Aspect of the Channeler','Aspect of the Channeler',[f'Tribal Chants applies stacks {v}s faster.' for v in [0.1,0.15,0.2]])
    replace_aspect('Aspect of the Amphibian','Aspect of the Amphibian',[f'Frog Dance gains +{v}% velocity.' for v in [20,30,40]])
    replace_aspect('Aspect of Seismic Sense','Aspect of the Eternal Dance',[f'Ritual Circle maximum hits and radius increase by +{v}.' for v in [1,2,3]])
    replace_aspect("Ritualist's Embodiment of the Ancestral Avatar","Ritualist's Embodiment of the Ancestral Avatar",['Eye of the Storm strikes 0.5s faster.','Eye of the Storm strikes 0.5s faster; maximum Surge increases by 1.','Eye of the Storm strikes 0.5s faster; maximum Surge increases by 1; Ritual Circle deals +10% damage.'])
    harmony=asp["Shaman's Embodiment of Serene Harmony"]
    for tier in harmony['tiers'][1:]:
        tier['description']=tier['description'].replace("Sundered Skies' delay between lightning strikes is -0.3s shorter.",'Awakened lasts 5s longer.')
        tier['abilities']=[]
    for tier in asp['Aspect of Stances']['tiers']:
        tier['abilities']=[a for a in tier['abilities'] if 'Meticulous Act' not in a.get('dependencies',[])]
    majors['BLINDING_LIGHTS']['description']+=' Individual orb damage cooldown is increased by 60%. Collision-dependent DPS is not modeled.'
    # Any remaining obsolete references must fail validation, never be silently
    # redirected into a different new ability with unrelated effects.
    removed=set(replacements)-{'Awakened'}
    for c,nodes in tree.items():
        names={n['display_name'] for n in nodes}
        for n in nodes:
            for key in ['parents','dependencies','blockers']:
                assert all(ref in names for ref in n.get(key,[])),(n['display_name'],key)
    for filename,data in [('atree_constants',tree),('major_ids_clean',majors),('aspects',aspects)]:
        (ROOT/'data/baseline'/f'{filename}.json').write_text(json.dumps(data,ensure_ascii=False,indent=4 if filename in ['atree_constants','major_ids_clean'] else 2)+'\n')
    provisional=[n['display_name'] for n in tree['Shaman'] if n.get('snapshot_provisional')]
    unmodeled=[n['display_name'] for n in tree['Shaman'] if n.get('snapshot_unmodeled')]
    (ROOT/'docs/snapshot-2.2.4/coverage.json').write_text(json.dumps({'source':'https://wynncraft.com/news/blog/581','beta_api_has_mantra':False,'provisional_nodes':provisional,'unmodeled_abilities':unmodeled,'omitted':['New mythic ascensions (user requested omission)','New items and ingredients without published stats'],'assumptions':['Frog Dance 300% preserves the previous 3:1 elemental split.','Greater Sacrifice costs 1 AP.','Awakened replaces Sundered Skies; Corporeal Manifestation is merged into it.','Depersonalization is replaced by Mantra because Masquerade was removed.']},indent=2)+'\n')
    print(f'Updated tree: {len(tree["Shaman"])} Shaman nodes; {len(provisional)} provisional nodes; {len(unmodeled)} abilities with unpublished effects.')

if __name__=='__main__': main()
