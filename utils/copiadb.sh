#!/bin/bash

# ==========================================
# Configurazione Database Sorgente
# ==========================================
SRC_HOST="172.16.1.98"
SRC_USER="p2p"
SRC_PASS="p2p2025"
SRC_DB="p2p"

# ==========================================
# Configurazione Database Destinazione
# ==========================================
DST_HOST="172.16.1.98"
DST_USER="p2p"
DST_PASS="p2p2025"
DST_DB="p2pdev"

echo "Inizio la copia dei dati da $SRC_HOST ($SRC_DB) a $DST_HOST ($DST_DB)..."

# Esecuzione del dump e importazione diretta tramite pipe
# --no-create-info: evita di esportare le istruzioni CREATE TABLE
# --single-transaction: garantisce un dump coerente per tabelle InnoDB
# --quick: utile per tabelle di grandi dimensioni

mysqldump  -u "$SRC_USER" -p"$SRC_PASS" \
  --no-create-info \
  --single-transaction \
  --quick \
  --no-tablespaces \
  -c \
  "$SRC_DB" > dump



echo "Inizio lo svuotamento delle tabelle nel database '$DST_DB' su $DST_HOST..."


mysql -h "$DST_HOST" -P13306 -u "$DST_USER" -p"$DST_PASS" "$DST_DB" <zap
echo "Inizio il travaso  tabelle nel database '$DST_DB' su $DST_HOST..."


mysql -h "$DST_HOST" -P13306 -u "$DST_USER" -p"$DST_PASS" "$DST_DB" <dump

exit

