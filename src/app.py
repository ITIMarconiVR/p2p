"""
app.py  –  Entry-point dell'applicazione P2P Marconi.

Il file crea l'istanza Flask tramite la factory `create_app` definita in
config.py e registra tutti i Blueprint (uno per dominio).
"""
from config import create_app
from auth import auth_bp
from routes_static import static_bp
from users import users_bp
from tutors import tutors_bp
from lezioni import lezioni_bp
from materie import materie_bp

# Crea e configura l'app
app = create_app()

# Registra i Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(static_bp)
app.register_blueprint(users_bp)
app.register_blueprint(tutors_bp)
app.register_blueprint(lezioni_bp)
app.register_blueprint(materie_bp)


if __name__ == "__main__":
    app.run(ssl_context="adhoc", host='0.0.0.0', port=5000, debug=True)
