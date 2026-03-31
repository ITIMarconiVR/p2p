"""
lezioni.py
Blueprint per la gestione delle lezioni (disponibilità, prenotazioni, validazione, cancellazioni).
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required
from markupsafe import escape

from db import get_db
from mail_utils import send_email, get_destinatari
from GoogleCalendarManager import GoogleCalendarManager

lezioni_bp = Blueprint('lezioni', __name__)


# ------------------------------------------------------------------------------
# Helper – stato del servizio

def _is_servizio_attivo():
    """Restituisce True se il servizio P2P è abilitato (valore DB = '1')."""
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT valore FROM ConfigurazioneServizio WHERE chiave = 'servizio_attivo'")
        row = cursor.fetchone()
        return row is not None and row[0] == '1'
    except Exception:
        # In caso di errore DB, considera il servizio attivo per non bloccare tutto
        return True


# ------------------------------------------------------------------------------
# Stato e toggle del servizio (solo admin)

@lezioni_bp.route("/servizio_stato", methods=["GET"])
@login_required
def servizio_stato():
    """Restituisce lo stato attuale del servizio P2P."""
    return jsonify({"attivo": _is_servizio_attivo()}), 200


@lezioni_bp.route("/servizio_toggle", methods=["POST"])
@login_required
def servizio_toggle():
    """Inverte lo stato del servizio P2P. Solo admin (tipo = 'docente')."""
    from flask import session
    if session.get("tipo") != "docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE ConfigurazioneServizio "
            "SET valore = CASE WHEN valore = '1' THEN '0' ELSE '1' END "
            "WHERE chiave = 'servizio_attivo'"
        )
        db.commit()
        nuovo_stato = _is_servizio_attivo()
        return jsonify({"attivo": nuovo_stato}), 200
    except Exception as e:
        print(f"Toggle servizio error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Disponibilità tutor

@lezioni_bp.route("/add_event", methods=["POST"])
@login_required
def add_event():
    """Il tutor aggiunge una disponibilità di lezione."""
    if not request.json or 'matricolaP' not in request.json or \
       'data' not in request.json or 'ora' not in request.json:
        return jsonify({"error": "Attributi mancanti"}), 400

    if session["mail"][:5] != request.json['matricolaP'] or session["tipo"] != "tutor":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricola = request.json['matricolaP']
    data = request.json['data']
    ora = request.json['ora']

    if not matricola or not data or not ora or \
       matricola == "null" or data == "null" or ora == "null":
        return jsonify({"error": "Attributi vuoti"}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        # Massimo una lezione al giorno per tutor
        cursor.execute(
            "SELECT 1 FROM Lezioni WHERE matricolaP = %s AND data = %s",
            (matricola, data)
        )
        if cursor.fetchone() is not None:
            return jsonify({"message": "Puoi fare una lezione al giorno"})

        cursor.execute(
            "INSERT INTO Lezioni (matricolaP, data, ora) VALUES (%s, %s, %s)",
            (matricola, data, ora)
        )
        db.commit()
        return jsonify({"message": "Event added successfully"}), 201

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Prenotazione

@lezioni_bp.route("/prenota", methods=["POST"])
@login_required
def reserve_event():
    """Il tutee prenota una lezione."""
    if session["tipo"] == "tutor" and session["abilitato"] == 0:
        return "Non sei autorizzato causa mancato pagamento del contributo volontario", 401

    matricolaP = request.json.get('matricolaP')
    ora = request.json.get('ora')
    data = request.json.get('data')
    matricolaT = request.json.get('matricolaT')
    materiaL = request.json.get('materiaL')
    argomenti = str(escape(request.json.get('argomenti', '')))

    if not all([matricolaP, ora, data, matricolaT, materiaL, argomenti]):
        return jsonify({"error": "Attributes are required"}), 400

    if matricolaT != session["mail"][:5]:
        return jsonify({"error": "not allowed"})

    try:
        db = get_db()
        cursor = db.cursor()

        # Un tutee non può prenotare più di una lezione al giorno
        cursor.execute(
            "SELECT 1 FROM Lezioni WHERE matricolaT = %s AND data = %s",
            (matricolaT, data)
        )
        if cursor.fetchone() is not None:
            return jsonify({"error": "Puoi fare una lezione al giorno"})

        cursor.execute("""
            UPDATE Lezioni
            SET matricolaT = %s, materiaL = %s, argomenti = %s
            WHERE matricolaP = %s AND ora = %s AND data = %s
              AND data >= DATE_ADD(CURDATE(), INTERVAL 1 DAY)
        """, (matricolaT, materiaL, argomenti, matricolaP, ora, data))

        # Crea evento Google Calendar se token disponibile
        if cursor.rowcount > 0 and 'google_token' in session:
            try:
                calendar_manager = GoogleCalendarManager(session['google_token'])
                event_details = {
                    'data': data, 'ora': ora, 'materiaL': materiaL,
                    'argomenti': argomenti, 'matricolaT': matricolaT,
                    'matricolaP': matricolaP, 'aulaL': None
                }
                success, calendar_id = calendar_manager.create_lesson_event(event_details)
                if success:
                    cursor.execute("""
                        UPDATE Lezioni
                        SET google_calendar_id = %s
                        WHERE matricolaP = %s AND ora = %s AND data = %s
                    """, (calendar_id, matricolaP, ora, data))
            except Exception as e:
                print(f"Calendar error: {e}")

        db.commit()

        # Notifica via mail
        query_nome = "SELECT nome, cognome, classe FROM Studenti WHERE matricola = %s"
        cursor.execute(query_nome, (matricolaP,))
        nome_cognP = cursor.fetchone()
        cursor.execute(query_nome, (matricolaT,))
        nome_cognT = cursor.fetchone()

        dest = get_destinatari(matricolaP)
        if matricolaT is not None:
            for des in get_destinatari(matricolaT):
                dest.append(des)

        ora_str = "13:40" if ora == 1 else "14:30" if ora == 2 else ora
        message = (f"La lezione del giorno {data} alle ore {ora_str} "
                   f"con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} "
                   f"è stata prenotata dal tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]}."
                   f"\nMateria: {materiaL}\nArgomenti: {argomenti}"
                   f"\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.")
        send_email(dest, "Lezione prenotata", message)

        return jsonify({"message": "Event reserved successfully"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Lettura

@lezioni_bp.route("/lezioni", methods=["GET"])
@login_required
def get_lezioni():
    """Restituisce le lezioni filtrate per i parametri passati via query string."""
    matricolaP = request.args.get('matricolaP')
    matricolaT = request.args.get('matricolaT')
    data = request.args.get('data')
    ora = request.args.get('ora')
    materiaL = request.args.get('materiaL')
    validata = request.args.get('validata')
    aulaL = request.args.get('aulaL')

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        where = "WHERE "
        campi = []

        if matricolaT is not None:
            if matricolaT == "NULL":
                where += "matricolaT IS NULL AND "
            elif matricolaT == "%":
                where += "matricolaT LIKE %s AND "
                campi.append(matricolaT)
            else:
                where += "matricolaT = %s AND "
                campi.append(matricolaT)
        if matricolaP is not None:
            where += "matricolaP = %s AND "
            campi.append(matricolaP)
        if data is not None:
            where += "data = %s AND "
            campi.append(data)
        if ora is not None:
            where += "ora = %s AND "
            campi.append(ora)
        if materiaL is not None:
            where += "materiaL = %s AND "
            campi.append(materiaL)
        if validata is not None:
            where += "validata = %s AND "
            campi.append(validata)
        if aulaL is not None:
            where += "aulaL = %s AND "
            campi.append(aulaL)

        where = "" if where == "WHERE " else where[:-5]
        cursor.execute("SELECT * FROM Lezioni " + where, campi)
        return jsonify(cursor.fetchall()), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lezioni_bp.route("/lezioni2", methods=["GET"])
@login_required
def get_lezioni2():
    """Restituisce lezioni con dati anagrafici di tutor e tutee (JOIN su Studenti)."""
    try:
        query_params = {
            "matricolaP": request.args.get("matricolaP"),
            "matricolaT": request.args.get("matricolaT"),
            "data": request.args.get("data"),
            "ora": request.args.get("ora"),
            "materiaL": request.args.get("materiaL"),
            "validata": request.args.get("validata"),
            "aulaL": request.args.get("aulaL"),
        }

        db = get_db()
        cursor = db.cursor(dictionary=True)

        where_clauses = []
        values = []

        for field, value in query_params.items():
            if value is not None:
                if field == "matricolaT":
                    if value == "%":
                        where_clauses.append("matricolaT LIKE %s")
                        values.append(value)
                    else:
                        where_clauses.append("matricolaT = %s")
                        values.append(value)
                else:
                    where_clauses.append(f"{field} = %s")
                    values.append(value)

        where_statement = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        cursor.execute(f"""
            SELECT L.*, S1.nome nomeP, S1.cognome cognomeP, S1.classe classeP,
                   S2.nome nomeT, S2.cognome cognomeT, S2.classe classeT
            FROM Lezioni AS L
            JOIN Studenti S1 ON L.matricolaP = S1.matricola
            LEFT JOIN Studenti S2 ON L.matricolaT = S2.matricola
            {where_statement}
        """, values)
        return jsonify(cursor.fetchall()), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lezioni_bp.route("/lezioniFilter", methods=["GET"])
@login_required
def get_lezioni_per_materia():
    """Filtra le lezioni disponibili per materia, anno e indirizzo."""
    idMat = request.args.get('idMat')
    anno = request.args.get('anno')
    indirizzo = request.args.get('indirizzo')
    matricolaP = request.args.get('matricolaP')

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if idMat is None and anno is None and indirizzo is None:
            idMat = anno = indirizzo = "ALL"

        if idMat == 'ALL':
            idMat = "%"
        else:
            idMat = idMat.upper()
        anno = '_' if anno == 'ALL' else anno.upper()
        indirizzo = "_" if indirizzo == 'ALL' else indirizzo.upper()[0]
        if matricolaP == 'ALL':
            matricolaP = "%"

        cursor.execute("""
            SELECT DISTINCT L.*, S1.nome nomeP, S1.cognome cognomeP, S1.classe classeP
            FROM MaterieInsegnate MI, Lezioni L, Studenti S1
            WHERE MI.matricola = L.matricolaP
              AND S1.matricola = L.matricolaP
              AND L.matricolaP LIKE %s
              AND L.matricolaT IS NULL
              AND L.validata = 1
              AND MI.idMat LIKE %s
              AND S1.classe LIKE %s
              AND S1.classe LIKE %s
        """, ('%' + matricolaP + '%', idMat, '%' + anno + '%', '%' + indirizzo + '%'))
        return jsonify(cursor.fetchall()), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Validazione

@lezioni_bp.route("/lezioni", methods=["POST"])
@login_required
def valida_lezione():
    """Valida una singola lezione (solo admin)."""
    if session["tipo"] != "docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricolaP = request.json.get('matricolaP')
    ora = request.json.get('ora')
    data = request.json.get('data')

    if not all([matricolaP, ora, data]):
        return jsonify({"error": "Attributes are required"}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Lezioni SET validata = 1
            WHERE matricolaP = %s AND ora = %s AND data = %s
        """, (matricolaP, ora, data))
        db.commit()
        return jsonify({"message": "Event validated successfully"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@lezioni_bp.route("/valida_tutto", methods=["POST"])
@login_required
def valida_tutto():
    """Valida tutte le lezioni future ancora non validate (solo admin)."""
    if session["tipo"] != "docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Lezioni SET validata = 1
            WHERE data >= CURDATE() AND validata = 0
        """)
        db.commit()
        return jsonify({"message": "Event validated successfully"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Cancellazione lezione (generica – da tutee o dal pannello admin)

@lezioni_bp.route("/lezioni", methods=["DELETE"])
@login_required
def delete_lezione():
    """
    Cancella o de-prenota una lezione.
    1> da tutee
    2> da tutor con tutee presente
    3> da tutor senza prenotazioni
    """

    matricolaT = request.json.get('matricolaT')
    matricolaP = request.json.get('matricolaP')
    data = request.json.get('data')
    ora = request.json.get('ora')
    deleter = request.json.get('deleter')
    matricolaD = deleter

    if not all([matricolaP, data, ora, deleter]):
        return jsonify({"error": "Attributes are required"}), 400

    if deleter != session['mail'][:5]:
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()

        query_nome = "SELECT nome, cognome, classe FROM Studenti WHERE matricola = %s"
        cursor.execute(query_nome, (matricolaP,))
        nome_cognP = cursor.fetchone()

        if matricolaT is not None:
            cursor.execute(query_nome, (matricolaT,))
            nome_cognT = cursor.fetchone()
            if deleter == matricolaT:
                deleter = nome_cognT
            elif deleter == matricolaP:
                deleter = nome_cognP

        if matricolaT is not None:
            cursor.execute("""
                UPDATE Lezioni SET matricolaT = NULL
                WHERE matricolaT = %s AND data = %s AND ora = %s AND DATE(data) >= CURDATE()
            """, (matricolaT, data, ora))
            db.commit()

        if matricolaD == matricolaP:
            cursor.execute("""
                DELETE FROM Lezioni
                WHERE matricolaP = %s AND data = %s AND ora = %s AND DATE(data) > CURDATE()
            """, (matricolaP, data, ora))
            db.commit()

        dest = get_destinatari(matricolaP)
        if matricolaT is not None:
            for des in get_destinatari(matricolaT):
                dest.append(des)

        ora_str = "13:40" if ora == 1 else "14:30" if ora == 2 else ora

        if matricolaT is not None:
            message = (f"La lezione del giorno {data} alle ore {ora_str} "
                       f"con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} "
                       f"e tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]} "
                       f"è stata annullata da {deleter[0]} {deleter[1]}."
                       f"\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.")
        else:
            message = (f"La lezione del giorno {data} alle ore {ora_str} "
                       f"con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} "
                       f"è stata annullata da {deleter[0]} {deleter[1]} {deleter[2]}."
                       f"\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.")
        send_email(dest, "Lezione cancellata", message)

        return jsonify({'message': 'Lezione rimossa con successo'})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Cancellazione da tutor

@lezioni_bp.route("/delete_lezione_tutor", methods=["DELETE"])
@login_required
def delete_lezione_tutor():
    """Cancella una lezione su iniziativa del tutor."""
    matricolaT = request.json.get('matricolaT')
    matricolaP = request.json.get('matricolaP')
    data = request.json.get('data')
    ora = request.json.get('ora')

    if not all([matricolaP, data, ora]):
        return jsonify({"error": "Attributes are required"}), 400
    if matricolaP != session["mail"][:5]:
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()

        query_nome = "SELECT nome, cognome, classe FROM Studenti WHERE matricola = %s"
        cursor.execute(query_nome, (matricolaP,))
        nome_cognP = cursor.fetchone()
        nome_cognT = None
        if matricolaT is not None:
            cursor.execute(query_nome, (matricolaT,))
            nome_cognT = cursor.fetchone()

        # Recupera e cancella evento Google Calendar
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT google_calendar_id FROM Lezioni
            WHERE matricolaP = %s AND data = %s AND ora = %s
        """, (matricolaP, data, ora))
        result = cursor.fetchone()
        if result and result['google_calendar_id'] and 'google_token' in session:
            GoogleCalendarManager(session['google_token']).delete_event(result['google_calendar_id'])

        # Archivia in LezioniCancellate
        cursor.execute("SELECT * FROM Lezioni WHERE matricolaP = %s AND data = %s AND ora = %s",
                       (matricolaP, data, ora))
        lezione = cursor.fetchone()
        cursor.execute("""
            INSERT INTO LezioniCancellate
                (matricolaP, data, ora, matricolaT, materiaL, argomenti, validata, aulaL, svolta, deleter)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (lezione['matricolaP'], lezione['data'], lezione['ora'], lezione['matricolaT'],
              lezione['materiaL'], lezione['argomenti'], lezione['validata'],
              lezione['aulaL'], lezione['svolta'], matricolaP))
        db.commit()

        # Rimuovi da Lezioni
        cursor = db.cursor()
        cursor.execute("""
            DELETE FROM Lezioni
            WHERE matricolaP = %s AND data = %s AND ora = %s AND DATE(data) > CURDATE()
        """, (matricolaP, data, ora))
        db.commit()

        # Notifica
        dest = get_destinatari(matricolaP)
        if matricolaT is not None:
            for des in get_destinatari(matricolaT):
                dest.append(des)

        ora_str = "13:40" if ora == 1 else "14:30" if ora == 2 else ora

        if matricolaT is not None and nome_cognT is not None:
            message = (f"La lezione del giorno {data} alle ore {ora_str} "
                       f"con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} "
                       f"e tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]} "
                       f"è stata annullata da {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]}."
                       f"\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.")
        else:
            message = (f"La lezione del giorno {data} alle ore {ora_str} "
                       f"con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} "
                       f"è stata annullata da {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]}."
                       f"\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.")
        send_email(dest, "Lezione cancellata", message)

        return jsonify({'message': 'Lezione rimossa con successo'})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# Cancellazione da tutee

@lezioni_bp.route("/delete_lezione_tutee", methods=["DELETE"])
@login_required
def delete_lezione_tutee():
    """Il tutee rinuncia alla propria prenotazione."""
    matricolaT = request.json.get('matricolaT')
    matricolaP = request.json.get('matricolaP')
    data = request.json.get('data')
    ora = request.json.get('ora')

    if not all([matricolaP, data, ora, matricolaT]):
        return jsonify({"error": "Attributes are required"}), 400
    if matricolaT != session["mail"][:5]:
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()

        # Recupera e cancella evento Google Calendar
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT google_calendar_id FROM Lezioni
            WHERE matricolaP = %s AND data = %s AND ora = %s
        """, (matricolaP, data, ora))
        cal_result = cursor.fetchone()
        if cal_result and cal_result['google_calendar_id'] and 'google_token' in session:
            try:
                GoogleCalendarManager(session['google_token']).delete_event(cal_result['google_calendar_id'])
            except Exception as e:
                print(f"Calendar deletion error: {e}")

        # Nomi tutor e tutee
        cursor = db.cursor()
        query_nome = "SELECT nome, cognome, classe FROM Studenti WHERE matricola = %s"
        cursor.execute(query_nome, (matricolaP,))
        nome_cognP = cursor.fetchone()
        cursor.execute(query_nome, (matricolaT,))
        nome_cognT = cursor.fetchone()

        # Archivia in LezioniCancellate
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Lezioni WHERE matricolaP = %s AND data = %s AND ora = %s",
                       (matricolaP, data, ora))
        lezione = cursor.fetchone()
        cursor.execute("""
            INSERT INTO LezioniCancellate
                (matricolaP, data, ora, matricolaT, materiaL, argomenti, validata, aulaL, svolta, deleter)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (lezione['matricolaP'], lezione['data'], lezione['ora'], lezione['matricolaT'],
              lezione['materiaL'], lezione['argomenti'], lezione['validata'],
              lezione['aulaL'], lezione['svolta'], matricolaT))
        db.commit()

        # Azzera la prenotazione (non cancella la disponibilità)
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Lezioni
            SET matricolaT = NULL, materiaL = NULL, argomenti = NULL,
                aulaL = NULL, google_calendar_id = NULL
            WHERE matricolaT = %s AND data = %s AND ora = %s AND DATE(data) >= CURDATE()
        """, (matricolaT, data, ora))
        db.commit()

        # Notifica
        dest = get_destinatari(matricolaP)
        for des in get_destinatari(matricolaT):
            dest.append(des)

        ora_str = "13:40" if ora == 1 else "14:30" if ora == 2 else ora
        message = (f"La lezione del giorno {data} alle ore {ora_str} "
                   f"con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} "
                   f"e tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]} "
                   f"è stata annullata da {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]}."
                   f"\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.")
        send_email(dest, "Lezione cancellata", message)

        return jsonify({'message': 'Lezione rimossa con successo'})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
