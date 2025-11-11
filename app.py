
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'bettvplus_secret_key'

# Kreiranje baze ako ne postoji
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            dns TEXT,
            active INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    # dodaj admin korisnika ako ne postoji
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, dns, active) VALUES (?, ?, ?, ?)",
                  ('admin', 'admin123', '', 1))
        conn.commit()
    conn.close()

# Prijava korisnika
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        dns = request.form['dns']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            if user[4] == 0:
                flash('Ovaj korisnik je blokiran.')
                return redirect(url_for('login'))
            session['username'] = username
            session['dns'] = dns
            if username == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('player'))
        else:
            flash('Neispravno korisničko ime ili lozinka.')
            return redirect(url_for('login'))
    return render_template('login.html')

# Player stranica
@app.route('/player')
def player():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('player.html', username=session['username'], dns_url=session['dns'])

# Admin panel
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if request.method == 'POST':
        new_username = request.form['new_username']
        new_password = request.form['new_password']
        new_dns = request.form['new_dns
