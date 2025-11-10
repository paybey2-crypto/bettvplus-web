
from flask import Flask, render_template, request, redirect, jsonify
import stripe
import sqlite3
import os

app = Flask(__name__)

# Učitaj Stripe ključ iz .env fajla
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Inicijalizacija baze
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mac TEXT UNIQUE,
            playlist TEXT,
            paid INTEGER DEFAULT 0
        )
    ''')
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

    # Kreiraj Stripe checkout sesiju za 7.99€
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {
                    'name': 'Bet TV Plus - Lifetime Activation',
                },
                'unit_amount': 799,  # 7.99 € = 799 centi
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.host_url + 'success?mac=' + mac + '&playlist=' + playlist,
        cancel_url=request.host_url + 'cancel',
    )
    return redirect(session.url, code=303)

@app.route('/success')
def success():
    mac = request.args.get('mac')
    playlist = request.args.get('playlist')

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO activations (mac, playlist, paid) VALUES (?, ?, 1)", (mac, playlist))
    conn.commit()
    conn.close()

    return "Uspješna aktivacija za MAC: " + mac

@app.route('/cancel')
def cancel():
    return "Plaćanje otkazano."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
