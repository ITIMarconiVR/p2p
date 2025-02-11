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

    loadMat();
    fetch(`/materie?matricola=${matricola}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(subject => {
                addSubject(subject);
            });
        })
        .catch(error => console.error('Errore durante il recupero delle materie:', error));

    document.getElementById('add-subject').addEventListener('submit', handleAddSubject);
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
    deleteButton.textContent = 'Remove';

    deleteButton.addEventListener('click', () => handleRemoveSubject(subjectID));

    subjectRow.appendChild(subjectName);
    deleteSubject.appendChild(deleteButton);
    subjectRow.appendChild(deleteSubject);

    subjectsList.appendChild(subjectRow);
}

function handleAddSubject(event) {
    const subjectName = document.getElementById('subject-name').value;

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