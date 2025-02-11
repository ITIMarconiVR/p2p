document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }
    
    document.getElementById('close-modal').addEventListener('click', function () {
        document.getElementById('modal-overlay').style.display = 'none';
    });
    
    const tutorsTableBody = document.querySelector('#tutors-table tbody');

    // Fetch tutors
    fetch('/tutors')
        .then(response => response.json())
        .then(data => {
            data.forEach(tutor => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${tutor.matricolaP}</td>
                    <td>${tutor.nome}</td>
                    <td>${tutor.cognome}</td>
                    <td>${tutor.classe}</td>
                    <td><button class="delete-button">Elimina</button></td>
                `;
                row.addEventListener('click', () => seeTutorInfo(tutor));
                row.querySelector('.delete-button').addEventListener('click', (event) => {
                    event.stopPropagation();
                    handleDeleteTutor(tutor.matricolaP, row);
                    });
                tutorsTableBody.appendChild(row);
            });
        })
        .catch(error => console.error('Error fetching tutors:', error));

    // Modal handling
    const modal = document.getElementById('add-tutor-modal');
    const openModalButton = document.getElementById('open-add-tutor-modal');
    const thead = document.getElementById('thead');

    openModalButton.addEventListener('click', () => {
        modal.style.display = 'flex';
        thead.style.position = 'static';
        modal.onclick = (event) => {
            event.preventDefault();
            event.stopPropagation();
            if (event.target === modal) {
                modal.style.display = 'none';
                modal.onclick = null;
                thead.style.position = 'sticky';
            }
        };
    });

});

function handleDeleteTutor(matricola, row) {
    if (confirm('Sei sicuro di voler eliminare questo tutor?')) {
        fetch('/tutors', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ matricola })
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('Tutor eliminato con successo');
                row.remove();
            } else {
                alert(`Errore: ${data.error}`);
            }
        })
        .catch(error => alert('Errore durante la rimozione del tutor.'));
    }
}

function handleAddTutor() {
    const form = document.getElementById('add-tutor');
    const formData = new FormData(form);
    fetch('/tutors', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.fromEntries(formData))
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert('Tutor aggiunto con successo');
            location.reload();
        } else {
            alert(`Errore: ${data.error}`);
        }
    })
    .catch(error => alert('Errore durante l\'aggiunta del tutor.'));
}

function seeTutorInfo(tutor) {
    const modal = document.getElementById('modal-overlay');
    document.getElementById('modal-header').textContent = `Informazioni sul tutor ${tutor.nome} ${tutor.cognome}`;

    const materieList = document.getElementById('materie-list');
    materieList.innerHTML = '';
    addMaterieInsegnate(tutor.matricolaP, materieList);

    document.getElementById('modal-text').innerHTML = `Matricola: ${tutor.matricolaP}<br>Nome: ${tutor.nome}<br>Cognome: ${tutor.cognome}<br>Classe: ${tutor.classe}`;

    modal.style.display = 'flex';
}

function addMaterieInsegnate(matricola, list) {
    fetch(`/materie?matricola=${matricola}`)
        .then(response => response.json())
        .then(data => {
            list.innerHTML = '<h3>Materie insegnate</h3>';
            list.innerHTML += `${data.map(materia => `<li>${materia}</li>`).join('')}`;
        })
        .catch(error => console.error('Error fetching materie:', error));
}