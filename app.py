@app.route('/')
def home():
    return render_template('index.html')
from flask import Flask, request, jsonify, render_template, redirect, url_for
import sqlite3, stripe, datetime

# --- Kreiranje baze ako ne postoji ---
conn = sqlite3.connect('database.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT UNIQUE,
        device_key TEXT,
        playlist TEXT,
        trial_start TEXT,
        paid_until TEXT,
        paid_type TEXT
    )
''')
conn.commit()
conn.close()
# --- Kraj dijela za bazu ---

app = Flask(__name__)
