
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Kreiraj bazu ako ne postoji
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac TEXT UNIQUE,
                    playlist TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/activate', methods=['POST'])
def activate():
    mac = request.form.get('mac')
    playlist = request.form.get('playlist')

    if not mac or not playlist:
        return "Greška: MAC i playlist su obavezni podaci.", 400

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO activations (mac, playlist) VALUES (?, ?)", (mac, playlist))
        conn.commit()
    except sqlite3.IntegrityError:
        return "Ovaj MAC je već aktiviran.", 400
    finally:
        conn.close()

    return "Uređaj uspješno aktiviran!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

