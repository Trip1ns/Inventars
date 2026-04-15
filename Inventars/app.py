from flask import Flask, render_template, request, url_for, redirect, session   
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "loti_slepeni_123"

def dabut_db():
    conn = sqlite3.connect('projekts.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def base():
    if 'lietotajs_id' in session:
        return redirect(url_for('inventars'))
    return redirect(url_for('pieteiksanas'))

@app.route('/pieteiksanas', methods=['GET', 'POST'])
def pieteiksanas():
    if request.method == 'POST':
        lietotajvards = request.form.get('lietotajs')
        parole = request.form.get('parole')

        db = dabut_db()
        lietotajs = db.execute("SELECT * FROM lietotaji WHERE lietotajvards = ?", (lietotajvards,)).fetchone()
        db.close()

        if lietotajs and check_password_hash(lietotajs['parole'], parole):
            session['lietotajs_id'] = lietotajs['ID']
            session['lietotajvards'] = lietotajs['lietotajvards']
            session['loma'] = lietotajs['loma']
            return redirect(url_for('inventars'))
        
        return "Nepareizi dati!"
    
    return render_template("pieteiksanas.html")

@app.route('/registreties', methods=['GET', 'POST'])
def registreties():
    if request.method == 'POST':
        lietotajs = request.form.get('lietotajs')
        parole = request.form.get('parole')
        parole_hash = generate_password_hash(parole)
        loma = 'klients' 

        db = dabut_db() 
        db.execute("INSERT INTO lietotaji (lietotajvards, parole, loma) VALUES (?, ?, ?)", 
                   (lietotajs, parole_hash, loma))
        db.commit()
        db.close()
        return redirect(url_for('pieteiksanas'))
    return render_template("registreties.html") 

@app.route("/inventars")
def inventars():
    if 'lietotajs_id' not in session:
        return redirect(url_for('pieteiksanas'))

    db = dabut_db()
    nosaukums = request.args.get("nosaukums", "")
    
    if nosaukums:
        atbilde = db.execute("SELECT * FROM inventars WHERE nosaukums LIKE ?", (f"%{nosaukums}%",)).fetchall()
    else:
        atbilde = db.execute("SELECT * FROM inventars").fetchall()
    
    db.close()
    return render_template("inventars.html", inventars = atbilde)

@app.route('/pievienot', methods=['GET', 'POST'])
def pievienot():
    if session.get('loma') != 'admin':
        return "Piekļuve liegta!"

    if request.method == 'POST':
        veids = request.form.get('veids')
        nosaukums = request.form.get('nosaukums')
        kopejais = request.form.get('kopejais_skaits')
        pieejamais = request.form.get('pieejamais_skaits')

        db = dabut_db()
        db.execute("INSERT INTO inventars (veids, nosaukums, kopejais_skaits, pieejamais_skaits) VALUES (?, ?, ?, ?)",
                   (veids, nosaukums, kopejais, pieejamais))
        db.commit()
        db.close()
        return redirect(url_for('inventars'))
    
    return render_template('pievienot.html')

@app.route('/atslegties')
def atslegties():
    session.clear()
    return redirect(url_for('pieteiksanas'))

if __name__ == "__main__":
    app.run(debug=True)