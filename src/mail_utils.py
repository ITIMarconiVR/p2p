"""
mail_utils.py
Utility per l'invio di email e il calcolo dei destinatari.
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import jsonify
from flask_mail import Message

from db import get_db
from config import mail, resp_mail


def send_email(recipients, subject, message):
    """
    Invia una email a tutti i destinatari indicati.
    Aggiunge sempre resp_mail in copia.
    PRIMA dell'invio, crea notifiche interne per gli utenti del sistema.
    In caso di errore nell'invio email, notifica gli admin.
    """
    if not all([recipients, message]):
        return jsonify({"error": "All fields are required"}), 400

    # --- 1. Crea notifiche interne PRIMA dell'invio email ---
    # Rimuovi la frase "no-reply" dal corpo della notifica
    corpo_notifica = message.replace(
        "\n\nQuesta è un'email generata automaticamente, si prega di non rispondere.", ""
    )

    try:
        from notifiche import crea_notifica
        db = get_db()
        cursor = db.cursor(dictionary=True)

        for dest in recipients:
            # Salta resp_mail: le notifiche normali non vanno al responsabile
            if dest == resp_mail:
                continue

            # Verifica se il destinatario è un utente del sistema (studente)
            cursor.execute(
                "SELECT email FROM Studenti WHERE email = %s",
                (dest,)
            )
            if cursor.fetchone():
                crea_notifica(dest, subject, corpo_notifica)
            else:
                # Verifica se è un admin/centralino (docenti hanno email nel sistema)
                from config import admins, centraline
                if dest in admins or dest in centraline:
                    crea_notifica(dest, subject, corpo_notifica)

    except Exception as e:
        print(f"Errore creazione notifiche interne: {e}")
        # Non bloccare: le notifiche sono un bonus, l'email deve partire comunque

    # --- 2. Invio email ---
    try:
        recipients.append(resp_mail)
        for des in recipients:
            msg = Message(subject, recipients=[des])
            msg.body = message
            mail.send(msg)

        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")

        # --- 3. Notifica errore invio email a tutti gli admin ---
        try:
            from notifiche import crea_notifica
            from config import admins
            titolo_errore = "Errore invio email"
            corpo_errore = (
                f"L'invio dell'email con oggetto \"{subject}\" "
                f"ai destinatari {', '.join(recipients)} è fallito.\n\n"
                f"Errore: {e}"
            )
            for admin_email in admins:
                crea_notifica(admin_email, titolo_errore, corpo_errore)
        except Exception as notify_err:
            print(f"Errore anche nella notifica admin: {notify_err}")

        return jsonify({"error": "Internal server error"}), 500


def get_destinatari(matricola):
    """
    Ritorna la lista di indirizzi email a cui inviare notifiche per lo studente
    con la matricola indicata. Se è minorenne include i genitori.
    """
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT *
            FROM Studenti
            WHERE matricola = %s
        """
        cursor.execute(query, (matricola,))
        user = cursor.fetchone()

        if not user:
            return []

        destinatari = []

        # Parse data di nascita in formato DD/MM/YYYY
        year = user['data_nascita'][6:]
        month = user['data_nascita'][3:5]
        day = user['data_nascita'][:2]

        birth_date = datetime(int(year), int(month), int(day)).date()
        today = datetime.now().date()

        # Se minorenne aggiungi genitori
        if relativedelta(today, birth_date).years < 18:
            if user['emailgenitore1'] == user['emailgenitore2']:
                if user['emailgenitore1']:
                    destinatari.append(user['emailgenitore1'])
            else:
                if user['emailgenitore1']:
                    destinatari.append(user['emailgenitore1'])
                if user['emailgenitore2']:
                    destinatari.append(user['emailgenitore2'])

        if user['email']:
            destinatari.append(user['email'])

        return destinatari

    except Exception as e:
        print("error:", e)
        return []
