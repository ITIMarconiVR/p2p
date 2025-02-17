from dateutil.relativedelta import relativedelta
from flask import Flask, request, jsonify, redirect, session, send_from_directory, render_template, escape
#from flask_cors import CORS
from flask_session import Session
from db import get_db
from flask_mail import Mail, Message
import shutil
from datetime import datetime, timedelta
from GoogleCalendarManager import GoogleCalendarManager

#LLL remove
#from authlib.integrations.flask_client import OAuth

import requests
import os

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
###LLLADD
from requests_oauthlib import OAuth2Session

from oauthlib.oauth2 import WebApplicationClient
from db import get_db
from user import User


# ------------------------------------------------------------------------------
# google auth configuration
GOOGLE_CLIENT_ID="717588494889-3ecmb3rfivadscacgnj98cpd7d7ko0ar.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET ="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"
GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")


# ------------------------------------------------------------------------------
# flask app configuration
app = Flask(__name__)
#CORS(app)
app.config['DEBUG'] = True
app.config['SECRET_KEY']="qwerasdzxc123098poi__#@[]"
app.config['BASE_DIR']=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config['UPLOAD_FOLDER'] = app.config['BASE_DIR'] + '/import'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'p2p@marconiverona.edu.it'
app.config['MAIL_PASSWORD'] = 'P2p2025$'
app.config['MAIL_DEFAULT_SENDER'] = 'p2p@marconiverona.edu.it'
app.config['MAIL_DEBUG'] = False

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)
app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_LIFETIME"] = timedelta(days=7)

mail = Mail(app)
Session(app)
#app.secret_key = os.urandom(24)


# ------------------------------------------------------------------------------
# utenti speciali
admins = ['LORENZO DE CARLI', 'CLAUDIA CARLETTI', 'peerTopeer Marconi']
resp_mail = 'claudia.carletti@marconiverona.edu.it'
centraline = ['PAOLA LAVAGNOLI', 'LUISELLA CARLI', 'PALMINA GIANNETTO'] 


# ------------------------------------------------------------------------------
# OAuth configuration
# oauth = OAuth(app)


# ------------------------------------------------------------------------------
# User session management setup
login_manager = LoginManager()
login_manager.init_app(app)


# ------------------------------------------------------------------------------
# OAuth 2 client setup
#LLL Spostata in login client = WebApplicationClient(GOOGLE_CLIENT_ID)


# ------------------------------------------------------------------------------
# Static files
@app.route('/html/<path:path>', methods=['GET'])
def send_static(path):
    return send_from_directory(os.path.join(app.config['BASE_DIR'], 'static'), path)

@app.route('/css/<path:path>', methods=['GET'])
def send_css(path):
    return send_from_directory(os.path.join(app.config['BASE_DIR'], 'static/css'), path)

@app.route('/img/<path:path>')
def send_img(path):
    data = os.path.join(app.config['BASE_DIR'], 'static/img')
    return send_from_directory(data, path)

@app.route('/lib/<path:path>')
def send_lib(path):
    data = os.path.join(app.config['BASE_DIR'], 'static/lib')
    return send_from_directory(data, path)


# ------------------------------------------------------------------------------
# Flask-Login helper to retrieve a user

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/")
def index():
    # if session and "tipo" in session.keys():
    #     if session["tipo"]=="tutor":
    #         return redirect("/loginTutor")
    #     elif session["tipo"]=="tutee": 
    #         return redirect("/loginTutee")
    #     elif session["tipo"]=="docente":
    #         return redirect("/loginDocenti")
    #     elif session["tipo"] == "centralino":
    #         return redirect("/loginCentraline")
    #     else:
    #         return jsonify({'error': 'Non sei autorizzato'}), 401
    return redirect('/login')

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # OAuth 2 client setup
    client = WebApplicationClient(GOOGLE_CLIENT_ID)

    # Genera un valore di stato casuale
    state = os.urandom(16).hex()  # Crea una stringa esadecimale di 32 caratteri
    
    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile", "https://www.googleapis.com/auth/calendar"],
        state=state
    )
    #LLLprint("request_uri login", request_uri)
    #LLLreturn redirect(request_uri)

    # Salva lo stato nella sessione per la protezione CSRF ???
    session['oauth_state'] = state

    return redirect(request_uri)

@app.route("/login/callback")
def callback():    
    # Ottieni i dati di configurazione del provider Google
    code = request.args.get("code")
    state = request.args.get("state", default=None, type=None)
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Usa il codice per ottenere un token di accesso
    oauth_session = OAuth2Session(GOOGLE_CLIENT_ID, state=state, redirect_uri=request.base_url)
    oauth_session.fetch_token(token_endpoint, client_secret=GOOGLE_CLIENT_SECRET, authorization_response=request.url)
    # Salva il token nella sessione
    session['google_token'] = oauth_session.token

    # ottenere i dati dell'utente
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    response = oauth_session.get(user_info_url)

    userinfo_response= response.json() if response.status_code == 200 else None

    if userinfo_response.get("email_verified"):
        unique_id = userinfo_response["sub"]
        users_email = userinfo_response["email"]
        picture = userinfo_response["picture"]
        users_name = userinfo_response["given_name"]
        name=userinfo_response["name"]
    else:
        return "User email not available or not verified by Google.", 400

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        # se le info non sono in tabella aggiungi
        cursor.execute("select * from utentiws where id = %s ",(unique_id,))
        res=cursor.fetchone()
        if not res:
            #inserisci
            cursor.execute("insert into utentiws (id,name,email,profile_pic) values (%s, %s, %s, %s)", (unique_id,name,users_email,picture))
            db.commit()

        tipo="docente"
        classe=""
        abilitato=0
        if users_email.lower().endswith("@studenti.marconiverona.edu.it"):
            # guardo se è abilitato a tutee (ha pagato il contributo volontario)
            query = "SELECT abilitato FROM Studenti WHERE email = %s"
            cursor.execute(query, (users_email, ))
            result = cursor.fetchone()
            if result["abilitato"] == 1:
                abilitato = True

            # guardo se è tutor o tutee
            cursor.execute("SELECT 1 FROM Peer WHERE matricolaP = %s",(users_email[0:5],))
            result = cursor.fetchone()

            if result:
                tipo="tutor"
            else:
                if abilitato:
                    tipo="tutee"
                else:
                    return "Non sei autorizzato causa mancato pagamento del contributo volontario", 401

            classe="---"
            q= "SELECT classe from Studenti where email = %s"
            cursor.execute(q, (users_email, ))
            result = cursor.fetchone()

            if result:
                classe=result["classe"]
        
        
        if tipo=="docente" and (name not in admins and  name not in centraline):
            abilitato = True
            return "Non sei autorizzato", 401

        user = User(unique_id, name, users_email, picture)

        login_user(user)
        # se utente == docente --> admin
        # se matricola --> tutor direttamente, che poi può decidere di fare il tutee
        session["mail"]=users_email
        session["classe"]=classe
        session["name"]=name
        session["tipo"]=tipo
        session["abilitato"]=abilitato


        # FOR DEBUGGING
        # session["tipo"] = "docente"
        # return redirect("/loginDocenti")

        fakeAdmins = ["19894"]
        if session["mail"][:5] in fakeAdmins:
            session["tipo"] = "docente"
            return redirect("/loginDocenti")

        # session["tipo"] = "centralino"
        # return redirect("/loginCentraline")

        if session["tipo"]=="tutor":
            return redirect("/loginTutor")
        elif session["tipo"]=="tutee": 
            return redirect("/loginTutee")
        elif session["tipo"]=="docente":
            if name in admins:
                return redirect("/loginDocenti")
            elif name in centraline:
                session["tipo"] = "centralino"
                return redirect("/loginCentraline")
            else:
                return redirect("/")
        else:
            return redirect("/")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ------------------------------------------------------------------------------
# render templates redirect

# login (index) pages
@app.route("/loginTutor")
@login_required
def loginTutor():
    return render_template("tutor/index.html",username=session["name"],user_id=session["mail"],tipo=session["tipo"], abilitato=session["abilitato"])
@app.route("/loginTutee")
@login_required
def loginTutee():
    if session["tipo"]=="tutor" and session["abilitato"]==0:
        return "Non sei autorizzato causa mancato pagamento del contributo volontario", 401
    return render_template("tutee/index.html",username=session["name"], user_id=session["mail"], tipo=session["tipo"])

@app.route("/loginDocenti")
@login_required
def loginDocenti():
    return render_template("admin/index.html",username=session["name"], user_id=session["mail"], tipo=session["tipo"])

@app.route("/loginCentraline")
@login_required
def loginCentraline():
    return render_template("centralino/index.html",username=session["name"], user_id=session["mail"], tipo=session["tipo"])

# tutor pages
@app.route("/tutor/profile") # qua il tutor può vedere/modificare le materie che insegna
@login_required
def tutor_profile():
    return render_template("tutor/profile.html", username=session["name"], user_id=session["mail"], tipo=session["tipo"])

# tutee pages
@app.route("/tutee/prenota")
@login_required
def tutee_prenota():
    return render_template("tutee/prenota.html", username=session["name"], user_id=session["mail"], tipo=session["tipo"])

# admin pages
@app.route("/admin/editTutors")
@login_required
def admin_editTutors():
    return render_template("admin/editTutors.html", username=session["name"], user_id=session["mail"], tipo=session["tipo"])

@app.route("/admin/seeEvents")
@login_required
def admin_seeEvents():
    return render_template("admin/seeEvents.html", username=session["name"], user_id=session["mail"], tipo=session["tipo"])

# ------------------------------------------------------------------------------
# Gestione sessioni

def cleanup_old_sessions():
    """Remove session files older than 7 days"""
    current_time = datetime.now()
    for filename in os.listdir(SESSION_DIR):
        filepath = os.path.join(SESSION_DIR, filename)
        # Get file modification time
        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        # If file is older than 7 days, delete it
        if current_time - file_time > timedelta(days=7):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Error deleting {filepath}: {e}")

# Schedule cleanup to run periodically
def schedule_cleanup():
    """
    Schedule the cleanup function to run daily
    You can use any scheduling method (APScheduler, celery, cron, etc.)
    Here's an example using APScheduler
    """
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_old_sessions, 'interval', days=1)
    scheduler.start()

# @app.before_first_request
# def init_app():
#     schedule_cleanup()


# ----------------------------------------------------------------
# Google calendar





@app.route("/logout")
@login_required
def logout():
    # Revoca il token di accesso prima di rimuoverlo dalla sessione
    if 'google_token' in session:
        google_token = session['google_token']
        google_provider_cfg = get_google_provider_cfg()
        revoke_url = google_provider_cfg["revocation_endpoint"]

        # Effettua la richiesta di revoca del token
        response = requests.post(revoke_url, params={'token': google_token['access_token']})

    session.pop('google_token', None)
    session.pop('oauth_state',None)
    session.pop("mail", None)
    session.pop("classe", None)
    session.pop("name", None)
    session.pop("tipo", None)
    
    logout_user()
    return redirect("/")


@app.route("/favicon.ico")
def favicon():
    return redirect("/img/favicon.ico")

@app.route("/userInfo", methods=["GET"])
@login_required
def get_user_info():
    """
    Get user information
    Returns: user session variables
    """
    if not current_user.is_authenticated:
        return jsonify({"error": "User not authenticated"}), 401
    else:
        return jsonify(session), 200

@app.route("/tutors", methods=["GET"])
@login_required
def get_tutors():
    """
    Get all tutors
    Returns: tutors
    """
    try:

        db = get_db()
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT P.matricolaP, S.nome, S.cognome, S.classe
            FROM Peer P, Studenti S
            WHERE P.matricolaP = S.matricola
            ORDER BY S.classe
        """
        cursor.execute(query)
        tutors = cursor.fetchall()
        
        return jsonify(tutors), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/tutors", methods=["POST"])
@login_required
def add_tutors():
    if session["tipo"]!="docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricola = request.json.get('matricola')
    if not matricola:
        return jsonify({"error": "Attributes are required"}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        
        # Check if matricola exists in Studenti
        cursor.execute("SELECT 1 FROM Studenti WHERE matricola = %s", (matricola,))
        one = cursor.fetchone()
        if one is None:
            return jsonify({"message": "Matricola non esistente"}), 200

        # Check if matricola exists in Peer
        cursor.execute("SELECT 1 FROM Peer WHERE matricolaP = %s", (matricola,))
        one = cursor.fetchone()
        if one is None:
            query = """
                INSERT INTO Peer (matricolaP)
                VALUES (%s)
            """
            cursor.execute(query, (matricola,))
            db.commit()
            return jsonify({"message": "Tutor aggiunto con successo"}), 200
        else:
            return jsonify({"message": "Tutor già presente"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/tutors/", methods=["DELETE"])
@login_required
def delete_tutor():
    if session["tipo"]!="docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricola = request.json.get('matricola')
    if not matricola:
        return jsonify({"error": "Attributes are required"}), 400
    
    try:
        db = get_db()
        cursor = db.cursor()
        query = """
            DELETE FROM Peer
            WHERE matricolaP = %s
        """
        cursor.execute(query, (matricola,))
        db.commit()

        noticeTutees(matricola)
        deleteTutorLessons(matricola)
    
        return jsonify({"message": "Tutor deleted successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

def noticeTutees(matricola):
    """
    Avvisa i tutee del cancellamento delle lezioni con una mail
    """
    try :
        db = get_db()
        cursor = db.cursor()

        query = """
            SELECT DISTINCT matricolaT
            FROM Lezioni
            WHERE matricolaP = %s AND data >= CURDATE()
        """
        cursor.execute(query, (matricola,))
        tutees = cursor.fetchall()

        query2 = """SELECT nome, cognome, classe FROM Studenti WHERE matricola = %s"""
        cursor.execute(query2, (matricola,))
        nome_cogn = cursor.fetchone()

        for tutee in tutees:
            destinatari = get_destinatari(tutee[0])
            send_email(destinatari, 'Lezione cancellata', f'Tutte le lezioni del tutor {nome_cogn[0]} {nome_cogn[1]} {nome_cogn[2]} sono state rimosse')
        
        # prendi tutti i dati delle lezioni del tutor e mettili nella tabella LezioniTutorRimossi
        cursor = db.cursor(dictionary=True)
        query_get = """SELECT * FROM Lezioni WHERE matricolaP = %s"""
        cursor.execute(query_get, (matricola,))
        lezioni = cursor.fetchall()

        query_add = """INSERT INTO LezioniTutorRimossi (matricolaP, data, ora, matricolaT, materiaL, argomenti, validata, aulaL)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        for lezione in lezioni:
            cursor.execute(query_add, (lezione['matricolaP'], lezione['data'], lezione['ora'], lezione['matricolaT'], lezione['materiaL'], lezione['argomenti'], lezione['validata'], lezione['aulaL']))
            db.commit()

        # rimuovi tutte le lezioni del tutor
        query = """DELETE FROM Lezioni WHERE matricolaT = %s AND data >= CURDATE()"""
        cursor.execute(query, (matricola,))
        db.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

def deleteTutorLessons(matricola):
    """
    Rimuove tutte le lezioni del tutor
    """
    # Aggiunge nella tabella che tiene traccia delle lezioni rimosse
    # Rimuove dalla tabella delle lezioni normali
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        query_get = """SELECT * FROM Lezioni WHERE matricolaP = %s"""
        cursor.execute(query_get, (matricola,))
        lezioni = cursor.fetchall()

        query_add = """INSERT INTO LezioniTutorRimossi (matricolaP, data, ora, matricolaT, materiaL, argomenti) 
            VALUES (%s, %s, %s, %s, %s, %s)"""
        for lezione in lezioni:
            cursor.execute(query_add, (lezione['matricolaP'], lezione['data'], lezione['ora'], lezione['matricolaT'], lezione['materiaL'], lezione['argomenti']))
            db.commit()

        query = """
            DELETE FROM Lezioni
            WHERE matricolaP = %s
        """
        cursor.execute(query, (matricola,))
        db.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

'''distLezione: distanza in giorni dalla lezione cancellata: presi tutti quelli con distanza maggiore di distLezione'''
@app.route('/lezioni_cancellate/<matricolaP>/<distLezione>/<prenotata>', methods=["GET"])
@login_required
def get_lezioni_cancellate(matricolaP, distLezione, prenotata):
    if session["tipo"]!="docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if matricolaP is None:
            return jsonify({"error": "Attributi mancanti: matricolaP"}), 400
        
        where_statement = """"""
        parameters = []
        if prenotata is not None:
            if prenotata:
                where_statement += "matricolaT IS NOT NULL AND "
        elif distLezione is not None:
            where_statement += """DATEDIFF(data, deleteDateTime) >= %s AND """
            parameters.append(distLezione)
        where_statement += "matricolaP = %s"
        parameters.append(matricolaP)

        query = f"""
            SELECT *
            FROM LezioniCancellate
            WHERE {where_statement}
        """
        
        cursor.execute(query, parameters)
        events = cursor.fetchall()          
        return jsonify(events), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/users", methods=["GET"])
@login_required
def get_users():
    """
    Ritorna uno studente
    Parametri: 
        matricola -> ritorna tutti i dati dell'utente richiesto
        nessuno -> ritorna alcuni dati per tutti gli utenti
    """
    try:
        matricola = request.args.get('matricola')
        if matricola is not None:
            if session["mail"][:5]!=matricola:
                return jsonify({"error": "non allowed"})
            db = get_db()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT *
                FROM Studenti
                WHERE matricola = %s
            """
            cursor.execute(query, (matricola,))
            user = cursor.fetchone()
            return jsonify(user), 200
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT matricola, nome, cognome, classe
            FROM Studenti
        """
        cursor.execute(query)
        users = cursor.fetchall()
        
        return jsonify(users), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/add_event", methods=["POST"])
@login_required
def add_event():
    """
    Aggiungi una disponibilità di lezione
    """
    # api chiamata dai tutor. 
    # Massimo 40 lezioni per tutor
    if not request.json or 'matricolaP' not in request.json or 'data' not in request.json or 'ora' not in request.json:
        return jsonify({"error": "Attributi mancanti"}), 400

    if session["mail"][:5]!=request.json['matricolaP'] or session["tipo"]!="tutor":
        return jsonify({"error":"Non sei autorizzato"}),401

    matricola = request.json['matricolaP']
    data = request.json['data']
    ora = request.json['ora']
    
    if matricola == "" or data == "" or ora == "" or matricola is None or data is None or ora is None or matricola == "null" or data == "null" or ora == "null":
        return jsonify({"error": "Attributi vuoti"}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        # TODO: sistemare la questione delle 40 lezioni massime
        # # first check if the user already has 40 events
        # query = """
        #     SELECT COUNT(*) as count
        #     FROM Lezioni 
        #     WHERE matricolaP = %s AND 
        #     (data >= CURDATE()) OR
        #     (data < CURDATE() AND matricolaT IS NOT NULL)
        # """
        # cursor.execute(query, (matricola,))
        # count = cursor.fetchone()
        # if count[0] >= 40:
        #     return jsonify({"error": "Limite di eventi raggiunto"}), 400
        
        # il tutor può fare al massimo una lezione al giorno
        query = """
            SELECT 1 
            FROM Lezioni
            WHERE matricolaP = %s AND data = %s
        """
        cursor.execute(query, (matricola, data))
        res = cursor.fetchone()
        if res is not None:
            return jsonify({"message": "Puoi fare una lezione al giorno"})

        query = """
            INSERT INTO Lezioni (matricolaP, data, ora)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (matricola, data, ora))
        db.commit()
        return jsonify({"message": "Event added successfully"}), 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/prenota", methods=["POST"])
@login_required
def reserve_event():
    """
    Prenota una lezione
    """
    # api chiamata dai tutee
    # le lezioni si vedono solo dopo essere state validate dagli admin


    # se è un tutor non abilitato a tutee non può prenotare
    if session["tipo"]=="tutor" and session["abilitato"]==0:
        return "Non sei autorizzato causa mancato pagamento del contributo volontario", 401
    

    matricolaP = request.json.get('matricolaP')
    ora = request.json.get('ora')
    data = request.json.get('data')
    matricolaT = request.json.get('matricolaT')
    materiaL = request.json.get('materiaL')
    argomenti = request.json.get('argomenti')
    argomenti = str(escape(argomenti))

    if not matricolaP or not ora or not data or not matricolaT or not materiaL or not argomenti:
        return jsonify({"error": "Attributes are required"}), 400
    
    if matricolaT!=session["mail"][:5]:
        return jsonify({"error": "not allowed"})

    try:
        db = get_db()
        cursor = db.cursor()

        query = """
            SELECT 1
            FROM Lezioni
            WHERE matricolaT = %s AND data = %s
        """
        cursor.execute(query, (matricolaT, data))
        res = cursor.fetchone()
        if res is not None:
            return jsonify({"error": "Puoi fare una lezione al giorno"})

        query = """
            UPDATE Lezioni
            SET matricolaT = %s , materiaL = %s, argomenti = %s
            WHERE matricolaP = %s AND ora = %s AND data = %s and data>=DATE_ADD(CURDATE(), INTERVAL 1 DAY)
        """
        cursor.execute(query, (matricolaT, materiaL, argomenti, matricolaP, ora, data))

        if cursor.rowcount > 0 and 'google_token' in session:
            calendar_manager = GoogleCalendarManager(session['google_token'])
            
            event_details = {
                'data': data,
                'ora': ora,
                'materiaL': materiaL,
                'argomenti': argomenti,
                'matricolaT': matricolaT,
                'matricolaP': matricolaP
            }
            
            success, calendar_id = calendar_manager.create_lesson_event(event_details)
            if success:
                # Store the calendar event ID
                cursor.execute("""
                    UPDATE Lezioni 
                    SET google_calendar_id = %s
                    WHERE matricolaP = %s AND ora = %s AND data = %s
                """, (calendar_id, matricolaP, ora, data))

        db.commit()

        query_nome = """
                SELECT nome, cognome, classe
                FROM Studenti
                WHERE matricola = %s
            """
        cursor.execute(query_nome, (matricolaP, ))
        nome_cognP = cursor.fetchone()
        cursor.execute(query_nome, (matricolaT, ))
        nome_cognT = cursor.fetchone()

        dest = get_destinatari(matricolaP)
        if matricolaT is not None:
            destT = get_destinatari(matricolaT)
            for des in destT:
                dest.append(des)
        if ora==1:
            ora="13:40"
        elif ora==2:
            ora="14:30"
        message = f"""La lezione del giorno {data} alle ore {ora} con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} è stata prenotata dal tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]}.\nMateria: {materiaL}\nArgomenti: {argomenti}"""
        send_email(dest, "Lezione prenotata", message)
        return jsonify({"message": "Event reserved successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/lezioni", methods=["GET"])
@login_required
def get_lezioni():
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

        where = """WHERE """
        campi = []

        if matricolaT is not None:
            if matricolaT == "NULL":
                where += """matricolaT IS NULL AND """
            else:
                if matricolaT == "%":
                    where += """matricolaT LIKE %s AND """
                    campi.append(matricolaT)
                else:
                    where += """matricolaT = %s AND """
                    campi.append(matricolaT)
        if matricolaP is not None:
            where += """matricolaP = %s AND """
            campi.append(matricolaP)
        if data is not None:
            where += """data = %s AND """
            campi.append(data)
        if ora is not None:
            where += """ora = %s AND """
            campi.append(ora)
        if materiaL is not None:
            where += """materiaL = %s AND """
            campi.append(materiaL)
        if validata is not None:
            where += """validata = %s AND """
            campi.append(validata)
        if aulaL is not None:
            where += """aulaL = %s AND """
            campi.append(aulaL)
        if where == """WHERE """:
            where = ""
        else:
            where = where[:-5]

        query = """
            SELECT *
            FROM Lezioni
        """ + where

        cursor.execute(query, campi)
        events = cursor.fetchall()
        return jsonify(events), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route("/lezioni2", methods=["GET"])
@login_required
def get_lezioni2():
    try:
        # Recupera i parametri della query
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

        # Costruzione dinamica della query
        where_clauses = []
        values = []

        for field, value in query_params.items():
            if value is not None:
                if field == "matricolaT":
                    if value is None:
                        where_clauses.append("matricolaT IS NULL")
                    elif value == "%":
                        where_clauses.append("matricolaT LIKE %s")
                        values.append(value)
                    else:
                        where_clauses.append("matricolaT = %s")
                        values.append(value)
                else:
                    where_clauses.append(f"{field} = %s")
                    values.append(value)

        where_statement = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT L.*, S1.nome nomeP, S1.cognome cognomeP, S1.classe classeP, S2.nome nomeT, S2.cognome cognomeT, S2.classe classeT
            FROM Lezioni AS L 
            JOIN Studenti S1 ON L.matricolaP = S1.matricola
            LEFT JOIN Studenti S2 ON L.matricolaT = S2.matricola
            {where_statement}
        """

        cursor.execute(query, values)
        events = cursor.fetchall()

        return jsonify(events), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/lezioni", methods=["POST"])
@login_required
def valida_lezione():
    # api chiamata dagli admin
    # valida la proposta di lezione fatta da un tutor
    if session["tipo"]!="docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    matricolaP = request.json.get('matricolaP')
    ora = request.json.get('ora')
    data = request.json.get('data')

    if not matricolaP or not ora or not data:
        return jsonify({"error": "Attributes are required"}), 400

    try:
        db = get_db()
        cursor = db.cursor()
        query = """
            UPDATE Lezioni
            SET validata = 1
            WHERE matricolaP = %s AND ora = %s AND data = %s
        """
        cursor.execute(query, (matricolaP, ora, data, ))
        db.commit()
        return jsonify({"message": "Event validated successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500    

@app.route("/valida_tutto", methods=["POST"])
@login_required
def valida_tutto():
    # api chiamata dagli admin
    # valida tutte le proposte di lezione fatte dai tutor
    if session["tipo"]!="docente":
        return jsonify({"error": "Non sei autorizzato"}), 401

    try:
        db = get_db()
        cursor = db.cursor()
        query = """
            UPDATE Lezioni
            SET validata = 1
            WHERE data >= CURDATE() AND validata = 0
        """
        cursor.execute(query, ())
        db.commit()
        return jsonify({"message": "Event validated successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500    


'''
Cancellazione lezione
1> da tutee
2> da tutor con tutee presente (lezione già prenotata)
3> da tutor senza prenotazioni
'''
@app.route("/lezioni", methods=["DELETE"])
@login_required
def delete_lezione():
    matricolaT = request.json.get('matricolaT')
    matricolaP = request.json.get('matricolaP')
    data = request.json.get('data')
    ora = request.json.get('ora')
    deleter = request.json.get('deleter')
    matricolaD = deleter


    if not matricolaP or not data or not ora or not deleter:
        return jsonify({"error": "Attributes are required"}), 400
    
    if deleter != session['mail'][:5]:
        return jsonify({"error": "Non sei autorizzato"}), 401            

    try:
        db = get_db()
        cursor = db.cursor()

        query_nome = """
                SELECT nome, cognome, classe
                FROM Studenti
                WHERE matricola = %s
            """
        cursor.execute(query_nome, (matricolaP, ))
        nome_cognP = cursor.fetchone()
        if matricolaT is not None:
            cursor.execute(query_nome, (matricolaT, ))
            nome_cognT = cursor.fetchone()
            if deleter==matricolaT:
                deleter = nome_cognT
            elif deleter==matricolaP:
                deleter = nome_cognP
        
        if matricolaT is not None:
            query = """
                UPDATE Lezioni
                SET matricolaT = NULL
                WHERE matricolaT = %s AND data = %s AND ora = %s AND DATE(data) >= CURDATE()
            """
            cursor.execute(query, (matricolaT, data, ora))
            db.commit()
            
        if matricolaD==matricolaP:
            query = """
                DELETE FROM Lezioni
                WHERE matricolaP = %s AND data = %s AND ora = %s AND DATE(data) > CURDATE()
            """
            cursor.execute(query, (matricolaP, data, ora))
            db.commit()
                
        dest = get_destinatari(matricolaP)
        if matricolaT is not None:
            destT = get_destinatari(matricolaT)
            for des in destT:
                dest.append(des)
        if ora==1:
            ora="13:40"
        elif ora==2:
            ora="14:30"

        if matricolaT is not None:
            message = f"""La lezione del giorno {data} alle ore {ora} con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} e tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]} è stata annullata da {deleter[0]} {deleter[1]}."""
        else:
            message = f"""La lezione del giorno {data} alle ore {ora} con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} è stata annullata da {deleter[0]} {deleter[1]} {deleter[2]}."""
        send_email(dest, "Lezione cancellata", message)

        return jsonify({'message': 'Lezione rimossa con successo'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route("/delete_lezione_tutor", methods=["DELETE"])
@login_required
def delete_lezione_tutor():
    """lesson deleted by a tutor"""
    matricolaT = request.json.get('matricolaT')
    matricolaP = request.json.get('matricolaP')
    data = request.json.get('data')
    ora = request.json.get('ora')

    if not matricolaP or not data or not ora:
        return jsonify({"error": "Attributes are required"}), 400
    if matricolaP!=session["mail"][:5]:
        return jsonify({"error": "Non sei autorizzato"}), 401
    
    try:
        db = get_db()
        cursor = db.cursor()

        # First, get the calendar event ID if it exists
        cursor.execute("""
            SELECT google_calendar_id 
            FROM Lezioni 
            WHERE matricolaP = %s AND data = %s AND ora = %s
        """, (matricolaP, data, ora))
        result = cursor.fetchone()
        
        # If there's a calendar event, delete it
        if result and result['google_calendar_id'] and 'google_token' in session:
            calendar_manager = GoogleCalendarManager(session['google_token'])
            calendar_manager.delete_event(result['google_calendar_id'])
        

        query_nome = """
                SELECT nome, cognome, classe
                FROM Studenti
                WHERE matricola = %s
            """
        cursor.execute(query_nome, (matricolaP, ))
        nome_cognP = cursor.fetchone()
        if matricolaT is not None:
            cursor.execute(query_nome, (matricolaT, ))
            nome_cognT = cursor.fetchone()

        
        # prendo i dati della lezione da cancellare e li metto nella tabella delle lezioni rimosse per tenerne traccia
        cursor = db.cursor(dictionary=True)
        query_get = """SELECT * FROM Lezioni WHERE matricolaP = %s AND data = %s AND ora = %s"""
        cursor.execute(query_get, (matricolaP, data, ora))
        lezione = cursor.fetchone()

        query_insert = """INSERT INTO LezioniCancellate 
                                (matricolaP, data, ora, matricolaT, materiaL, argomenti, validata, aulaL, svolta, deleter)
                            VALUES 
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_insert, (lezione['matricolaP'], lezione['data'], lezione['ora'], lezione['matricolaT'], lezione['materiaL'], lezione['argomenti'], lezione['validata'], lezione['aulaL'], lezione['svolta'], matricolaP))
        db.commit()
            
        # rimuovo la lezione dalla tabella lezioni
        cursor = db.cursor()
        query = """
            DELETE FROM Lezioni
            WHERE matricolaP = %s AND data = %s AND ora = %s AND DATE(data) > CURDATE()
        """
        cursor.execute(query, (matricolaP, data, ora))
        db.commit()


        # prendi i destinatari delle mail per il tutor e per il tutee (se c'è)        
        dest = get_destinatari(matricolaP)
        if matricolaT is not None:
            destT = get_destinatari(matricolaT)
            for des in destT:
                dest.append(des)
        if ora==1:
            ora="13:40"
        elif ora==2:
            ora="14:30"

        if matricolaT is not None:
            message = f"""La lezione del giorno {data} alle ore {ora} con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} e tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]} è stata annullata da {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]}."""
        else:
            message = f"""La lezione del giorno {data} alle ore {ora} con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognT[2]} è stata annullata da {nome_cognP[0]} {nome_cognP[1]} {nome_cognT[2]}."""
        send_email(dest, "Lezione cancellata", message)

        return jsonify({'message': 'Lezione rimossa con successo'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
  
@app.route("/delete_lezione_tutee", methods=["DELETE"])
@login_required
def delete_lezione_tutee():
    """lesson deleted by a tutee"""
    matricolaT = request.json.get('matricolaT')
    matricolaP = request.json.get('matricolaP')
    data = request.json.get('data')
    ora = request.json.get('ora')

    if not matricolaP or not data or not ora:
        return jsonify({"error": "Attributes are required"}), 400
    if matricolaT!=session["mail"][:5]:
        return jsonify({"error": "Non sei autorizzato"}), 401
    
    try:
        db = get_db()
        cursor = db.cursor()

        # First, get the calendar event ID if it exists
        cursor.execute("""
            SELECT google_calendar_id 
            FROM Lezioni 
            WHERE matricolaP = %s AND data = %s AND ora = %s
        """, (matricolaP, data, ora))
        result = cursor.fetchone()
        
        # If there's a calendar event, delete it
        if result and result['google_calendar_id'] and 'google_token' in session:
            calendar_manager = GoogleCalendarManager(session['google_token'])
            calendar_manager.delete_event(result['google_calendar_id'])
        
        
        # prendi i nomi dei tutor e tutee
        query_nome = """
                SELECT nome, cognome, classe
                FROM Studenti
                WHERE matricola = %s
            """
        cursor.execute(query_nome, (matricolaP, ))
        nome_cognP = cursor.fetchone()
        cursor.execute(query_nome, (matricolaT, ))
        nome_cognT = cursor.fetchone()

        # prendo i dati della lezione da sprenotare e li metto nella tabella delle lezioni rimosse per tenerne traccia
        cursor = db.cursor(dictionary=True)
        query_get = """SELECT * FROM Lezioni WHERE matricolaP = %s AND data = %s AND ora = %s"""
        cursor.execute(query_get, (matricolaP, data, ora))
        lezione = cursor.fetchone()

        query_insert = """INSERT INTO LezioniCancellate 
                                (matricolaP, data, ora, matricolaT, materiaL, argomenti, validata, aulaL, svolta, deleter)
                            VALUES 
                                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query_insert, (lezione['matricolaP'], lezione['data'], lezione['ora'], lezione['matricolaT'], lezione['materiaL'], lezione['argomenti'], lezione['validata'], lezione['aulaL'], lezione['svolta'], matricolaT))
        db.commit()

        # set null i valori del tutee nella tabella lezioni, non cancello la lezione
        cursor = db.cursor()
        query = """
            UPDATE Lezioni
            SET matricolaT = NULL, materiaL = NULL, argomenti = NULL, aulaL = NULL, google_calendar_id = NULL
            WHERE matricolaT = %s AND data = %s AND ora = %s AND DATE(data) >= CURDATE()
        """
        cursor.execute(query, (matricolaT, data, ora))
        db.commit()

        # prendi i destinatari delle mail per il tutor e per il tutee (se c'è)        
        dest = get_destinatari(matricolaP)
        destT = get_destinatari(matricolaT)
        for des in destT:
            dest.append(des)
        if ora==1:
            ora="13:40"
        elif ora==2:
            ora="14:30"

        message = f"""La lezione del giorno {data} alle ore {ora} con tutor {nome_cognP[0]} {nome_cognP[1]} {nome_cognP[2]} e tutee {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]} è stata annullata da {nome_cognT[0]} {nome_cognT[1]} {nome_cognT[2]}."""
        send_email(dest, "Lezione cancellata", message)

        return jsonify({'message': 'Lezione rimossa con successo'})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/materie", methods=["GET"])
@login_required
def get_materie():
    # parametri:
    #   matricola -> ritorna le materie insegnate dal tutor
    #   nessuno -> ritorna la lista di materie
    matricola = request.args.get('matricola')
    try:
        if matricola is not None:
            db = get_db()
            cursor = db.cursor()
            query = """
                SELECT idMat
                FROM MaterieInsegnate
                WHERE matricola = %s
            """
            cursor.execute(query, (matricola,))
            materie = cursor.fetchall()
            mat = []
            for m in materie:
                mat.append(m[0])
            return jsonify(mat), 200
        
        else:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            query = """
                SELECT idMat
                FROM Materie
            """
            cursor.execute(query)
            materie = cursor.fetchall()
            return jsonify(materie), 200
        
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500
    
@app.route("/materie", methods=["POST"])
@login_required
def manage_materie():
    """
    Aggiunge una materia insegnata ad un tutor
    """
    matricola = request.json.get('matricola')
    idMat = request.json.get('materia')

    if not matricola or not idMat:
        return jsonify({"error": "Attributes are required"}), 400

    if session["tipo"]!="tutor" or session["mail"][:5]!=matricola:
        return jsonify({"error": "Non sei autorizzato"}), 401
    
    try:
        db = get_db()

        cursor = db.cursor()
        idMat = idMat.upper()
        # Check if idMat exists in Materie
        cursor.execute("SELECT * FROM Materie WHERE idMat = %s", (idMat,))
        one = cursor.fetchone()
        if one is None:
            return jsonify({"error": "Invalid materia"}), 400
        query = """
            INSERT INTO MaterieInsegnate (matricola, idMat)
            VALUES (%s, %s)
        """
        cursor.execute(query, (matricola, idMat))
        db.commit()
        return jsonify({"message": "Materia added successfully"}), 201
        
    except Exception as e:
        print(f"An error occurred: {e}")
        if "Duplicate entry" in str(e):
            return jsonify({"error": "Duplicate entry"}), 400
        return jsonify({"error": "Internal server error","desc":e}), 500

@app.route("/materie", methods=["DELETE"])
@login_required
def delete_materia():
    """
    Rimuove una materia insegnata da un tutor
    """
    matricola = request.json.get('matricola')
    idMat = request.json.get('idMat')

    if not matricola or not idMat:
        return jsonify({"error": "Attributes are required"}), 400

    if session["tipo"]!="tutor" or session["mail"][:5]!=matricola:
        return jsonify({"error": "Non sei autorizzato"}), 401
    
    try:
        db = get_db()
        cursor = db.cursor()
        query = """
            DELETE FROM MaterieInsegnate
            WHERE matricola = %s AND idMat = %s
        """
        cursor.execute(query, (matricola, idMat))
        db.commit()
        return jsonify({"message": "Materia deleted successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/lezioniFilter", methods=["GET"])
@login_required
def get_lezioni_per_materia():
    idMat = request.args.get('idMat')
    anno = request.args.get('anno')
    indirizzo = request.args.get('indirizzo')
    matricolaP = request.args.get('matricolaP')
    
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        if idMat is None and anno is None and indirizzo is None:
            idMat = "ALL"
            anno = "ALL"
            indirizzo = "ALL"
        
        query = """
            SELECT DISTINCT L.*, S1.nome nomeP, S1.cognome cognomeP, S1.classe classeP
            FROM MaterieInsegnate MI, Lezioni L, Studenti S1
            WHERE 
            MI.matricola = L.matricolaP AND
            S1.matricola = L.matricolaP AND
            L.matricolaP LIKE %s AND
            L.matricolaT IS NULL AND
            L.validata = 1 AND
            MI.idMat LIKE %s AND
            S1.classe LIKE %s AND
            S1.classe LIKE %s
        """

        if idMat == 'ALL':
            idMat = "%"
        else:
            idMat = idMat.upper()
        if anno == 'ALL':
            anno = '_'
        else:
            anno = anno.upper()
        if indirizzo =='ALL':
            indirizzo = "_"
        else:
            indirizzo = indirizzo.upper()[0]
        if matricolaP=='ALL':
            matricolaP = "%"
        
        cursor.execute(query, ('%'+matricolaP+'%', idMat, '%'+anno+'%', '%'+indirizzo+'%'))
        lezioniFiltrate = cursor.fetchall()
        return jsonify(lezioniFiltrate), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

def send_email(recipients, subject, message):
    if not all([recipients, message]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        recipients.append(resp_mail)
        for des in recipients:
            msg = Message(subject, recipients=[des])
            msg.body = message
            mail.send(msg)

        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

def get_destinatari(matricola):
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

        destinatari = []
        year = user['data_nascita'][6:]
        month = user['data_nascita'][3:5]
        day = user['data_nascita'][:2]
        age = datetime.date(year=int(year), month=int(month), day=int(day))
        today = datetime.date.today()
        if (relativedelta(today, age).years < 18):
            if user['emailgenitore1']==user['emailgenitore2']:
                destinatari.append('emailgenitore1')
            else:
                destinatari.append(user['emailgenitore1'])
                destinatari.append(user['emailgenitore2'])
        destinatari.append(user['email'])

        return destinatari
    except Exception as e:
        print("error:", e)
        return jsonify({"error": "error while fetching user data"}), 401

if __name__ == "__main__":
    # Run initial cleanup
    # cleanup_old_sessions()
    app.run(ssl_context="adhoc",host='0.0.0.0', port=5000, debug=True)
