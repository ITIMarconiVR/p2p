
from flask import Flask, request, jsonify, redirect, session, send_from_directory, render_template
from db import get_db
from datetime import datetime
from datetime import timedelta
import os
import requests


# flask app configuration
app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SECRET_KEY']="qwerasdzxc123098poi__#@[]"
app.config['BASE_DIR']=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.config["SESSION_FILE_DIR"] =app.config["BASE_DIR"]



@app.route("/", methods=["GET"])
def home():
    return "test"

@app.route("/tutor", methods=["GET"])
def get_tuor():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)


        query = "SELECT s.cognome,s.nome,s.matricola,s.classe from  Peer p join Studenti s on p.matricolaP=s.matricola order by cognome,nome"

        cursor.execute(query)
        tutors = cursor.fetchall()

        return jsonify(tutors), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500



@app.route("/home")
def loginTutor():
    return render_template("admin/adddisp.html")



#@app.route("/add/<matricola>/<data>/<ora>", methods=["GET"])
#def add_eventmul(matricola,data,ora):

@app.route("/add", methods=["POST"])
def add_eventmul():
    matricola = request.json['matricola']
    data = request.json['data']
    ora = request.json['ora']
    print(matricola)
    print(data)
    print(ora)
    if matricola == "" or data == "" or ora == "" or matricola is None or data is None or ora is None or matricola == "null" or data == "null" or ora == "null":
        return jsonify({"error": "Attributi vuoti"}), 400

    date_format = '%Y-%m-%d'
    d = datetime.strptime(data, date_format)
    fine=datetime(2025,5,31)

    try:
        db = get_db()
        cursor = db.cursor()


        query = """
            INSERT INTO Lezioni (matricolaP, data, ora)
            VALUES (%s, %s, %s)
        """
        while d<fine:
            data_str = d.strftime('%Y-%m-%d')
            cursor.execute(query, (matricola, data_str, ora))
            d=d+timedelta(days=7)
        db.commit()
        return jsonify({"message": "Event added successfully"}), 201
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5500, debug=True)
