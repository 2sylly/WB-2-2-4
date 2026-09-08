/* Snapshot coverage is explicit: unknown effects never silently become estimates. */
function snapshot224ManaOnHeretic(stats) {
    const maxMana = 100 + (stats.get('maxMana') || 0)
        + Math.floor(skillPointsToPercentage(stats.get('int') || 0) * 100);
    return Math.max(0, maxMana) * 0.30;
}

function updateSnapshot224Notice(stats) {
    const notice = document.getElementById('snapshot-224-notice');
    if (!notice) return;
    const isSnapshot = wynn_version_names[wynn_version_id] .startsWith('2.2.4.');
    notice.hidden = !isSnapshot;
    if (!isSnapshot) return;
    const state = atree_state_node.value;
    const selected = (atree_node.value || [])
        .filter(node => state && state.get(node.ability.id)?.active)
        .map(node => node.ability);
    const unmodeled = selected.filter(node => node.snapshot_unmodeled).map(node => node.display_name);
    document.getElementById('snapshot-224-missing').textContent = unmodeled.length
        ? 'Selected abilities with effects excluded from totals: ' + unmodeled.join(', ') + '.'
        : 'Unpublished Ritualist damage and buff values are excluded from totals.';
    const mana = document.getElementById('snapshot-224-heretic');
    const hasStrides = selected.some(node => node.display_name === 'Strides of Heresy');
    mana.hidden = !hasStrides;
    mana.textContent = hasStrides
        ? `Strides of Heresy restores ${snapshot224ManaOnHeretic(stats).toFixed(1)} mana per switch to Heretic (30% of maximum). This event is not included in the spell-cycle mana estimate.`
        : '';
}
