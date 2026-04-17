"""
auth.py
Blueprint per l'autenticazione Google OAuth 2.0.
"""
import os
import requests

from flask import Blueprint, request, jsonify, redirect, session, url_for
from flask_login import login_user, logout_user, login_required

from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session

from db import get_db
from user import User
from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_DISCOVERY_URL,
    login_manager, admins, centraline
)

auth_bp = Blueprint('auth', __name__)


# ------------------------------------------------------------------------------
# Helper

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


# ------------------------------------------------------------------------------
# User loader (richiesto da Flask-Login)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


# ------------------------------------------------------------------------------
# Routes

@auth_bp.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    client = WebApplicationClient(GOOGLE_CLIENT_ID)

    state = os.urandom(16).hex()
    secure_base_url = request.base_url.replace("http://", "https://")

    request_uri = client.prepare_request_uri(
        authorization_endpoint,
#LLL 17/4/26        redirect_uri=request.base_url + "/callback",
        redirect_uri=secure_base_url+ "/callback",
        scope=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar"],
        state=state
    )

    session['oauth_state'] = state
    return redirect(request_uri)


@auth_bp.route("/login/callback")
def callback():
    if request.args.get("error"):
        error_reason = request.args.get("error")
        return f"Accesso negato o annullato ({error_reason}). I permessi richiesti sono obbligatori per l'utilizzo del servizio. <br><br> <a href='/login'>Riprova a fare il login</a>", 400

    code = request.args.get("code")
    if not code:
        return "Codice di autorizzazione mancante. <br><br> <a href='/login'>Riprova a fare il login</a>", 400

    state = request.args.get("state", default=None, type=None)
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Fissiamo i permessi OAUTHLIB per accettare http locale (se si va via nginx http)
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Dobbiamo garantire che gli URL di callback usino https come fatto nella route /login,
    # altrimenti OAuth disconoscerà e respingerà l'autorizzazione o lancia InsecureTransportError
    secure_redirect_uri = request.base_url.replace("http://", "https://")
    secure_auth_response = request.url.replace("http://", "https://")

    oauth_session = OAuth2Session(GOOGLE_CLIENT_ID, state=state, redirect_uri=secure_redirect_uri)
    oauth_session.fetch_token(token_endpoint, client_secret=GOOGLE_CLIENT_SECRET,
                              authorization_response=secure_auth_response)
    session['google_token'] = oauth_session.token

    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    response = oauth_session.get(user_info_url)
    userinfo_response = response.json() if response.status_code == 200 else None

    if userinfo_response.get("email_verified"):
        unique_id = userinfo_response["sub"]
        users_email = userinfo_response["email"]
        picture = userinfo_response["picture"]
        name = userinfo_response["name"]
    else:
        return "User email not available or not verified by Google.", 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM utentiws WHERE id = %s", (unique_id,))
        res = cursor.fetchone()
        if not res:
            cursor.execute(
                "INSERT INTO utentiws (id, name, email, profile_pic) VALUES (%s, %s, %s, %s)",
                (unique_id, name, users_email, picture)
            )
            db.commit()

        tipo = "docente"
        classe = ""
        abilitato = 0

        if users_email.lower().endswith("@studenti.marconiverona.edu.it"):
            cursor.execute("SELECT abilitato FROM Studenti WHERE email = %s", (users_email,))
            result = cursor.fetchone()
            if result["abilitato"] == 1:
                abilitato = True

            cursor.execute("SELECT 1 FROM Peer WHERE matricolaP = %s", (users_email[0:5],))
            result = cursor.fetchone()

            if result:
                tipo = "tutor"
            else:
                if abilitato:
                    tipo = "tutee"
                else:
                    return "Non sei autorizzato causa mancato pagamento del contributo volontario", 401

            classe = "---"
            cursor.execute("SELECT classe FROM Studenti WHERE email = %s", (users_email,))
            result = cursor.fetchone()
            if result:
                classe = result["classe"]

        if tipo == "docente" and (users_email not in admins and users_email not in centraline):
            abilitato = True
            return "Non sei autorizzato", 401

        user = User(unique_id, name, users_email, picture)
        login_user(user)

        session["mail"] = users_email
        session["classe"] = classe
        session["name"] = name
        session["tipo"] = tipo
        session["abilitato"] = abilitato

        if session["tipo"] == "tutor":
            return redirect("/loginTutor")
        elif session["tipo"] == "tutee":
            return redirect("/loginTutee")
        elif session["tipo"] == "docente":
            if users_email in admins:
                return redirect("/loginDocenti")
            elif users_email in centraline:
                session["tipo"] = "centralino"
                return redirect("/loginCentraline")
            else:
                return redirect("/")
        else:
            return redirect("/")

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/logout")
@login_required
def logout():
    if 'google_token' in session:
        google_token = session['google_token']
        google_provider_cfg = get_google_provider_cfg()
        revoke_url = google_provider_cfg["revocation_endpoint"]
        requests.post(revoke_url, params={'token': google_token['access_token']})

    session.pop('google_token', None)
    session.pop('oauth_state', None)
    session.pop("mail", None)
    session.pop("classe", None)
    session.pop("name", None)
    session.pop("tipo", None)

    logout_user()
    return redirect("/")
