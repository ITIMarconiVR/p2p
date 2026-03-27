# ─── Stage: immagine base Python 3.11.8 slim ───────────────────────────────────
# Usiamo la variante slim per ridurre la dimensione dell'immagine.
# Installiamo le librerie di sistema necessarie per compilare i driver C di MySQL
# (mysql-connector-python in alcune versioni richiede pkg-config e libmysqlclient-dev).
FROM python:3.11.8-slim

# ─── Variabili d'ambiente di sistema ──────────────────────────────────────────
# PYTHONDONTWRITEBYTECODE: evita la creazione di file .pyc
# PYTHONUNBUFFERED: output stdout/stderr non bufferizzato (log in tempo reale)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# ─── Directory di lavoro all'interno del container ────────────────────────────
WORKDIR /app

# ─── Dipendenze di sistema ────────────────────────────────────────────────────
# default-libmysqlclient-dev e pkg-config servono a compilare eventuali
# dipendenze C di mysql-connector-python.
# gcc è il compilatore richiesto da alcune wheel pure-Python con estensioni C.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
 && rm -rf /var/lib/apt/lists/*

# ─── Installazione delle dipendenze Python ────────────────────────────────────
# Copiamo solo il file dei requirements prima del resto del codice sorgente
# per sfruttare la cache dei layer Docker: i pacchetti vengono reinstallati
# solo se requirements.txt cambia.
COPY DOC/requirementPy.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ─── Codice sorgente ──────────────────────────────────────────────────────────
# In sviluppo questo layer viene sovrascritto dal bind mount definito
# in docker-compose.yml; serve però per costruire l'immagine in modo autonomo.
COPY src/ ./src/
COPY static/ ./static/

# ─── Porta esposta dall'applicazione ─────────────────────────────────────────
EXPOSE 8010

# ─── Comando di avvio ─────────────────────────────────────────────────────────
# app.py usa ssl_context="adhoc" (pyOpenSSL), quindi lanciamo direttamente
# python app.py dalla directory src/.
CMD ["python", "src/app.py"]
