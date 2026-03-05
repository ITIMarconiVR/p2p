"""
users.py
Blueprint per la gestione degli utenti/studenti.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user

from db import get_db

users_bp = Blueprint('users', __name__)


@users_bp.route("/userInfo", methods=["GET"])
@login_required
def get_user_info():
    """Restituisce le variabili di sessione dell'utente corrente."""
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401
    return jsonify(session), 200


@users_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    """
    Ritorna uno studente o la lista di tutti gli studenti.
    Parametri query:
        matricola -> dati completi dello studente indicato
        (nessuno) -> matricola, nome, cognome, classe di tutti
    """
    try:
        matricola = request.args.get('matricola')
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if matricola is not None:
            if session["mail"][:5] != matricola:
                return jsonify({"error": "non allowed"})
            cursor.execute("SELECT * FROM Studenti WHERE matricola = %s", (matricola,))
            user = cursor.fetchone()
            return jsonify(user), 200

        cursor.execute("SELECT matricola, nome, cognome, classe FROM Studenti")
        users = cursor.fetchall()
        return jsonify(users), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
