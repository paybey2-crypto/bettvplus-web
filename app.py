import os
import stripe
from flask import Flask, render_template, request, redirect, jsonify
import sqlite3

app = Flask(__name__)

# Učitaj Stripe ključeve iz .env fajla
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# Inicijalizacija baze
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()



if __name__ == '__main__':
    app.run(debug=True)
