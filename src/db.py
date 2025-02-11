import mysql.connector
from flask import g
#from cred import db_cred
email_cred = {
    'email': 'p2p@marconiverona.edu.it',
    'password': 'p2p2025'
}
db_cred = {
    'host': 'localhost',
    'user': 'p2p',
    'password': 'p2p2025',
    'database': 'p2p'
}
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
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
