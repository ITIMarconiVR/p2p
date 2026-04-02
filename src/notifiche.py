"""
notifiche.py
Blueprint per il sistema di notifiche interne.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required

from db import get_db

notifiche_bp = Blueprint('notifiche', __name__)


# ------------------------------------------------------------------------------
# Helper – creazione notifica (usato da mail_utils.py e altri moduli)

def crea_notifica(destinatario_email, titolo, corpo):
    """
    Crea una notifica interna nel database.
    Può essere chiamata anche fuori dal contesto di una request Flask
    (usa la connessione DB dal contesto applicativo g).
    """
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """INSERT INTO Notifiche (titolo, corpo, destinatario)
               VALUES (%s, %s, %s)""",
            (titolo, corpo, destinatario_email)
        )
        db.commit()
    except Exception as e:
        print(f"Errore creazione notifica: {e}")


# ------------------------------------------------------------------------------
# API Routes

@notifiche_bp.route("/notifiche/count", methods=["GET"])
@login_required
def count_notifiche():
    """Restituisce il conteggio delle notifiche non lette per l'utente corrente."""
    try:
        email = session.get("mail")
        if not email:
            return jsonify({"count": 0}), 200

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM Notifiche WHERE destinatario = %s AND letta = 0",
            (email,)
        )
        count = cursor.fetchone()[0]
        return jsonify({"count": count}), 200

    except Exception as e:
        print(f"Errore count notifiche: {e}")
        return jsonify({"count": 0}), 200


@notifiche_bp.route("/notifiche", methods=["GET"])
@login_required
def get_notifiche():
    """Restituisce tutte le notifiche dell'utente corrente, ordinate dalla più recente."""
    try:
        email = session.get("mail")
        if not email:
            return jsonify([]), 200

        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """SELECT id, titolo, corpo, data_ora, letta
               FROM Notifiche
               WHERE destinatario = %s
               ORDER BY data_ora DESC""",
            (email,)
        )
        notifiche = cursor.fetchall()
        return jsonify(notifiche), 200

    except Exception as e:
        print(f"Errore get notifiche: {e}")
        return jsonify({"error": "Internal server error"}), 500


@notifiche_bp.route("/notifiche/<int:notifica_id>/letta", methods=["POST"])
@login_required
def segna_letta(notifica_id):
    """Segna una notifica come letta. Solo il proprietario può farlo."""
    try:
        email = session.get("mail")
        if not email:
            return jsonify({"error": "Non autenticato"}), 401

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """UPDATE Notifiche SET letta = 1
               WHERE id = %s AND destinatario = %s""",
            (notifica_id, email)
        )
        db.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Notifica non trovata"}), 404

        return jsonify({"message": "Notifica segnata come letta"}), 200

    except Exception as e:
        print(f"Errore segna letta: {e}")
        return jsonify({"error": "Internal server error"}), 500


@notifiche_bp.route("/notifiche/segna_tutte_lette", methods=["POST"])
@login_required
def segna_tutte_lette():
    """Segna tutte le notifiche dell'utente corrente come lette."""
    try:
        email = session.get("mail")
        if not email:
            return jsonify({"error": "Non autenticato"}), 401

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE Notifiche SET letta = 1 WHERE destinatario = %s AND letta = 0",
            (email,)
        )
        db.commit()
        return jsonify({"message": f"{cursor.rowcount} notifiche segnate come lette"}), 200

    except Exception as e:
        print(f"Errore segna tutte lette: {e}")
        return jsonify({"error": "Internal server error"}), 500
