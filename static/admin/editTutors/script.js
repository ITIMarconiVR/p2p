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
            let totalLezioni = 0;
            data.forEach(tutor => {
                totalLezioni += Number(tutor.lezioni) || 0;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${tutor.matricolaP}</td>
                    <td>${tutor.nome}</td>
                    <td>${tutor.cognome}</td>
                    <td>${tutor.classe}</td>
                    <td>${tutor.lezioni}</td>
                    <td><button class="delete-button">Elimina</button></td>
                `;
                row.addEventListener('click', () => seeTutorInfo(tutor));
                row.querySelector('.delete-button').addEventListener('click', (event) => {
                    event.stopPropagation();
                    handleDeleteTutor(tutor.matricolaP, row);
                    });
                tutorsTableBody.appendChild(row);
            });

            // Add total row
            const totalRow = document.createElement('tr');
            totalRow.style.fontWeight = 'bold';
            totalRow.innerHTML = `
                <td colspan="4" style="text-align: right;">Totale Lezioni:</td>
                <td>${totalLezioni}</td>
                <td></td>
            `;
            tutorsTableBody.appendChild(totalRow);
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

async function seeTutorInfo(tutor) {
    const modal = document.getElementById('modal-overlay');
    document.getElementById('modal-header').textContent = `Informazioni sul tutor ${tutor.nome} ${tutor.cognome}`;
    document.getElementById('modal-text').innerHTML = `Matricola: ${tutor.matricolaP}<br>Nome: ${tutor.nome}<br>Cognome: ${tutor.cognome}<br>Classe: ${tutor.classe}<br><br><b>Descrizione:</b><br>${tutor.descrizione || 'Nessuna descrizione impostata'}`;


    // lista materie insegnate dal tutor
    const materieList = document.getElementById('materie-list');
    materieList.innerHTML = '';
    addMaterieInsegnate(tutor.matricolaP, materieList);

    // numero lezioni cancellate dal tutor che erano prenotate e sono state cancellate a meno di due giorni dalla data della lezione
    const meno2g_prenotate = document.getElementById('meno2g_prenotate');
    nLez = await statisticheTutor(tutor.matricolaP, 2, 1);
    console.log(nLez);
    meno2g_prenotate.innerHTML = 'A meno di due giorni e prenotate: ' + nLez;

    // numero lezioni cancellate dal tutor che erano prenotate
    prenotate = document.getElementById('prenotate');
    nLez = await statisticheTutor(tutor.matricolaP, null, 1);
    prenotate.innerHTML = 'Prenotate: ' + nLez;

    // numero lezioni cancellate dal tutor in tutto
    totali = document.getElementById('totali');
    nLez = await statisticheTutor(tutor.matricolaP);
    totali.innerHTML = 'Totali: ' + nLez;   

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

async function statisticheTutor(matricola, distLezione = null, prenotata = 0) {
    try {
        const response = await fetch(`/lezioni_cancellate/${matricola}/${distLezione}/${prenotata}`);
        const data = await response.json();
        return data.length;
    } catch (error) {
        console.error('Error fetching statistiche:', error);
        return 0; // Return 0 in case of error
    }
}