# Python standard libraries
import json
import os
import sqlite3
import time
import csv

from markupsafe import escape

import flask
from flask import request, jsonify, send_from_directory, make_response, current_app, g, render_template
from flask.cli import with_appcontext

import sqlite3
#from io import StringIO
import io
# Third-party libraries
from flask import Flask, redirect, request, url_for, session
from flask_session import Session
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
from db import init_db_command
from db import get_db
from db import get_cfamici

from user import User

#-----------------------------------------
#google auth 
# Configuration
GOOGLE_CLIENT_ID="717588494889-3ecmb3rfivadscacgnj98cpd7d7ko0ar.apps.googleusercontent.com"
#GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET ="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"
#GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)

GOOGLE_DISCOVERY_URL = ("https://accounts.google.com/.well-known/openid-configuration")

# Flask app setup
app = Flask(__name__)

app.config["DEBUG"] = True

app.config['SECRET_KEY']="qwerasdzxc123098poi__#@[]"
app.config['BASE_DIR']=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#app.config["SESSION_FILE_DIR"] = "/var/wwwlocal/nextcl/wrk"
app.config["SESSION_FILE_DIR"] =app.config["BASE_DIR"] 
#DB_PATH = app.config['BASE_DIR'] + '/data/scuola.db'
#UPLOAD_FOLDER = app.config['BASE_DIR'] + '/import'
app.config['UPLOAD_FOLDER'] = app.config['BASE_DIR'] + '/import'
# dizionario per gestione import alunni
# la chiave è il cf il dato è la riga

#25/7 forse session non servce
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
###Da verificare la gestione del DB 
#try:
#    init_db_command()
#except sqlite3.OperationalError as err:
    # Assume it's already been created
#    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


@app.route('/html/<path:path>', methods=['GET'])
def send_static(path):
    return send_from_directory(os.path.join(app.config['BASE_DIR'], 'static/html'), path)

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

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("indaut.html",user=current_user)

    else:
        return ("<h1> Classi 2023!! </h1>"
                "<h2>Autenticazione richiesta </h2>"
                "<h2> usare email scolastica</h2>"
                '<h2><a href="/login"> MarconiVerona Login</a></h2>')

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)
    
@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        name=userinfo_response.json()["name"].lower()
    else:
        return "User email not available or not verified by Google.", 400

    # check utente
    #if name not in ["lorenzo de carli","vania doro","mariangela massella","antonio sette","orietta avesani"]:
    print("login-->"+name)
    utenti=["lorenzo de carli"]
    if name not in utenti:
        return "Utente non valido", 400


    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    #return userinfo_response.json()
    return redirect(url_for("index"))
    
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

#----TEMPLATE --------------------------------------------------------------

@app.route('/in')
def hello():
    return render_template('index.html')

#tabelle 
@app.route('/pag/tabelle',methods=['GET'])
def tabelle():
    return render_template('tabelle.html',user=current_user)

#classi 
@app.route('/pag/classi.html',methods=['GET'])
@login_required
def classi():
    return render_template('classi.html')

#import 
@app.route('/pag/import.html',methods=['GET'])
@login_required
def f_impo():
    return render_template('import.html')

if __name__ == "__main__":
    #app.run(host="0.0.0.0")
    app.run(ssl_context="adhoc",host="0.0.0.0")
