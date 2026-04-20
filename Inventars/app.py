from flask import Flask, render_template, request, url_for, redirect, session   
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


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


@app.route('/rezervet/<int:id>')
def rezervet(id):
    if 'lietotajs_id' not in session:
        return redirect(url_for('pieteiksanas'))
    
    db = dabut_db()
    inventars = db.execute("SELECT * FROM inventars WHERE ID = ?", (id,)).fetchone()
    
    if inventars and inventars['pieejamais_skaits'] > 0:
        db.execute("UPDATE inventars SET pieejamais_skaits = pieejamais_skaits - 1 WHERE ID = ?", (id,))
        
        sodien = datetime.now().strftime('%Y-%m-%d')
        db.execute("INSERT INTO izsniegtais (lietotajs_ID, inventars_ID, datums_izsniegts) VALUES (?, ?, ?)",
                   (session['lietotajs_id'], id, sodien))
        
        db.commit()
    
    db.close()
    return redirect(url_for('inventars'))

@app.route('/mans_inventars')
def mans_inventars():
    if 'lietotajs_id' not in session:
        return redirect(url_for('pieteiksanas'))
    
    db = dabut_db()
    mans_saraksts = db.execute("""
        SELECT izsniegtais.ID, inventars.nosaukums, izsniegtais.datums_izsniegts 
        FROM izsniegtais 
        JOIN inventars ON izsniegtais.inventars_ID = inventars.ID 
        WHERE izsniegtais.lietotajs_ID = ?
    """, (session['lietotajs_id'],)).fetchall()
    
    db.close()
    return render_template('mans_inventars.html', saraksts=mans_saraksts)

@app.route('/atdot_inventaru'):
def atdot_inventaru():
    if 'if_lietotajs_id' not in session:
        return redirect(url_for('pieteiksanas'))

    db = dabut_db()
    

if __name__ == "__main__":
    app.run(debug=True)