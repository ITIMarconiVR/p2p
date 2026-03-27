"""
app.py  –  Entry-point dell'applicazione P2P Marconi.

Il file crea l'istanza Flask tramite la factory `create_app` definita in
config.py e registra tutti i Blueprint (uno per dominio).
"""
import os
from config import create_app
from auth import auth_bp
from routes_static import static_bp
from users import users_bp
from tutors import tutors_bp
from lezioni import lezioni_bp
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    app.run(host='0.0.0.0', port=port, debug=True)
