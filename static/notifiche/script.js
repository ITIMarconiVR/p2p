document.addEventListener('DOMContentLoaded', () => {
    const notificheList = document.getElementById('notifiche-list');
    const emptyMessage = document.getElementById('notifiche-empty');
    const segnaTutteBtn = document.getElementById('segna-tutte-lette-btn');

    // Carica tutte le notifiche
    function loadNotifiche() {
        fetch('/notifiche')
            .then(async res => {
                if (!res.ok) {
                    const text = await res.text();
                    throw new Error(`HTTP ${res.status}: ${text}`);
                }
                const text = await res.text();
                try {
                    return JSON.parse(text);
                } catch (e) {
                    throw new Error(`Invalid JSON: ${text}`);
                }
            })
            .then(data => {
                notificheList.innerHTML = '';

                if (!Array.isArray(data) || data.length === 0) {
                    if (data && data.error) {
                        emptyMessage.textContent = 'Errore server: ' + data.error;
                    } else {
                        emptyMessage.textContent = 'Nessuna notifica.';
                    }
                    emptyMessage.style.display = 'block';
                    segnaTutteBtn.style.display = 'none';
                    return;
                }

                emptyMessage.style.display = 'none';

                // Mostra/nascondi il pulsante "segna tutte" in base alle non lette
                const nonLette = data.filter(n => n.letta === 0);
                segnaTutteBtn.style.display = nonLette.length > 0 ? 'inline-block' : 'none';

                data.forEach(notifica => {
                    const li = document.createElement('li');
                    li.className = 'notifica-card' + (notifica.letta === 0 ? ' non-letta' : '');
                    li.dataset.id = notifica.id;

                    // Formatta data
                    let dataStr = '';
                    if (notifica.data_ora) {
                        try {
                            const dataOra = new Date(notifica.data_ora);
                            dataStr = dataOra.toLocaleDateString('it-IT', {
                                year: 'numeric', month: 'long', day: 'numeric',
                                hour: '2-digit', minute: '2-digit'
                            });
                        } catch(e) { dataStr = notifica.data_ora; }
                    }

                    let footerHTML = `<span class="notifica-data">${dataStr}</span>`;
                    if (notifica.letta === 0) {
                        footerHTML += `<button class="segna-letta-btn" data-id="${notifica.id}">Segna come letta</button>`;
                    }

                    li.innerHTML = `
                        <p class="notifica-titolo">${escapeHtml(notifica.titolo)}</p>
                        <p class="notifica-corpo">${escapeHtml(notifica.corpo)}</p>
                        <div class="notifica-footer">
                            ${footerHTML}
                        </div>
                    `;

                    notificheList.appendChild(li);
                });

                // Event listener per i pulsanti "segna come letta"
                document.querySelectorAll('.segna-letta-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        const id = e.target.dataset.id;
                        segnaComeLetta(id);
                    });
                });
            })
            .catch(err => {
                console.error('Errore caricamento notifiche:', err);
                emptyMessage.textContent = 'Errore nel caricamento delle notifiche. DETTAGLI: ' + err.message;
                emptyMessage.style.display = 'block';
            });
    }

    // Segna una notifica come letta
    function segnaComeLetta(id) {
        fetch(`/notifiche/${id}/letta`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                // Aggiorna la UI senza ricaricare
                const card = document.querySelector(`.notifica-card[data-id="${id}"]`);
                if (card) {
                    card.classList.remove('non-letta');
                    const btn = card.querySelector('.segna-letta-btn');
                    if (btn) btn.remove();
                }
                // Aggiorna visibilità pulsante "segna tutte"
                const remaining = document.querySelectorAll('.notifica-card.non-letta');
                if (remaining.length === 0) {
                    segnaTutteBtn.style.display = 'none';
                }
            }
        })
        .catch(err => console.error('Errore segna letta:', err));
    }

    // Segna tutte come lette
    segnaTutteBtn.addEventListener('click', () => {
        fetch('/notifiche/segna_tutte_lette', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                // Aggiorna tutte le card
                document.querySelectorAll('.notifica-card.non-letta').forEach(card => {
                    card.classList.remove('non-letta');
                    const btn = card.querySelector('.segna-letta-btn');
                    if (btn) btn.remove();
                });
                segnaTutteBtn.style.display = 'none';
            }
        })
        .catch(err => console.error('Errore segna tutte lette:', err));
    });

    // Utility: escape HTML per prevenire XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Carica le notifiche all'avvio
    loadNotifiche();
});
