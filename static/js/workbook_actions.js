/**
 * Master Cashbook workbook actions — Update / Clear / Rerun
 * Requires wbJobId (and wbSubsidiaryId for per-region actions).
 */

function wbFormatResultMessage(result, action) {
    if (!result) return action + ' completed.';
    const region = result.region || '';
    if (action === 'update') {
        let msg = `Updated ${region}: ${result.rows_in_region_tab ?? 0} row(s) in ${region} Stripe Import.`;
        if (result.rows_removed) msg += ` ${result.rows_removed} removed from tab.`;
        msg += ` ${result.to_be_uploaded_remaining ?? '—'} remaining in To be Uploaded.`;
        if (result.unresolved) msg += ` Warning: ${result.unresolved} match(es) could not be linked to master.`;
        return msg;
    }
    if (action === 'clear') {
        return `Cleared ${region} tab: ${result.rows_cleared ?? 0} row(s) moved to To be Uploaded. Matches unchanged.`;
    }
    if (action === 'rerun') {
        return `Rerun ${region}: cleared ${result.rows_cleared ?? 0} row(s), deleted ${result.matches_deleted ?? 0} match(es). Redirecting to reconciliation…`;
    }
    if (action === 'update_all') {
        const n = result.regions_updated ?? 0;
        return `Updated ${n} region(s). ${result.to_be_uploaded_remaining ?? '—'} row(s) in To be Uploaded.`;
    }
    return action + ' completed.';
}

async function workbookUpdate(jobId, subsidiaryId, btn) {
    if (btn) { btn.disabled = true; btn.dataset.wbOrig = btn.innerHTML; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating…'; }
    try {
        const res = await fetch(`/api/master-cashbook/${jobId}/update-from-stripe/${subsidiaryId}`, { method: 'POST' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Update failed');
        alert(wbFormatResultMessage(data.result, 'update'));
        if (typeof window.onWorkbookActionComplete === 'function') window.onWorkbookActionComplete(data);
        return data;
    } catch (e) {
        alert('Update Cashbook failed: ' + e.message);
        throw e;
    } finally {
        if (btn && btn.dataset.wbOrig) { btn.disabled = false; btn.innerHTML = btn.dataset.wbOrig; }
    }
}

async function workbookUpdateAll(jobId, btn) {
    if (btn) { btn.disabled = true; btn.dataset.wbOrig = btn.innerHTML; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating all…'; }
    try {
        const res = await fetch(`/api/master-cashbook/${jobId}/update-from-stripe/all`, { method: 'POST' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Update all failed');
        alert(wbFormatResultMessage(data.result, 'update_all'));
        if (typeof window.onWorkbookActionComplete === 'function') window.onWorkbookActionComplete(data);
        return data;
    } catch (e) {
        alert('Update all failed: ' + e.message);
        throw e;
    } finally {
        if (btn && btn.dataset.wbOrig) { btn.disabled = false; btn.innerHTML = btn.dataset.wbOrig; }
    }
}

async function workbookClear(jobId, subsidiaryId, regionLabel, btn) {
    if (!confirm(`Clear ${regionLabel} Stripe Import tab?\n\nRows will move back to To be Uploaded. Stripe matches are NOT deleted.`)) return;
    if (btn) { btn.disabled = true; btn.dataset.wbOrig = btn.innerHTML; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Clearing…'; }
    try {
        const res = await fetch(`/api/master-cashbook/${jobId}/workbook-clear/${subsidiaryId}`, { method: 'DELETE' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Clear failed');
        alert(wbFormatResultMessage(data.result, 'clear'));
        if (typeof window.onWorkbookActionComplete === 'function') window.onWorkbookActionComplete(data);
        return data;
    } catch (e) {
        alert('Clear tab failed: ' + e.message);
        throw e;
    } finally {
        if (btn && btn.dataset.wbOrig) { btn.disabled = false; btn.innerHTML = btn.dataset.wbOrig; }
    }
}

async function workbookRerun(jobId, subsidiaryId, regionLabel, btn) {
    if (!confirm(`Rerun ${regionLabel}?\n\nThis will:\n• Clear the ${regionLabel} Stripe Import tab\n• Delete ALL matches for ${regionLabel}\n\nYou will need to re-run matching.`)) return;
    if (btn) { btn.disabled = true; btn.dataset.wbOrig = btn.innerHTML; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Rerunning…'; }
    try {
        const res = await fetch(`/api/master-cashbook/${jobId}/workbook-rerun/${subsidiaryId}`, { method: 'POST' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Rerun failed');
        alert(wbFormatResultMessage(data.result, 'rerun'));
        if (data.result && data.result.redirect_url) {
            window.location.href = data.result.redirect_url;
        } else if (typeof window.onWorkbookActionComplete === 'function') {
            window.onWorkbookActionComplete(data);
        }
        return data;
    } catch (e) {
        alert('Rerun failed: ' + e.message);
        throw e;
    } finally {
        if (btn && btn.dataset.wbOrig) { btn.disabled = false; btn.innerHTML = btn.dataset.wbOrig; }
    }
}
