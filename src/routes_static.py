"""
routes_static.py
Blueprint per file statici e redirect verso i template HTML.
"""
import os
from flask import Blueprint, redirect, render_template, send_from_directory, session, current_app
from flask_login import login_required

static_bp = Blueprint('static_routes', __name__)


# ------------------------------------------------------------------------------
# Serve file statici

@static_bp.route('/html/<path:path>', methods=['GET'])
def send_html(path):
    return send_from_directory(os.path.join(current_app.config['BASE_DIR'], 'static'), path)

@static_bp.route('/css/<path:path>', methods=['GET'])
def send_css(path):
    return send_from_directory(os.path.join(current_app.config['BASE_DIR'], 'static/css'), path)

@static_bp.route('/img/<path:path>')
def send_img(path):
    return send_from_directory(os.path.join(current_app.config['BASE_DIR'], 'static/img'), path)

@static_bp.route('/lib/<path:path>')
def send_lib(path):
    return send_from_directory(os.path.join(current_app.config['BASE_DIR'], 'static/lib'), path)

@static_bp.route('/favicon.ico')
def favicon():
    return redirect("/img/favicon.ico")


# ------------------------------------------------------------------------------
# Indice

@static_bp.route("/")
def index():
    return redirect('/login')


# ------------------------------------------------------------------------------
# Login landing pages (dopo OAuth redirect)

@static_bp.route("/loginTutor")
@login_required
def loginTutor():
    return render_template("tutor/index.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"],
                           abilitato=session["abilitato"])

@static_bp.route("/loginTutee")
@login_required
def loginTutee():
    if session["tipo"] == "tutor" and session["abilitato"] == 0:
        return "Non sei autorizzato causa mancato pagamento del contributo volontario", 401
    return render_template("tutee/index.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])

@static_bp.route("/loginDocenti")
@login_required
def loginDocenti():
    return render_template("admin/index.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])

@static_bp.route("/loginCentraline")
@login_required
def loginCentraline():
    return render_template("centralino/index.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])


# ------------------------------------------------------------------------------
# Pagine interne per ruolo

@static_bp.route("/tutor/profile")
@login_required
def tutor_profile():
    return render_template("tutor/profile.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])

@static_bp.route("/tutee/prenota")
@login_required
def tutee_prenota():
    return render_template("tutee/prenota.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])

@static_bp.route("/tutee/tutors")
@login_required
def tutee_tutors():
    return render_template("tutee/tutors.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])

@static_bp.route("/admin/editTutors")
@login_required
def admin_editTutors():
    return render_template("admin/editTutors.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])

@static_bp.route("/admin/seeEvents")
@login_required
def admin_seeEvents():
    return render_template("admin/seeEvents.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])


# ------------------------------------------------------------------------------
# Pagina notifiche (tutti i ruoli)

@static_bp.route("/notifiche/pagina")
@login_required
def pagina_notifiche():
    return render_template("notifiche.html",
                           username=session["name"],
                           user_id=session["mail"],
                           tipo=session["tipo"])


# ------------------------------------------------------------------------------
# Pagina avviso servizio disabilitato

@static_bp.route("/servizio_disabilitato")
def servizio_disabilitato():
    return render_template("servizio_disabilitato.html"), 503

