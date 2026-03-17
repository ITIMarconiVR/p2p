import os
import mysql.connector
from flask import g

email_cred = {
    'email': 'p2p@marconiverona.edu.it',
    'password': 'p2p2025'
}

# Le credenziali vengono lette dalle variabili d'ambiente impostate in
# docker-compose.yml. I valori di default permettono di eseguire l'app
# anche fuori da Docker (es. sviluppo locale diretto).
db_cred = {
    'host':     os.environ.get('DB_HOST',     '172.16.1.98'),
    'user':     os.environ.get('DB_USER',     'p2p'),
    'password': os.environ.get('DB_PASSWORD', 'p2p2025'),
    'database': os.environ.get('DB_NAME',     'p2pdev'),
}

def get_db():
    if 'db' not in g:
        #print("CONNECT")
        g.db = mysql.connector.connect(
            host=db_cred['host'],
            user=db_cred['user'],
            password=db_cred['password'],
            database=db_cred['database'],
            auth_plugin='mysql_native_password'
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()
