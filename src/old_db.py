# http://flask.pocoo.org/docs/1.0/tutorial/database/
import os
import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    print(id(g))
    if "db" not in g:
        #g.db = sqlite3.connect("/var/wwwlocal/nextcl/wrk/data/sqlite_db", detect_types=sqlite3.PARSE_DECLTYPES)
        filename = os.path.join(current_app.config['BASE_DIR'], "data/scuola.db")

        g.db = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
        #g.db.row_factory = sqlite3.Row
        g.db.row_factory = dict_factory
    return g.db
# dizionario statico all'applicazione 
#key cf value=vettore di CF
# boh non funziona
def get_cfamici():
    if "cfamici" not in g:
        g.cfamici={}
    return g.cfamici


def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))

@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


