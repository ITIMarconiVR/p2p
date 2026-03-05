"""
materie.py
Blueprint per la gestione delle materie insegnate dai tutor.
"""
from flask import Blueprint, request, jsonify, session
from flask_login import login_required

from db import get_db

materie_bp = Blueprint('materie', __name__)


@materie_bp.route("/materie", methods=["GET"])
@login_required
def get_materie():
    """
    Ritorna le materie.
    Parametri query:
        matricola -> materie insegnate dal tutor indicato
        (nessuno)  -> tutte le materie disponibili
    """
    matricola = request.args.get('matricola')
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if matricola is not None:
            cursor.execute(
                "SELECT idMat FROM MaterieInsegnate WHERE matricola = %s",
                (matricola,)
            )
            materie = cursor.fetchall()
            return jsonify([m['idMat'] for m in materie]), 200

        cursor.execute("SELECT idMat FROM Materie")
        return jsonify(cursor.fetchall()), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@materie_bp.route("/materie", methods=["POST"])
@login_required
def add_materia():
    """Aggiunge una materia insegnata a un tutor."""
    matricola = request.json.get('matricola')
    idMat = request.json.get('materia')

    if not matricola or not idMat:
        return jsonify({"error": "Attributes are required"}), 400

    if session["tipo"] != "tutor" or session["mail"][:5] != matricola:
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()
        idMat = idMat.upper()

        cursor.execute("SELECT * FROM Materie WHERE idMat = %s", (idMat,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Invalid materia"}), 400

        cursor.execute("INSERT INTO MaterieInsegnate (matricola, idMat) VALUES (%s, %s)", (matricola, idMat))
        db.commit()
        return jsonify({"message": "Materia added successfully"}), 201

    except Exception as e:
        print(f"An error occurred: {e}")
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Duplicate entry"}), 400
        return jsonify({"error": "Internal server error", "desc": str(e)}), 500


@materie_bp.route("/materie", methods=["DELETE"])
@login_required
def delete_materia():
    """Rimuove una materia insegnata da un tutor."""
    matricola = request.json.get('matricola')
    idMat = request.json.get('idMat')

    if not matricola or not idMat:
        return jsonify({"error": "Attributes are required"}), 400

    if session["tipo"] != "tutor" or session["mail"][:5] != matricola:
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM MaterieInsegnate WHERE matricola = %s AND idMat = %s",
            (matricola, idMat)
        )
        db.commit()
        return jsonify({"message": "Materia deleted successfully"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
