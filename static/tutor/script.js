const matricola = mail.substring(0, 5);

document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }
    
    createCalendar('calendar', `/lezioni2?matricolaP=${matricola}`);

    showLoading('Caricamento lezioni…');
    countLessons().then(([future, pastReserved]) => {
        updateLessonCounts(future, pastReserved);
        populateLessonLists(future, pastReserved).then(() => hideLoading());
    });

});

function updateLessonCounts(future, pastReserved) {
    document.getElementById('lessons-count').textContent = future;
    document.getElementById('lessons-count-PASTReserved').textContent = pastReserved;
    document.getElementById('lessons-total').textContent = (future + pastReserved);

    if (future + pastReserved >= 35) {
        document.getElementById('lessons-total').style.color = '#dc3545';
    }
}

async function populateLessonLists(future, pastReserved) {
    const scheduledList = document.getElementById('scheduled-lessons-list');
    const heldList = document.getElementById('held-lessons-list');

    try {
        const response = await fetch(`/lezioni2?matricolaP=${matricola}&matricolaT=%`);
        const data = await response.json();
        if (Array.isArray(data)) {
            data.forEach(event => {
                const date = new Date(event.data);
                const dateFormatted = date.toLocaleDateString('it-IT', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

                const li = document.createElement('li');
                if (date < new Date()) {
                    const capitalizedDateFormatted = dateFormatted.charAt(0).toUpperCase() + dateFormatted.slice(1);
                    li.innerHTML = `${capitalizedDateFormatted} alle ${event.ora === 2 ? '14:30' : '13:40'} (turno ${event.ora}) con ${event.nomeT} ${event.cognomeT}`;
                    heldList.appendChild(li);   
                } else {
                    if (event.matricolaT !== null) {
                        li.innerHTML = `Lezione in programma ${dateFormatted} alle ${event.ora === 2 ? '14:30' : '13:40'} (turno ${event.ora}) con ${event.nomeT} ${event.cognomeT}<br>${event.materiaL}: ${event.argomenti}`;
                        scheduledList.appendChild(li);
                    }
                }
            });
        } else {
            console.error('Formato inaspettato:', data);
        }
    } catch (error) {
        console.error('Errore durante il recupero delle lezioni:', error);
    }
}

function createCalendar(id, fetchUrl) {
    const calendarEl = document.getElementById(id);
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'it',
        buttonText: { today: 'Oggi' },
        firstDay: 1,
        selectable: true,
        events: (fetchInfo, successCallback, failureCallback) => {
            showLoading('Caricamento calendario…');
            fetch(fetchUrl)
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (Array.isArray(data)) {
                        const events = data.map(event => ({
                            title: `T${event.ora} ${event.validata === 0 ? 'Richiesta' : ''} ${event.matricolaT === null ? 'Lezione' : (event.nomeT + " " + event.cognomeT)} alle ${event.ora === 1 ? '13:40' : '14:30'}`,
                            start: new Date(event.data).toISOString(),
                            allDay: true,
                            matricolaP: matricola,
                            ora: event.ora,
                            data: event.data,
                            matricolaT: event.matricolaT,
                            backgroundColor: event.ora === 1 ? '#FF5733' : '#33B5FF',
                            borderColor: event.ora === 1 ? '#FF5733' : '#33B5FF'
                        }));
                        successCallback(events);
                    } else {
                        console.error('Unexpected response format:', data);
                        failureCallback(new Error('Unexpected response format'));
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error fetching events:', error);
                    failureCallback(error);
                });
        },
        selectAllow: (selectInfo) => {
            const now = new Date();
            now.setDate(now.getDate() + 2);
            return selectInfo.start >= now;
        },
        dateClick: (info) => {
            handleDateClick(info, calendar);
        },
        eventClick: (info) => {
            handleEventClick(info);
        },
        dayCellDidMount: (info) => {
            const today = new Date();
            if (info.date < today) {
                info.el.style.backgroundColor = '#f0f0f0'; // Light grey color for past days
            }
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
}

function handleDateClick(info, calendar) {
    const now = new Date();
    now.setDate(now.getDate() + 1);
    if (info.date >= now) {
        showAddLesson(info, calendar);
    } else {
        alert('Puoi dare disponibilità solo con almeno due giorni di anticipo.');
    }
}

function handleEventClick(info) {
    if (info.event.extendedProps.matricolaP === matricola) {
        removeLesson(info);
    }
}

async function countLessons() {
    let future = 0;
    let pastReserved = 0;
    try {
        const response = await fetch(`/lezioni?matricolaP=${matricola}`);
        const data = await response.json();
        if (Array.isArray(data)) {
            data.forEach(event => {
                if (new Date(event.data) >= new Date()) {
                    future++;
                } else if (event.matricolaT !== null) {
                    pastReserved++;
                }
            });
        } else {
            console.error('Formato inaspettato:', data);
        }
    } catch (error) {
        console.error('Errore durante il recupero delle lezioni:', error);
    }
    return [future, pastReserved];
}

function showAddLesson(info, calendar) {
    const modal = document.getElementById('add-tutor-modal');
    const dataInfo = document.getElementById('data-info');
    const dateObj = new Date(info.dateStr);
    const formattedDate = dateObj.toLocaleDateString('it-IT', { weekday: 'long', year: 'numeric', month: 'long', day: '2-digit' });
    dataInfo.innerHTML = formattedDate;

    modal.style.display = 'flex';
    modal.onclick = (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (event.target === modal) {
            modal.style.display = 'none';
            modal.onclick = null;
        }
    };

    const addLessonButton = document.getElementById('addLessonButton');
    addLessonButton.onclick = () => {
        addLesson(info);
        modal.style.display = 'none';
        modal.onclick = null;
        calendar.refetchEvents();
    };
}

function addLesson(info) {
    const ora = document.getElementById('shift-time').value;

    fetch('/add_event', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            matricolaP: matricola,
            ora: ora,
            data: info.dateStr
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            window.location.reload();
        } else {
            alert(`Errore: ${data.error}`);
        }
    });
}

function removeLesson(info) {
    const confirm = window.confirm('Sei sicuro di voler cancellare la lezione?');
    if (!confirm) return;
    const eventDate = new Date(info.event.start);
    const year = eventDate.getFullYear();
    const month = String(eventDate.getMonth() + 1).padStart(2, '0');
    const day = String(eventDate.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    fetch(`/lezioni?matricolaP=${matricola}&data=${formattedDate}&ora=${info.event.extendedProps.ora}`)
    .then(response => response.json())
    .then(data => {
        data = data[0];
        const now = new Date();
        const eventDate = new Date(info.event.start);
        if (eventDate <= now) {
            alert('Puoi cancellare lezioni solo con almeno un giorno di anticipo.');p2p
        } else if (data) {
            fetch('/delete_lezione_tutor', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    matricolaP: info.event.extendedProps.matricolaP,
                    data: formattedDate,
                    ora: info.event.extendedProps.ora,
                    matricolaT: info.event.extendedProps.matricolaT
                })
            })

            alert('Lezione rimossa con successo');
            location.reload();
        } else {
            alert(`Errore: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Errore durante la rimozione della lezione', error);
        alert('Si è verificato un errore. Riprova.');
    });
}
