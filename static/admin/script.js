document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }

    document.getElementById('validate-all').addEventListener('click', () => valida_tutto());

    // Inizializzazione Toggle Servizio
    const toggleBtn = document.getElementById('servizio-toggle-btn');
    const statusLabel = document.getElementById('servizio-status-label');

    function updateToggleUI(attivo) {
        statusLabel.style.display = 'inline';
        toggleBtn.style.display = 'inline-block';
        if (attivo) {
            statusLabel.innerHTML = 'Servizio: <b style="color: green;">ATTIVO</b>';
            toggleBtn.textContent = 'Disabilita Servizio';
            toggleBtn.style.backgroundColor = ''; // Rimuove colore inline per usare il default css
        } else {
            statusLabel.innerHTML = 'Servizio: <b style="color: red;">DISABILITATO</b>';
            toggleBtn.textContent = 'Abilita Servizio';
            toggleBtn.style.backgroundColor = ''; // Rimuove colore inline per usare il default css
        }
    }

    // Carica stato iniziale
    fetch('/servizio_stato')
        .then(res => res.json())
        .then(data => updateToggleUI(data.attivo))
        .catch(err => console.error("Errore fetch stato servizio:", err));

    // Gestione click toggle
    toggleBtn.addEventListener('click', () => {
        if (confirm("Sei sicuro di voler cambiare lo stato del servizio globale?")) {
            fetch('/servizio_toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(res => res.json())
            .then(data => {
                if(data.error) {
                    alert("Errore: " + data.error);
                } else {
                    updateToggleUI(data.attivo);
                }
            })
            .catch(err => {
                console.error("Errore toggle servizio:", err);
                alert("Si è verificato un errore.");
            });
        }
    });

    const calendarEl = document.getElementById('calendar');
    const unvalidatedEventsList = document.getElementById('unvalidated-events-list');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'it',
        buttonText: { today: 'Oggi' },
        firstDay: 1,
        selectable: true,
        events: function(fetchInfo, successCallback, failureCallback) {
            showLoading('Caricamento calendario…');
            fetch('/lezioni2')
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (Array.isArray(data)) {
                        const events = data.map(event => ({
                            id: event.id,
                            title: `T${event.ora} ${event.validata === 0 ? 'Richiesta ' : ''}${event.nomeP} ${event.cognomeP} alle ${event.ora === 1 ? '13.40' : '14.30'}`,
                            nomeP: `${event.nomeP} ${event.cognomeP}`,
                            nomeT: `${event.nomeT} ${event.cognomeT}`,
                            start: new Date(event.data).toISOString(),
                            allDay: true,
                            matricolaP: event.matricolaP,
                            ora: event.ora,
                            validata: event.validata,
                            backgroundColor: event.ora === 1 ? '#FF5733' : '#33B5FF',
                            borderColor: event.ora === 1 ? '#FF5733' : '#33B5FF'
                        }));
                        successCallback(events);

                        unvalidatedEventsList.innerHTML = '';

                        const now = new Date();
                        const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

                        events.filter(event => {
                            const eventDateStr = event.start.split('T')[0];
                            return event.validata === 0 && eventDateStr >= todayStr;
                        }).forEach(event => {
                            const listItem = document.createElement('li');
                            const add = document.createElement('button');
                            add.textContent = 'Valida';
                            
                            const [year, month, day] = event.start.split('T')[0].split('-');
                            const eventDateObj = new Date(year, month - 1, day);
                            const formattedDate = eventDateObj.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
                            const oraStr = event.ora === 1 ? '13.40' : '14.30';
                            
                            listItem.innerHTML = `<span>Richiesta da parte di <b>${event.nomeP}</b> per il giorno <b>${formattedDate}</b> alle ${oraStr} (turno ${event.ora})</span>`;
                            listItem.dataset.eventId = event.id;
                            
                            add.addEventListener('click', () => {
                                if (confirm(`Vuoi validare questa lezione: ${event.title}?`)) {
                                    showLoading('Validazione in corso…');
                                    fetch('/lezioni', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json'
                                        },
                                        body: JSON.stringify({
                                            matricolaP: event.matricolaP,
                                            data: event.start.toString().split('T')[0],
                                            ora: event.ora,
                                        })
                                    })
                                    .then(response => response.json())
                                    .then(data => {
                                        hideLoading();
                                        if (data.message) {
                                            alert('Lezione validata con successo');
                                            unvalidatedEventsList.removeChild(listItem);
                                            location.reload();
                                        } else {
                                            alert(`Errore: ${data.error}`);
                                        }
                                    })
                                    .catch(error => {
                                        hideLoading();
                                        console.error('Errore durante la validazione della lezione', error);
                                        alert('Si è verificato un errore. Riprova.');
                                    });
                                }
                            });

                            listItem.appendChild(add);
                            unvalidatedEventsList.appendChild(listItem);
                        });

                        const eventDates = events.map(event => event.start.split('T')[0]);
                        const allCells = document.querySelectorAll('.fc-day');

                        allCells.forEach(cell => {
                            const cellDate = cell.getAttribute('data-date');
                            if (eventDates.includes(cellDate)) {
                                cell.classList.add('hasEvents');
                            } else {
                                cell.classList.remove('hasEvents');
                            }
                        });

                    } else {
                        failureCallback(new Error('Formato inaspettato'));
                    }
                })
                .catch(error => {
                    hideLoading();
                    failureCallback(error);
                });
        }
    });

    if (window.innerWidth <= 768) {
        const today = new Date();
        const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()+1));
        const endOfWeek = new Date(startOfWeek); 
        endOfWeek.setDate(startOfWeek.getDate() + 7);

        calendar.changeView('listWeek', {
            start: startOfWeek.toISOString().split('T')[0],
            end: endOfWeek.toISOString().split('T')[0]
        });
    }


    calendar.render();
    // Legenda colori calendario
    const _calLegend = document.createElement('div');
    _calLegend.className = 'calendar-legend';
    _calLegend.innerHTML = `
        <div class='calendar-legend-item'>
            <span class='calendar-legend-dot' style='background-color:#FF5733;'></span>
            Turno 1 (13:40)
        </div>
        <div class='calendar-legend-item'>
            <span class='calendar-legend-dot' style='background-color:#33B5FF;'></span>
            Turno 2 (14:30)
        </div>
    `;
    const _calToolbar = calendarEl.querySelector('.fc-toolbar');
    if (_calToolbar) _calToolbar.insertAdjacentElement('afterend', _calLegend);

    document.getElementById('close-modal').addEventListener('click', function () {
        document.getElementById('modal-overlay').style.display = 'none';
    });
    
    calendarEl.addEventListener('click', (event) => {
        const cell = event.target.closest('.fc-day');
        if (!cell) return;
    
        const dateStr = cell.getAttribute('data-date');
        if (!dateStr) return;
    
        const eventsForDay = calendar.getEvents().filter(event =>
            event.start.toISOString().split('T')[0] === dateStr
        );
    
        if (eventsForDay.length === 0) return;
    
        const formattedDate = new Date(dateStr).toLocaleDateString('it-IT', { year: 'numeric', month: 'long', day: 'numeric' });
    
        const modal = document.getElementById('modal-overlay');
        document.getElementById('modal-header').textContent = `Eventi del giorno ${formattedDate}`;
        const eventList = document.getElementById('event-list');
        eventList.innerHTML = '';
    
        eventsForDay.forEach(event => {
            const eventItem = document.createElement('li');
            eventItem.textContent = event.title;
            eventList.appendChild(eventItem);
        });
    
        modal.style.display = 'flex';
    });
});

function valida_tutto() {
    if (confirm('Vuoi validare tutte le lezioni?')) {
        showLoading('Validazione in corso…');
        fetch('/valida_tutto', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            if (data.message) {
                alert('Tutte le lezioni sono state validate con successo');
                location.reload();
            } else {
                alert(`Errore: ${data.error}`);
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Errore durante la validazione delle lezioni', error);
            alert('Si è verificato un errore. Riprova.');
        });
    }
}