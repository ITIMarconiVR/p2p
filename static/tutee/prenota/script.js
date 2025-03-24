const matricola = mail.substring(0, 5);

const materieSelect = document.getElementById('materie');
const classesSelect = document.getElementById('tutor_classes');
const indirizzoSelect = document.getElementById('tutor_indirizzo');
const nomiSelect = document.getElementById('tutor_nomi');

document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }

    createMaterieDropdown();
    createAnnoTutorDropdown();
    createIndirizzoDropdown();
    createNomeTutorDropdown();

    createCalendar(matricola, `/lezioniFilter?idMat=ALL&anno=ALL&indirizzo=ALL&matricolaP=ALL`);
});

function createMaterieDropdown() {
    fetch('/materie')
        .then(response => response.json())
        .then(data => {
            const allOption = document.createElement('option');
            allOption.value = 'ALL';
            allOption.textContent = 'ALL';
            materieSelect.appendChild(allOption);

            data.forEach(materia => {
                const option = document.createElement('option');
                option.value = materia.idMat;
                option.textContent = materia.idMat;
                materieSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Errore durante il recupero delle materie:', error));

    materieSelect.addEventListener('change', updateCalendar);
    classesSelect.addEventListener('change', updateCalendar);
    indirizzoSelect.addEventListener('change', updateCalendar);
    nomiSelect.addEventListener('change', updateCalendar);
}

function createAnnoTutorDropdown() {
    fetch('/tutors')
        .then(response => response.json())
        .then(data => {
            const allOption = document.createElement('option');
            allOption.value = 'ALL';
            allOption.textContent = 'ALL';
            classesSelect.appendChild(allOption);
            
            const anni = [...new Set(data.map(classe => classe.classe.split()[0][0]))];
            anni.forEach(anno => {
                const option = document.createElement('option');
                option.value = anno;
                option.textContent = anno;
                classesSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Errore durante il recupero delle classi', error));

    materieSelect.addEventListener('change', updateCalendar);
    classesSelect.addEventListener('change', updateCalendar);
    indirizzoSelect.addEventListener('change', updateCalendar);
    nomiSelect.addEventListener('change', updateCalendar);
}

function createIndirizzoDropdown() {
    const allOption = document.createElement('option');
    allOption.value = 'ALL';
    allOption.textContent = 'ALL';
    indirizzoSelect.appendChild(allOption);

    const indirizzi = ['Informatica', 'Elettronica', 'Telecomunicazioni', 'Costruzione del Mezzo', 'Logistica', 'Biennio'];
    indirizzi.forEach(indirizzo => {
        const option = document.createElement('option');
        option.value = indirizzo;
        option.textContent = indirizzo;
        indirizzoSelect.appendChild(option);
    });

    materieSelect.addEventListener('change', updateCalendar);
    classesSelect.addEventListener('change', updateCalendar);
    indirizzoSelect.addEventListener('change', updateCalendar);
    nomiSelect.addEventListener('change', updateCalendar);
}

function createNomeTutorDropdown() {
    fetch('/tutors')
        .then(response => response.json())
        .then(data => {
            const allOption = document.createElement('option');
            allOption.value = 'ALL';
            allOption.textContent = 'ALL';
            nomiSelect.appendChild(allOption);
            
            data.forEach(tutor => {
                const option = document.createElement('option');
                option.value = tutor.matricolaP;
                option.textContent = `${tutor.nome} ${tutor.cognome} ${tutor.classe}`;
                nomiSelect.appendChild(option);
            });
        })
        .catch(error => console.error('Errore durante il recupero dei nomi', error));

    materieSelect.addEventListener('change', updateCalendar);
    classesSelect.addEventListener('change', updateCalendar);
    indirizzoSelect.addEventListener('change', updateCalendar);
    nomiSelect.addEventListener('change', updateCalendar);
}


function updateCalendar() {
    const selectedMateria = materieSelect.value;
    const selectedAnno = classesSelect.value;
    const selectedIndirizzo = indirizzoSelect.value;
    const selectedMatricola= nomiSelect.value;
    createCalendar(matricola, `/lezioniFilter?idMat=${selectedMateria}&anno=${selectedAnno}&indirizzo=${selectedIndirizzo}&matricolaP=${selectedMatricola}`);
}

function createCalendar(matricola, fetchUrl) {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'it',
        firstDay: 1,
        selectable: true,
        // views: {
        //     dayGridMonth: {
        //         dayMaxEventRows: 5
        //     }
        // },
        events: (fetchInfo, successCallback, failureCallback) => {
            fetch(fetchUrl)
                .then(response => response.json())
                .then(data => {
                    if (Array.isArray(data)) {
                        const now = new Date();
                        const events = data
                            .filter(event => new Date(event.data) >= now) // Filter out past events
                            .map(event => ({
                                title: `T${event.ora}  ${(event.nomeP + " " + event.cognomeP)} alle ${event.ora === 1 ? '13:40' : '14:30'}`,
                                start: new Date(event.data).toISOString(),
                                allDay: true,
                                matricolaP: event.matricolaP,
                                ora: event.ora,
                                classeP: event.classeP,
                                materiaL: event.idMat,
                                backgroundColor: event.ora === 1 ? '#FF5733' : '#33B5FF',
                                borderColor: event.ora === 1 ? '#FF5733' : '#33B5FF'
                            }));
                        successCallback(events);
                    } else {
                        console.error('Formato inaspettato:', data);
                        failureCallback(new Error('Formato inaspettato'));
                    }
                })
                .catch(error => {
                    console.error('Errore durante il recupero degli eventi', error);
                    failureCallback(error);
                });
        },
        selectAllow: selectInfo => {
            checkDate = selectInfo.start;
            const today = new Date();
            const twoDaysFromNow = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 2);
            const checkDate = new Date(dateToCheck);
            const dateOnly = new Date(checkDate.getFullYear(), checkDate.getMonth(), checkDate.getDate());
            
            return dateOnly >= twoDaysFromNow;
        },
        eventClick: async info => {
            showPrenotaLezione(info);
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

async function showPrenotaLezione(info) {
    const now = new Date();
    // add 2 days to the current date
    //now.setDate(now.getDate() + 1);
    //LLL aggiunge sei ore limite delle 18.00 del giorno precedente
    // info.event.start punta allamezzanotte
    now.setHours(now.getHours()+5)
    if (info.event.start <= now) {
        alert('Puoi prenotare lezioni fino alle 19.00 del giorno precedente.');
        return;
    }
    const tuteeAvailable = await tuteeHasLesson(info);
    if (tuteeAvailable) {
        alert('Hai già prenotato una lezione per questa data e ora.');
        return;
    }

    const modal = document.getElementById('add-tutor-modal');
    const tutorinfo = document.getElementById('tutor-info');
    tutorinfo.innerHTML = `Con Tutor: ${info.event._def.title.substring(4,)} ${info.event._def.extendedProps.classeP}`;

    const select = document.getElementById('shift-mat');
    select.innerHTML = '';
    const option = document.createElement('option');
    option.value = "-1";
    option.textContent = "Materia";
    select.appendChild(option);

    fetch(`/materie?matricola=${info.event._def.extendedProps.matricolaP}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(materia => {
                const option = document.createElement('option');
                option.value = materia;
                option.textContent = materia;
                select.appendChild(option);
            });
        })
        .catch(error => console.error('Errore durante il recupero delle materie:', error));

    const confrimLessonButton = document.getElementById('confrimLessonButton');
    confrimLessonButton.onclick = async () => confirmLesson(info);

    modal.style.display = 'flex';
    modal.onclick = (event) => {
        event.preventDefault();
        event.stopPropagation();
        if (event.target === modal) {
            modal.style.display = 'none';
            modal.onclick = null;
        }
    };
}


async function confirmLesson(info) {
    const select = document.getElementById('shift-mat');
    const materiaL = select.value;

    const eventDate = new Date(info.event.start);
    const year = eventDate.getFullYear();
    const month = String(eventDate.getMonth() + 1).padStart(2, '0');
    const day = String(eventDate.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;

    if (materiaL === "-1") {
        alert('Seleziona una materia valida.');
        return;
    }

    const argomenti = document.getElementById('lesson-dettagli').value;
    if (!argomenti) {
        alert('Inserisci gli argomenti della lezione.');
        return;
    }
    if(argomenti.length > 100){
        alert('Gli argomenti della lezione devono essere al massimo 100 caratteri.\nNe hai inseriti: ' + argomenti.length);
        return;
    }
    try {
        const response = await fetch('/prenota', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                matricolaP: info.event.extendedProps.matricolaP,
                data: formattedDate,
                ora: info.event.extendedProps.ora,
                matricolaT: matricola,
                materiaL: materiaL,
                argomenti: argomenti,
                nomecognT: userName
            })
        });
        const data = await response.json();
        if (data.message) {
            const modal = document.getElementById('add-tutor-modal');
            modal.style.display = 'none';
            modal.onclick = null;
            alert('Lezione prenotata con successo');
            destinatari = [];
            location.reload();
        } else {
            alert(`Errore: ${data.error}`);
        }
    } catch (error) {
        console.error('Errore durante la prenotazione della lezione', error);
        alert('Si è verificato un errore. Riprova.');
    }
}

async function checkIfTutor(matricolaP, materiaL) {
    try {
        const response = await fetch(`/materie?matricola=${matricolaP}`);
        if (!response.ok) {
            throw new Error('La risposta del server non è valida');
        }
        const data = await response.json();
        return data.some(materia => materia === materiaL);
    } catch (error) {
        console.error('Errore durante l\'accertamento della disponibilità del tutor', error);
        return false;
    }
}

async function tuteeHasLesson(info) {
    const dataL = info.event.start.toISOString().split('T')[0];
    const ora = info.event.extendedProps.ora;
    try {
        fetch(`/lezioni?matricolaT=${matricola}&data=${dataL}`)
            .then(response => response.json())
            .then(data => {
                return data.length>0
            })
            .catch(error => console.error('Errore durante il recupero delle lezioni:', error)
        );
    } catch (error) {
        console.error('Errore durante il controllo delle lezioni del tutee', error);
        return false;
    }
}
