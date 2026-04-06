// ── Loading Overlay helpers (disponibili globalmente) ──
(function () {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-spinner"></div>
        <span class="loading-label">Caricamento in corso…</span>
    `;
    document.body ? document.body.appendChild(overlay)
                  : document.addEventListener('DOMContentLoaded', () => document.body.appendChild(overlay));
})();

function showLoading(msg) {
    const overlay = document.getElementById('loading-overlay');
    if (!overlay) return;
    const label = overlay.querySelector('.loading-label');
    if (label) label.textContent = msg || 'Caricamento in corso…';
    overlay.classList.add('visible');
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.classList.remove('visible');
}

document.addEventListener('DOMContentLoaded', () => {

    // ── Profile dropdown (desktop) ──
    const profileDropdown = document.querySelector('.profile-dropdown');
    if (profileDropdown) {
        profileDropdown.addEventListener('click', (e) => {
            // On mobile the profile menu is always visible inside the nav panel,
            // so skip the toggle behaviour
            if (window.innerWidth <= 768) return;
            profileDropdown.classList.toggle('active');
            e.stopPropagation();
        });
        document.addEventListener('click', () => {
            if (profileDropdown.classList.contains('active')) {
                profileDropdown.classList.remove('active');
            }
        });
    }

    // ── Hamburger menu (mobile) ──
    const menuToggle = document.querySelector('.menu-toggle');
    const nav = document.querySelector('nav');

    if (menuToggle && nav) {
        // Toggle open/close on hamburger click
        menuToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = nav.classList.toggle('open');
            menuToggle.querySelector('.icon').textContent = isOpen ? 'close' : 'menu';
        });

        // Close when clicking the backdrop (outside the ul panel)
        nav.addEventListener('click', (e) => {
            // clicked backdrop, not the panel itself
            if (e.target === nav) {
                nav.classList.remove('open');
                menuToggle.querySelector('.icon').textContent = 'menu';
            }
        });

        // Close when any nav link is tapped
        nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                nav.classList.remove('open');
                menuToggle.querySelector('.icon').textContent = 'menu';
            });
        });

        // Close on resize to desktop
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                nav.classList.remove('open');
                menuToggle.querySelector('.icon').textContent = 'menu';
            }
        });
    }

    // ── Greeting personalisation ──
    if (typeof userName !== 'undefined' && userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        if (greetingElement) {
            greetingElement.innerHTML = window.innerWidth <= 768
                ? `Bentornato,<br>${newUserName}!`
                : `Bentornato, ${newUserName}!`;
        }
    }

    // ── Notification badge & popup ──
    fetch('/notifiche/count')
        .then(res => res.json())
        .then(data => {
            if (data.count > 0) {
                const badge = document.getElementById('notifiche-badge');
                if (badge) {
                    badge.textContent = data.count;
                    badge.style.display = 'inline-flex';
                }

                let overlay = document.getElementById('notifiche-popup-overlay');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'notifiche-popup-overlay';
                    overlay.className = 'notifiche-popup-overlay';
                    overlay.innerHTML = `
                        <div class="notifiche-popup">
                            <h3>Nuove notifiche</h3>
                            <p id="notifiche-popup-text"></p>
                            <div class="notifiche-popup-actions">
                                <button class="btn-secondary" id="chiudi-notifiche-btn">Chiudi</button>
                                <button onclick="window.location.href='/notifiche/pagina'">Vai alle notifiche</button>
                            </div>
                        </div>
                    `;
                    document.body.appendChild(overlay);

                    document.getElementById('chiudi-notifiche-btn').addEventListener('click', () => {
                        overlay.classList.remove('visible');
                    });
                }

                const countText = document.getElementById('notifiche-popup-text');
                if (countText) {
                    countText.textContent = 'Hai ' + data.count + ' nuov' + (data.count === 1 ? 'a' : 'e') + ' notific' + (data.count === 1 ? 'a' : 'he') + ' da leggere.';
                }

                // Show popup only if not already on notifiche page
                if (!window.location.pathname.includes('/notifiche')) {
                    overlay.classList.add('visible');
                }
            }
        })
        .catch(err => console.error('Errore check notifiche:', err));
});
