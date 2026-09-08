# 2.2.4 snapshot coverage

Source: [official 2.2.4 changelog](https://wynncraft.com/news/blog/581), published September 7, 2026. Upstream base: `ddf593be` from `wynnbuilder/wynnbuilder.github.io`.

This is an experimental snapshot fork, not a claim of complete game parity. The live and `beta-api.wynncraft.com/v3/ability/tree/shaman` endpoints still returned the previous Ritualist tree when checked on September 8. The user requested provisional tree connections and later supplied screenshots for three ascensions.

## Included

- 461 item/ingredient stat edits from the published before/after values, plus the Synch Core set bonuses, Ritual Catalyst's full rework, Psionic Quill's tailoring eligibility, and the Ionic Spark display-name change.
- Freezing Sigil, Twisted Tether, Bloodletting, Eldritch Call, Rupture, Effuse, the documented one-bounce Frog Dance, Artist's Immersion's 50% Lunatic discount, and four-second Totemic Shatter.
- The new Ritualist nodes, revised AP costs, removal/replacement of obsolete nodes, Greater Sacrifice and its Double Totem exclusion, and the revised aspect names/descriptions. Old aspect IDs are preserved.
- Calculable changes to Wavebreak, Divine Right, Fissure, Gentle Glow, Old Spark, Forest's Blessing, Slow Boil, Solar Wind, Juggle, Cindercurse, Faustian Gambit, and Sublimation.
- A separate Strides of Heresy readout: 30% of the final maximum mana when the ability is selected. It does not assume every spell-cycle Uproot switches to Heretic.
- Historical datasets are unchanged. New builds use version index 34 (`2.2.4.0`). Existing item and aspect IDs, level 121 and seven powder tiers are retained. Share snapshot links from this fork: an official-site link may interpret the experimental version differently.

## Provisional or not calculated

The visible builder notice and node tooltips identify these limits. `coverage.json` contains the machine-readable node list.

- Ritualist connections, replacement positions and archetype requirements are provisional. Greater Sacrifice is provisionally one AP.
- Awakened replaces Sundered Skies and absorbs Corporeal Manifestation. Depersonalization is replaced by Mantra because its old Masquerade effect no longer applies. These structural choices are inferred.
- Frog Dance's published total is 300%; its 225% Neutral / 75% Water split preserves the old 3:1 ratio and is **not confirmed**.
- Eye of the Storm, Mantra scaling, Transmute, Charged Ritual, Doom, Malediction, Acid Rain, Ritual Circle, Synchrony, Overcharge, Awakened and the new Tribal Chants have missing coefficients, caps or timing details. Their unspecified damage/buffs are **excluded from totals**, not estimated. New aspects targeting them have updated descriptions but cannot yet contribute numerical effects. Strides' speed burst is also unmodeled.
- Weathering's strength and the corrected merged Egomania Aura bonus are not published. Greater Sacrifice's extra drain is described but is not yet included in the automatic Twisted Tether drain estimate. The new Tether activation cap is documented; arbitrary external health-drain events are not simulated.
- Find Thyself, Alter Ego and Starcrossed have updated descriptions; event-based mana, Mantra timing and linked-target damage are not simulated. Hawkeye's Feedback Loop capacity reduction and Blinding Lights' collision-dependent cooldown are described but are outside upstream's steady-DPS model.
- Solar Wind assumes three lightning hits on one target: unchanged 840% total conversion and 30 Mana Bank gain. It does not model misses or multi-target hits.
- Masterwork Divzer, Sunstar and Warp are included from user screenshots. Other ascensions remain omitted. Other new items/ingredients, Dreamer's Soul's unnamed new major ID, unpublished lore, the Ornate Shadow set correction and unquantified fixes await authoritative data.

## Source discrepancies resolved

Current display names take precedence over internal historical names. This distinguishes Cancer from Necrosis and the Tectonics wand from the Tremor chestplate. Spelling aliases resolve Kaas' Fur, Quick Claw, Exquisite Marsh Scale, Cerulean Rectrix and Urdar's Stone.

Three before-values differ from upstream: Last Stand health (6550 vs the notes' 6250), Wilted Orchard health regen (-70 vs -91), and Cerulean Rectrix air damage (8–11 vs 9–13). The published after-values are applied explicitly. Space Dust's raw elemental damage, Tattered Magic Cloth's fire spell damage and Dernic Hydroid's raw water spell damage retain their existing ID types where the changelog label is inconsistent. These decisions are explicit in the importer.

## Rebuild and verify

```sh
python3 py_script/build_snapshot_224.py
node tests/snapshot_224.cjs
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/builder/`. No Node packages or Python dependencies are needed for this snapshot pipeline. It rebuilds from the pinned upstream commit and the checked-in numeric change notes. Generated baseline and versioned data must be committed together.

Validation performed: upstream graph geometry/reference checks; real ability merging and spell collection in Node; representative damage/mana changes; item identity and crafting range regression checks; all-class tree reachability; historical/new header and level round trips; dataset parity and script load order. Visual browser validation was blocked by the browser's admin-policy verification error.

## Screenshot ascensions (September 8)

Added Masterwork Divzer (level 110), Masterwork Sunstar (109), and Masterwork Warp (111) as separate items. The original weapons and their IDs are unchanged. Fork-local IDs 5429–5431 fit the existing 13-bit encoding. These IDs and the Masterwork naming follow this fork’s conventions; they are not verified API identities. Powder slots, icons, and lore are inherited because the screenshots do not reveal all item pages.

Vortex adds 200% Neutral + 20% Air to each Teleport; displacement is not simulated. Warp's screenshot endpoints for mana regeneration (-46 to -25) and Teleport cost (-113 to -488) are preserved explicitly because upstream rounding of the inferred base values differs by one. Other visible rolls use the existing expansion rules.

Source: three user-supplied item-guide screenshots showing ordinary and ascended Divzer, Sunstar, and Warp. The preview site's hostname is obscured, so these are provisional user-provided data, not independently verified API data.
