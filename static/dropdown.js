document.addEventListener('DOMContentLoaded', () => {
    const profileDropdown = document.querySelector('.profile-dropdown');
    if (profileDropdown) {
        profileDropdown.addEventListener('click', (e) => {
            profileDropdown.classList.toggle('active');
            e.stopPropagation();
        });
        document.addEventListener('click', (e) => {
            if (profileDropdown.classList.contains('active')) {
                profileDropdown.classList.remove('active');
            }
        });
    }

    if (typeof userName !== 'undefined' && userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        if (greetingElement) {
            greetingElement.innerHTML = window.innerWidth <= 768 
                ? `Bentornato,<br>${newUserName}!` 
                : `Bentornato, ${newUserName}!`;
        }
    }

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
                                <button onclick="window.location.href='/notifiche/pagina'">Vai alle notifiche</button>
                                <button class="btn-secondary" id="chiudi-notifiche-btn">Chiudi</button>
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
                
                // Mostra il pop-up solo se l'utente non è già sulla pagina delle notifiche
                if (!window.location.pathname.includes('/notifiche')) {
                    overlay.classList.add('visible');
                }
            }
        })
        .catch(err => console.error('Errore check notifiche:', err));
});
