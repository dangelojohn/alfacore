// AlfaCore Ops Sim — light JS islands for state-bearing interactions.
// Vanilla JS over OWL: low authoring overhead, easy to read, sufficient
// for wireframe-grade interactivity.
(function () {
    'use strict';

    function initSeverityFilter() {
        const filterBar = document.querySelector('[data-sim-island="filter"]');
        if (!filterBar) return;
        const buttons = filterBar.querySelectorAll('[data-filter]');
        const reports = document.querySelectorAll('[data-severity]');
        buttons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const filter = btn.getAttribute('data-filter');
                buttons.forEach(b => b.classList.remove('ac-btn--primary'));
                btn.classList.add('ac-btn--primary');
                reports.forEach(r => {
                    if (filter === 'all') {
                        r.style.display = '';
                    } else {
                        r.style.display = r.getAttribute('data-severity') === filter ? '' : 'none';
                    }
                });
            });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        initSeverityFilter();
    });
})();
