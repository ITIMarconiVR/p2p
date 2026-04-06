# P2P Tutoring Service

Il servizio P2P Tutoring è un'applicazione web sviluppata in Python (Flask) e supportata da un database MySQL, progettata per consentire la prenotazione, gestione e notifica di lezioni e tutoraggi scolastici. 

Questo progetto è interamente gestito attraverso architettura a container tramite **Docker** e **Docker Compose**. Questo approccio garantisce che l'applicazione giri sempre in un ambiente identico e controllato, eliminando problemi di dipendenze sul sistema ospite.

---

##  Architettura dei Container

Il progetto è suddiviso in due container principali, definiti nel `docker-compose.yml`:

1.  **`web` (Applicazione Flask)**:
    *   Basato sull'immagine Python 3.11 (slim) creata dal `Dockerfile`.
    *   Si occupa di tutta la logica di backend, l'esposizione delle API e lo smistamento dei template frontend.
    *   Monta in tempo reale la cartella `./src` e `./static` grazie ai volumi di Docker Compose. Modificare il codice Python, JS o CSS sul server si riflette immediatamente nel container (non serve riavviare).
    *   Espone il servizio sulla porta **8010**.

2.  **`db` (Database MySQL 8.0)**:
    *   Basato sull'immagine ufficiale `mysql:8.0`.
    *   Durante la prima esecuzione, esegue automaticamente lo schema SQL posto in `./DOC/db_struct.sql` per creare le tabelle e la struttura del database.
    *   Tutti i dati generati (prenotazioni, utenti, log) vengono salvati e resi persistenti attraverso il Docker Volume `mysql_data`.
    *   Espone il database sulla porta dell'host **13306** per eventuali esplorazioni esterne (tramite client SQL).

---

## Guida all'uso: comandi Docker Compose

Eseguire i seguenti comandi direttamente nella directory principale del progetto (dove si trova il file `docker-compose.yml`).

### `docker compose up`
Avvia tutti i container necessari. Consigliato per l'esecuzione standard in fase di sviluppo. Mostrerà nel terminale i log combinati del database e dell'app Flask.
* *Nota: premere `Ctrl+C` nel terminale per arrestarli dolcemente.*

### `docker compose up -d`
Avvia i container in modalità "Detached" (in background). Il terminale viene rilasciato e puoi continuare ad utilizzarlo.

### `docker compose up --build -d`
Riavvia i container **forzando il ricalcolo e la build dell'immagine Docker**. 
Usare questo comando, piuttosto del classico `up`, in due scenari:
1. È stato modificato il file `Dockerfile`.
2. È stato aggiunto/rimosso un pacchetto in `DOC/requirementPy.txt` (es. `pip install request`). Poiché l'ambiente di runtime è nel container, è necessario ricostruirlo affinché installi la nuova libreria.

### `docker compose down`
Stoppa i container in esecuzione e distrugge le reti interne create da Compose. I **dati all'interno del database vengono conservati**. Se si esegue un successivo `up`, si ritroveranno utenti e prenotazioni esattamente come li si erano lasciati.

### `docker compose down -v`
Stoppa i container e **distrugge i volumi nominati** (nello specifico, `mysql_data`).
Questo elimina fisicamente l'intero stato del database MySQL. È estremamente utile in fase di sviluppo se il database ha dati corrotti o se hai modificato il file schema `db_struct.sql` e vuoi forzare un soft-reset pulito delle tabelle. Al prossimo `up` il DB sarà ricreato da zero, completamente vuoto (popolato solo da ciò che è nel db_struct).

### `docker compose logs -f web`
Permette di visualizzare in tempo reale i log generati dall'applicazione Flask nel container web (particolarmente utile se si lancia l'app in modalità detached `-d`).

---

## Struttura del Progetto

```
.
├── DOC/                 # Documentazione varia, script SQL di base (db_struct.sql) e i requirements.txt
├── src/                 # Sorgenti Python backend (app.py, routes, classi) MONTATI in tempo reale su container
├── static/              # CSS, JS client-side MONTATI in tempo reale su docker
├── utils/               # Script per il db
├── Dockerfile           # File per la build dell'immagine Python App
├── docker-compose.yml   # L'infrastruttura as codice locale
└── README.md            # Questo file!
```

