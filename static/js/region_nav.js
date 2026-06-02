/**
 * Show Journal Preparation nav/buttons when matching is complete for a job/region.
 */
window.RegionNav = {
    async fetchReady(jobId, subsidiaryId) {
        const res = await fetch(`/api/journal-prep-ready/${jobId}/${subsidiaryId}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Failed to check journal prep status');
        return data;
    },

    showNavLink(linkEl, data) {
        if (!linkEl || !data.ready) return;
        linkEl.style.display = '';
    },

    showButton(btnEl, data) {
        if (!btnEl || !data.ready) return;
        btnEl.style.display = '';
        if (data.unmatched_stripe_count != null && btnEl.dataset.showUnmatchedCount === '1') {
            const note = btnEl.querySelector('.unmatched-note');
            if (note) note.textContent = `${data.unmatched_stripe_count} unmatched Stripe`;
        }
    },

    initNavLink(jobId, subsidiaryId, linkId, alwaysShow) {
        const link = document.getElementById(linkId || 'nav-journal-prep-link');
        if (!link || !jobId || !subsidiaryId) return;
        if (alwaysShow) {
            link.style.display = '';
            return;
        }
        this.fetchReady(jobId, subsidiaryId)
            .then(data => this.showNavLink(link, data))
            .catch(err => console.warn('Journal prep nav:', err));
    },

    initButton(jobId, subsidiaryId, buttonId) {
        const btn = document.getElementById(buttonId);
        if (!btn || !jobId || !subsidiaryId) return;
        this.fetchReady(jobId, subsidiaryId)
            .then(data => this.showButton(btn, data))
            .catch(err => console.warn('Journal prep button:', err));
    },
};
