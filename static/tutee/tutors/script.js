const matricola = mail.substring(0, 5);

const materieSelect = document.getElementById('materie');
const classesSelect = document.getElementById('tutor_classes');
const indirizzoSelect = document.getElementById('tutor_indirizzo');
const nomiSelect = document.getElementById('tutor_nomi');

let allTutors = [];
let allSubjectsMapping = {};

document.addEventListener('DOMContentLoaded', () => {
    if (userName) {
        const newUserName = userName.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        const greetingElement = document.getElementById('greeting');
        
        greetingElement.innerHTML = window.innerWidth <= 768 
            ? `Bentornato,<br>${newUserName}!` 
            : `Bentornato, ${newUserName}!`;
    }

    createMaterieDropdown();
    createIndirizzoDropdown();
    
    loadTutors();
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

    materieSelect.addEventListener('change', renderTutors);
    classesSelect.addEventListener('change', renderTutors);
    indirizzoSelect.addEventListener('change', renderTutors);
    nomiSelect.addEventListener('change', renderTutors);
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
}

function populateTutorDropdowns() {
    const allOptionC = document.createElement('option');
    allOptionC.value = 'ALL';
    allOptionC.textContent = 'ALL';
    classesSelect.appendChild(allOptionC);
    
    const anni = [...new Set(allTutors.map(t => t.classe ? t.classe.charAt(0) : ''))].filter(x => x);
    anni.forEach(anno => {
        const option = document.createElement('option');
        option.value = anno;
        option.textContent = anno;
        classesSelect.appendChild(option);
    });

    const allOptionN = document.createElement('option');
    allOptionN.value = 'ALL';
    allOptionN.textContent = 'ALL';
    nomiSelect.appendChild(allOptionN);
    
    allTutors.forEach(tutor => {
        const option = document.createElement('option');
        option.value = tutor.matricolaP;
        option.textContent = `${tutor.nome} ${tutor.cognome} ${tutor.classe}`;
        nomiSelect.appendChild(option);
    });
}

async function loadTutors() {
    try {
        const res = await fetch('/tutors');
        allTutors = await res.json();
        
        await Promise.all(allTutors.map(async (tutor) => {
            try {
                const subRes = await fetch(`/materie?matricola=${tutor.matricolaP}`);
                const subs = await subRes.json();
                allSubjectsMapping[tutor.matricolaP] = subs || [];
            } catch (e) {
                allSubjectsMapping[tutor.matricolaP] = [];
            }
        }));

        allTutors = allTutors.filter(t => allSubjectsMapping[t.matricolaP] && allSubjectsMapping[t.matricolaP].length > 0);
        
        populateTutorDropdowns();
        renderTutors();
    } catch (e) {
        console.error('Errore durante il recupero dei tutor:', e);
    }
}

function getIndirizzoFromClasse(classeStr) {
    if (!classeStr) return 'ALL';
    const c = classeStr.toUpperCase();
    if (c.includes('IN')) return 'Informatica';
    if (c.includes('EL') || c.includes('EA') || c.includes('EN')) return 'Elettronica';
    if (c.includes('TL')) return 'Telecomunicazioni';
    if (c.includes('CM')) return 'Costruzione del Mezzo';
    if (c.includes('LO')) return 'Logistica';
    if (c.startsWith('1') || c.startsWith('2')) return 'Biennio';
    return 'ALL';
}

function renderTutors() {
    const container = document.getElementById('tutor-cards-container');
    container.innerHTML = '';
    
    const selectedMateria = materieSelect.value;
    const selectedAnno = classesSelect.value;
    const selectedIndirizzo = indirizzoSelect.value;
    const selectedMatricola = nomiSelect.value;

    const filtered = allTutors.filter(tutor => {
        if (selectedMatricola !== 'ALL' && tutor.matricolaP !== selectedMatricola) return false;
        if (selectedAnno !== 'ALL' && (!tutor.classe || !tutor.classe.startsWith(selectedAnno))) return false;
        if (selectedIndirizzo !== 'ALL') {
            const ind = getIndirizzoFromClasse(tutor.classe);
            if (ind !== selectedIndirizzo) return false;
        }
        if (selectedMateria !== 'ALL') {
            const subs = allSubjectsMapping[tutor.matricolaP] || [];
            if (!subs.includes(selectedMateria)) return false;
        }
        return true;
    });

    if (filtered.length === 0) {
        container.innerHTML = '<p>Nessun tutor trovato con i filtri selezionati.</p>';
        return;
    }

    filtered.forEach(tutor => {
        const card = document.createElement('div');
        card.className = 'tutor-card';
        
        const subs = allSubjectsMapping[tutor.matricolaP] || [];
        const subjectsHtml = subs.map(s => `<span>${s}</span>`).join('');
        
        const descriptionHtml = tutor.descrizione ? tutor.descrizione.replace(/\n/g, '<br>') : '<i>Nessuna descrizione impostata.</i>';
        
        card.innerHTML = `
            <h3>${tutor.nome} ${tutor.cognome}</h3>
            <div><strong>Classe:</strong> ${tutor.classe || ''}</div>
            <div class="tutor-subjects" style="margin-top: 10px;">
                ${subjectsHtml || '<i>Nessuna materia registrata</i>'}
            </div>
            <div class="tutor-desc">
                ${descriptionHtml}
            </div>
            <a href="/tutee/prenota?tutor=${tutor.matricolaP}" class="prenota-btn">Prenota</a>
        `;
        container.appendChild(card);
    });
}
