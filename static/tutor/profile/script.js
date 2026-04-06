const matricola = mail.substring(0, 5);
const subjectsList = document.getElementById('subjects-table-content');

document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }

    loadDescription();
    loadMat();
    fetch(`/materie?matricola=${matricola}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(subject => {
                addSubject(subject);
            });
        })
        .catch(error => console.error('Errore durante il recupero delle materie:', error));

});

async function loadMat() {
    const subjectSel = document.getElementById('subject-name');

    fetch('/materie')
        .then(response => response.json())
        .then(data => {
            data.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.idMat;
                option.text = subject.idMat;
                subjectSel.appendChild(option);
            });
        })
        .catch(error => console.error('Errore durante il recupero delle materie:', error));
}

function handleRemoveSubject(subjectId) {
    if (confirm('Sei sicuro di voler rimuovere questa materia?')) {
        fetch('/materie', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ matricola: matricola, idMat: subjectId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('Materia rimossa con successo');
                document.getElementById(subjectId).remove();
            } else {
                alert(`Errore: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Errore durante la rimozione della materia:', error);
            alert('Si è verificato un errore. Riprova.');
        });
    }
}

function addSubject(subjectID) {
    const subjectRow = document.createElement('tr');
    subjectRow.id = subjectID;

    const subjectName = document.createElement('td');
    const deleteSubject = document.createElement('td');
    const deleteButton = document.createElement('button');

    subjectName.textContent = subjectID;
    deleteButton.textContent = 'Rimuovi';

    deleteButton.addEventListener('click', () => handleRemoveSubject(subjectID));

    subjectRow.appendChild(subjectName);
    deleteSubject.appendChild(deleteButton);
    subjectRow.appendChild(deleteSubject);

    subjectsList.appendChild(subjectRow);
}

function handleAddSubject() {
    const sel = document.getElementById('subject-name');
    const subjectName = sel.value;

    if (!subjectName || subjectName === '-1') {
        alert('Seleziona una materia prima di aggiungerla.');
        return;
    }

    // Evita duplicati
    if (document.getElementById(subjectName)) {
        alert('Questa materia è già presente.');
        return;
    }

    fetch('/materie', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ matricola: matricola, materia: subjectName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            addSubject(subjectName);
            sel.value = '-1'; // reset selezione
            alert('Materia aggiunta con successo');
        } else {
            alert(`Errore: ${data.error}`);
        }
    })
    .catch(error => {
        console.error('Errore durante l\'aggiunta della materia:', error);
        alert('Si è verificato un errore. Riprova.');
    });
}

async function loadDescription() {
    try {
        const res = await fetch('/tutors/descrizione');
        if (res.ok) {
            const data = await res.json();
            document.getElementById('tutor-description').value = data.descrizione || '';
        }
    } catch (e) {
        console.error('Errore get descrizione', e);
    }
}

async function handleSaveDescription() {
    const desc = document.getElementById('tutor-description').value;
    try {
        const res = await fetch('/tutors/descrizione', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ descrizione: desc })
        });
        const data = await res.json();
        if (data.message) {
            alert('Descrizione salvata con successo');
        } else {
            alert('Errore: ' + data.error);
        }
    } catch (e) {
        alert('Errore durante il salvataggio');
    }
}