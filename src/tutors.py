"""
tutors.py
Blueprint per la gestione dei tutor (Peer).
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required

from db import get_db
from mail_utils import send_email, get_destinatari

tutors_bp = Blueprint('tutors', __name__)


# ------------------------------------------------------------------------------
# Helper interni

def _notice_tutees(matricola):
    """Avvisa via email i tutee le cui lezioni future vengono rimosse."""
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT DISTINCT matricolaT FROM Lezioni WHERE matricolaP = %s AND data >= CURDATE()",
            (matricola,)
        )
        tutees = cursor.fetchall()

        cursor.execute("SELECT nome, cognome, classe FROM Studenti WHERE matricola = %s", (matricola,))
        nome_cogn = cursor.fetchone()

        for tutee in tutees:
            destinatari = get_destinatari(tutee[0])
            send_email(destinatari, 'Lezione cancellata',
                       f'Tutte le lezioni del tutor {nome_cogn[0]} {nome_cogn[1]} {nome_cogn[2]} sono state rimosse')

        # Copia in LezioniTutorRimossi
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Lezioni WHERE matricolaP = %s", (matricola,))
        lezioni = cursor.fetchall()

        for lezione in lezioni:
            cursor.execute(
                """INSERT INTO LezioniTutorRimossi
                   (matricolaP, data, ora, matricolaT, materiaL, argomenti, validata, aulaL)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (lezione['matricolaP'], lezione['data'], lezione['ora'],
                 lezione['matricolaT'], lezione['materiaL'], lezione['argomenti'],
                 lezione['validata'], lezione['aulaL'])
            )
            db.cursor().connection.commit()

        cursor.execute("DELETE FROM Lezioni WHERE matricolaT = %s AND data >= CURDATE()", (matricola,))
        db.commit()

    except Exception as e:
        print(f"An error occurred in _notice_tutees: {e}")


def _delete_tutor_lessons(matricola):
    """Sposta tutte le lezioni del tutor in LezioniTutorRimossi e le cancella."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM Lezioni WHERE matricolaP = %s", (matricola,))
        lezioni = cursor.fetchall()

        for lezione in lezioni:
            cursor.execute(
                """INSERT INTO LezioniTutorRimossi
                   (matricolaP, data, ora, matricolaT, materiaL, argomenti)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (lezione['matricolaP'], lezione['data'], lezione['ora'],
                 lezione['matricolaT'], lezione['materiaL'], lezione['argomenti'])
            )
            db.commit()

        cursor.execute("DELETE FROM Lezioni WHERE matricolaP = %s", (matricola,))
        db.commit()

    except Exception as e:
        print(f"An error occurred in _delete_tutor_lessons: {e}")


# ------------------------------------------------------------------------------
# Routes

@tutors_bp.route("/tutors", methods=["GET"])
@login_required
def get_tutors():
    """Restituisce la lista di tutti i tutor."""
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT P.matricolaP, S.nome, S.cognome, S.classe
            FROM Peer P, Studenti S
            WHERE P.matricolaP = S.matricola
            ORDER BY S.classe
        """)
        return jsonify(cursor.fetchall()), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@tutors_bp.route("/tutors", methods=["POST"])
@login_required
def add_tutor():
    """Aggiunge un tutor (solo admin)."""
    if session["tipo"] != "docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricola = request.json.get('matricola')
    if not matricola:
        return jsonify({"error": "Attributes are required"}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT 1 FROM Studenti WHERE matricola = %s", (matricola,))
        if cursor.fetchone() is None:
            return jsonify({"message": "Matricola non esistente"}), 200

        cursor.execute("SELECT 1 FROM Peer WHERE matricolaP = %s", (matricola,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO Peer (matricolaP) VALUES (%s)", (matricola,))
            db.commit()
            return jsonify({"message": "Tutor aggiunto con successo"}), 200
        else:
            return jsonify({"message": "Tutor già presente"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@tutors_bp.route("/tutors/", methods=["DELETE"])
@login_required
def delete_tutor():
    """Rimuove un tutor e le sue lezioni (solo admin)."""
    if session["tipo"] != "docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricola = request.json.get('matricola')
    if not matricola:
        return jsonify({"error": "Attributes are required"}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM Peer WHERE matricolaP = %s", (matricola,))
        db.commit()

        _notice_tutees(matricola)
        _delete_tutor_lessons(matricola)

        return jsonify({"message": "Tutor deleted successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@tutors_bp.route('/lezioni_cancellate/<matricolaP>/<distLezione>/<prenotata>', methods=["GET"])
@login_required
def get_lezioni_cancellate(matricolaP, distLezione, prenotata):
    """Restituisce le lezioni cancellate di un tutor (solo admin)."""
    if session["tipo"] != "docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    if matricolaP is None:
        return jsonify({"error": "Attributi mancanti: matricolaP"}), 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        where_statement = ""
        parameters = []

        if prenotata is not None:
            if prenotata:
                where_statement += "matricolaT IS NOT NULL AND "
        elif distLezione is not None:
            where_statement += "DATEDIFF(data, deleteDateTime) >= %s AND "
            parameters.append(distLezione)

        where_statement += "matricolaP = %s"
        parameters.append(matricolaP)

        cursor.execute(f"SELECT * FROM LezioniCancellate WHERE {where_statement}", parameters)
        return jsonify(cursor.fetchall()), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
