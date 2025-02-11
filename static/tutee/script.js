
const matricola = mail.substring(0, 5);
document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }

    isTutor();

    createCalendar(matricola, '/lezioni2?matricolaT=');
    const upLessons = document.getElementById('upcoming-events-list');
    loadUpcomingLessons(upLessons);
});

function isTutor() {
    fetch("/userInfo")
        .then(response => response.json())
        .then(data => {
            if (data.tipo === "tutor") {
                const ulNav = document.getElementById('listNav');
                const liNav = document.createElement('li');
                liNav.innerHTML = "Tutor";
                liNav.style.cursor = "pointer";
                liNav.addEventListener('click', () => {
                    window.location.href = '/loginTutor';
                });
                ulNav.appendChild(liNav);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function redirectToLogin() {
    window.location.href = '../login/index.html';
}

function createCalendar(matricola, fetchUrl) {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'it',
        firstDay: 1,
        selectable: true,
        events: (fetchInfo, successCallback, failureCallback) => {
            fetchEvents(fetchUrl + matricola, successCallback, failureCallback);
        },
        eventClick: (info) => {
            handleEventClick(matricola, info);
        },
        dayCellDidMount: (info) => {
            const today = new Date();
            if (info.date < today) {
                info.el.style.backgroundColor = '#f0f0f0'; // Light grey color for past days
                info.el.innerHTML = ''; // Remove any content
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
}

function fetchEvents(url, successCallback, failureCallback) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                const events = data.map(event => ({
                    id: event.id,
                    title: `T${event.ora} ${event.nomeP} ${event.cognomeP} alle ${event.ora === 1 ? '13.40' : '14.30'}`,
                    start: new Date(event.data).toISOString(),
                    allDay: true,
                    matricolaP: event.matricolaP,
                    matricolaT: event.matricolaT,
                    ora: event.ora,
                    classeP: event.classeP,
                    validata: event.validata,
                    backgroundColor: event.ora === 1 ? '#FF5733' : '#33B5FF',
                    borderColor: event.ora === 1 ? '#FF5733' : '#33B5FF'
                }));
                successCallback(events);
            } else {
                handleUnexpectedResponse(data, failureCallback);
            }
        })
        .catch(error => {
            console.error('Error fetching events:', error);
            failureCallback(error);
        });
}

function handleUnexpectedResponse(data, failureCallback) {
    console.error('Unexpected response format:', data);
    failureCallback(new Error('Unexpected response format'));
}

function handleEventClick(matricola, info) {
    // check if the data is today or in the future
    if (new Date(info.event.start) < new Date()) {
        alert('Non puoi rimuovere una prenotazione passata');
        return;
    }
    if (confirm(`Vuoi rimuovere questa prenotazione: ${info.event.title} ${info.event.extendedProps.classeP}?`)) {
        removeEvent(matricola, info);
    }
}

function removeEvent(matricola, info) {
    const eventDate = new Date(info.event.start);
    const year = eventDate.getFullYear();
    const month = String(eventDate.getMonth() + 1).padStart(2, '0');
    const day = String(eventDate.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    fetch('/delete_lezione_tutee', {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            matricolaT: matricola,
            data: formattedDate,
            ora: info.event.extendedProps.ora,
            matricolaP: info.event.extendedProps.matricolaP
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert('Reservation removed successfully');
            location.reload();
        } else {
            alert(`Error: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Error removing reservation:', error);
        alert('An error occurred. Please try again.');
    });
}

function loadUpcomingLessons(upLessons) {
    fetch(`/lezioni2?matricolaT=${matricola}`)
        .then(response => response.json())
        .then(data => {
            if (Array.isArray(data)) {
                const lessons = data.map(lesson => {
                    const li = document.createElement('li');
                    const data = new Date(lesson.data).toLocaleDateString('it-IT', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
                    if (new Date(lesson.data) < new Date()) return null
                    li.innerHTML = `<span><b>${data}</b> alle <b>${lesson.ora === 1 ? '13.40' : '14.30'} |</b> Lezione con tutor: <b>${lesson.nomeP} ${lesson.cognomeP}</b> su <b>${lesson.materiaL}: ${lesson.argomenti}</b></span>`;
                    return li;
                });
                lessons.forEach(lesson => {if (lesson !== null) upLessons.appendChild(lesson)});
            } else {
                console.error('Unexpected response format:', data);
            }
        })
        .catch(error => {
            console.error('Error fetching upcoming lessons:', error);
        });
}
