"""
app.py  –  Entry-point dell'applicazione P2P Marconi.

Il file crea l'istanza Flask tramite la factory `create_app` definita in
config.py e registra tutti i Blueprint (uno per dominio).
"""
import os
from flask import request, redirect, jsonify, session
from flask_login import current_user
from config import create_app
from auth import auth_bp
from routes_static import static_bp
from users import users_bp
from tutors import tutors_bp
from lezioni import lezioni_bp, _is_servizio_attivo
from materie import materie_bp
from werkzeug.middleware.proxy_fix import ProxyFix

# Crea e configura l'app
app = create_app()
# Subito dopo aver creato l'app:
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Registra i Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(static_bp)
app.register_blueprint(users_bp)
app.register_blueprint(tutors_bp)
app.register_blueprint(lezioni_bp)
app.register_blueprint(materie_bp)


# ------------------------------------------------------------------------------
# Guardia globale: blocco servizio per utenti non-admin

# Prefissi/path esenti dal controllo (login, logout, pagina di avviso, static)
_ROUTE_ESCLUSE = {
    '/login',
    '/login/callback',
    '/logout',
    '/servizio_disabilitato',
    '/favicon.ico',
}
_PREFIX_ESCLUSI = ('/html/', '/css/', '/img/', '/lib/')


@app.context_processor
def inject_global_vars():
    from db import get_db
    vers = "1.0.0"
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT valore FROM ConfigurazioneServizio WHERE chiave = 'versione'")
        row = cursor.fetchone()
        cursor.close()
        if row:
            vers = row[0]
    except Exception:
        pass
    return dict(versione_servizio=vers)


@app.before_request
def controlla_servizio():
    """
    Prima di ogni richiesta, se il servizio è disabilitato e l'utente non è
    un admin (docente), blocca l'accesso:
    - Per richieste di pagine HTML → redirect alla pagina di avviso
    - Per chiamate API (JSON) → risposta 503 JSON
    Gli admin passano sempre, anche a servizio disattivato.
    """
    path = request.path

    # Lascia passare route esenti e file statici
    if path in _ROUTE_ESCLUSE or path.startswith(_PREFIX_ESCLUSI):
        return

    # Lascia passare utenti non autenticati (gestisce Flask-Login)
    if not current_user.is_authenticated:
        return

    # Lascia passare sempre gli admin
    if session.get('tipo') == 'docente':
        return

    # Controlla lo stato del servizio
    if not _is_servizio_attivo():
        # Chiamata API → risposta JSON
        if request.accept_mimetypes.best == 'application/json' or \
                request.content_type == 'application/json':
            return jsonify({'error': 'Servizio momentaneamente disabilitato'}), 503
        # Navigazione browser → pagina di avviso
        return redirect('/servizio_disabilitato')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    app.run(host='0.0.0.0', port=port, debug=True)

