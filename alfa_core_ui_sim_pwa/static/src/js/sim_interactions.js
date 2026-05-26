// AlfaCore PWA wireframe — shared JS
// Reads JWT from URL fragment, fetches /api/v1/*, renders into the page.
// In mockup mode (?mockup=1), uses bundled mock data and skips network calls.

(function () {
    'use strict';

    const AlfacorePwa = {
        _token: null,
        _mockup: false,

        init() {
            // Extract token from URL fragment, then strip it from the URL bar
            // (replaceState — leaves browsing history clean of the bearer).
            const hash = window.location.hash || '';
            const tokenMatch = hash.match(/token=([^&]+)/);
            if (tokenMatch) {
                this._token = tokenMatch[1];
                // Clean the URL so the token doesn't linger in the address bar
                history.replaceState(null, '', window.location.pathname + window.location.search);
            }
            this._mockup = new URLSearchParams(window.location.search).has('mockup');

            if (typeof window.PageInit === 'function') {
                window.PageInit(this);
            }
        },

        isMockup() {
            return this._mockup;
        },

        async fetchJson(path, opts = {}) {
            if (this._mockup) {
                throw new Error('fetchJson called in mockup mode — page should use MOCKUP_DATA');
            }
            if (!this._token) {
                throw new Error('No JWT in URL fragment — re-launch via /alfacore/sim/pwa');
            }
            const url = path.startsWith('http') ? path : (window.location.origin + path);
            const headers = Object.assign(
                { 'Authorization': 'Bearer ' + this._token, 'Accept': 'application/json' },
                opts.headers || {}
            );
            const response = await fetch(url, Object.assign({}, opts, { headers }));
            if (!response.ok) {
                const errBody = await response.text();
                throw new Error(`HTTP ${response.status}: ${errBody.slice(0, 200)}`);
            }
            return response.json();
        },

        // Render helpers — kept tiny on purpose
        $(sel, root) {
            return (root || document).querySelector(sel);
        },
        showError(target, msg) {
            const el = typeof target === 'string' ? this.$(target) : target;
            if (!el) return;
            el.innerHTML = '<div class="ac-card" style="border-color: var(--ac-danger);">' +
                           '<div class="ac-eyebrow" style="color: var(--ac-danger);">Error</div>' +
                           '<p>' + this._escapeHtml(msg) + '</p>' +
                           '<p><small>Try the <a href="?mockup=1">mockup-data version</a> for design review.</small></p>' +
                           '</div>';
        },
        _escapeHtml(s) {
            return String(s)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        },
    };

    window.AlfacorePwa = AlfacorePwa;
    window.addEventListener('DOMContentLoaded', () => AlfacorePwa.init());
})();
