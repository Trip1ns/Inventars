from flask import Flask, render_template, request, url_for, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.secret_key = "projekts_inventars"

def dabut_db(): #Palīgfunkcija, lai savienotos ar datubāzi.
    conn = sqlite3.connect('projekts.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/') #sākumlapa
def base():
    if 'lietotajs_id' in session:
        return redirect(url_for('inventars'))
    return redirect(url_for('pieteiksanas'))

@app.route('/pieteiksanas', methods=['GET', 'POST']) #Pieteikšanās lapa.
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
        
        flash("Nepareizi dati!") 
    
    return render_template("pieteiksanas.html")

@app.route('/registreties', methods=['GET', 'POST']) #Reģistrēšanās lapa.
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

@app.route("/inventars") #Visa inventāra saraksts.
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

@app.route('/pievienot', methods=['GET', 'POST']) #Admin pievieno inventāru kopējam inventāra sarakstam.
def pievienot():
    if session.get('loma') != 'admin':
        return "Piekļuve liegta!"

    if request.method == 'POST':
        veids = request.form.get('veids')
        nosaukums = request.form.get('nosaukums')
        try:
            kopejais = int(request.form.get('kopejais_skaits'))
            pieejamais = int(request.form.get('pieejamais_skaits'))
        except (ValueError, TypeError):
            flash("Kļūda - ievadiet naturālus un pozitīvus skaitļus") 
            return "Kļūda - ievadiet naturālus un pozitīvus skaitļus"

        if kopejais < 1 or pieejamais < 0:
            flash("Kļūda - ievadiet naturālus un pozitīvus skaitļus")
            return  "Kļūda - ievadiet naturālus un pozitīvus skaitļus"

        if pieejamais > kopejais:
            flash("Kļūda - pieejamais skaits ir lielāks par kopējo skaitu")
            return "Kļūda - pieejamais skaits ir lielāks par kopējo skaitu"

        db = dabut_db()
        db.execute("INSERT INTO inventars (veids, nosaukums, kopejais_skaits, pieejamais_skaits) VALUES (?, ?, ?, ?)",
                   (veids, nosaukums, kopejais, pieejamais))
        db.commit()
        db.close()
        return redirect(url_for('inventars'))
    
    return render_template('pievienot.html')

@app.route('/atslegties') #Lietotājs atslēdzas no sistēmas.
def atslegties():
    session.clear()
    return redirect(url_for('pieteiksanas'))


@app.route('/rezervet/<int:id>') #Klients rezervē inventāru.
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

@app.route('/mans_inventars') #Klients redz savu paņemto inventāru.
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

@app.route('/atdot_inventaru') #Klients redz savu paņemoto inventāru.
def atdot_inventaru():
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
    return render_template('atdot.html', saraksts=mans_saraksts)

@app.route('/izpildit_atdosanu/<int:ieraksta_id>') #Klients nospiežot pogu "atdot" atdot paņemto inventāru.
def izpildit_atdosanu(ieraksta_id):
    if 'lietotajs_id' not in session:
        return redirect(url_for('pieteiksanas'))
    
    db = dabut_db()
    ieraksts = db.execute("SELECT inventars_ID FROM izsniegtais WHERE ID = ?", (ieraksta_id,)).fetchone()
    
    if ieraksts:
        inv_id = ieraksts['inventars_ID']
        db.execute("UPDATE inventars SET pieejamais_skaits = pieejamais_skaits + 1 WHERE ID = ?", (inv_id,))
        db.execute("DELETE FROM izsniegtais WHERE ID = ?", (ieraksta_id,))
        db.commit()
    
    db.close()
    return redirect(url_for('atdot_inventaru'))    

@app.route('/dzest_saraksts') #Admin izdzēš inventāru no inventāra saraksta.
def dzest_saraksts():
    if session.get('loma') != 'admin':
        return "Piekļuve liegta!"
    
    db = dabut_db()
    visi_dati = db.execute("SELECT * FROM inventars").fetchall()
    db.close()
    return render_template('dzest.html', inventars=visi_dati)

@app.route('/dzest/<int:id>') #pogas "dzēst" funkcionalitāte
def dzest(id):
    if session.get('loma') != 'admin':
        return "Piekļuve liegta!"
    
    db = dabut_db()
    db.execute("DELETE FROM inventars WHERE ID = ?", (id,))
    db.commit()
    db.close()
    
    return redirect(url_for('dzest_saraksts'))

@app.route('/izsniegtais_inventars') #Admin redz klientus, kuriem ir izsniegts inventārs.
def izsniegtais_inventars():
    if session.get('loma') != 'admin':
        return "Piekļuve liegta! Šī lapa ir tikai administratoriem.", 403
    
    db = dabut_db()
    viss_izsniegtais = db.execute("""
        SELECT 
            lietotaji.lietotajvards, 
            inventars.nosaukums, 
            inventars.veids, 
            izsniegtais.datums_izsniegts 
        FROM izsniegtais
        JOIN lietotaji ON izsniegtais.lietotajs_ID = lietotaji.ID
        JOIN inventars ON izsniegtais.inventars_ID = inventars.ID
        ORDER BY izsniegtais.datums_izsniegts DESC
    """).fetchall()
    db.close()
    
    return render_template('izsniegtais_inventars.html', saraksts=viss_izsniegtais)

if __name__ == "__main__":
    app.run(debug=True)