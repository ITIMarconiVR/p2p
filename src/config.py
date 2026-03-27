"""
config.py
Costanti di configurazione e inizializzazione dell'app Flask.
"""
import os
from datetime import timedelta

from flask import Flask
from flask_mail import Mail
from flask_session import Session
from flask_login import LoginManager

# ------------------------------------------------------------------------------
# App Version
VERSION = "1.0.0"

# ------------------------------------------------------------------------------
# Google OAuth
GOOGLE_CLIENT_ID = "717588494889-3ecmb3rfivadscacgnj98cpd7d7ko0ar.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# ------------------------------------------------------------------------------
# Utenti speciali
admins = ['LORENZO DE CARLI', 'CLAUDIA CARLETTI', 'peerTopeer Marconi']
resp_mail = 'claudia.carletti@marconiverona.edu.it'
centraline = ['PAOLA LAVAGNOLI', 'LUISELLA CARLI', 'PALMINA GIANNETTO']

# ------------------------------------------------------------------------------
# Istanze globali condivise (inizializzate in create_app)
mail = Mail()
login_manager = LoginManager()


def create_app():
    """Factory che crea e configura l'istanza Flask."""
    app = Flask(__name__)

    app.config['DEBUG'] = True
    app.config['VERSION'] = VERSION
    app.config['SECRET_KEY'] = "qwerasdzxc123098poi__#@[]"
    app.config['BASE_DIR'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app.config['UPLOAD_FOLDER'] = app.config['BASE_DIR'] + '/import'

    # Mail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = 'p2p@marconiverona.edu.it'
    app.config['MAIL_PASSWORD'] = 'jarc tihp ultm shhx' #'P2p2025$'
    app.config['MAIL_DEFAULT_SENDER'] = 'p2p@marconiverona.edu.it'
    app.config['MAIL_DEBUG'] = False

    # Session
    SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sessions')
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)
    app.config['SESSION_FILE_DIR'] = SESSION_DIR
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_LIFETIME"] = timedelta(days=7)

    # Inizializza estensioni
    mail.init_app(app)
    Session(app)
    login_manager.init_app(app)

    return app
