from flask import Flask, render_template, request, redirect, jsonify
import stripe
import sqlite3
import os

app = Flask(__name__)

# Učitaj tajne ključeve iz .env fajla ili ih direktno stavi ovde
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_live_tvoj_pravi_secret_key")
PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "pk_live_tvoj_pravi_public_key")

# Baza za aktivacije (ako je koristiš)
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
    return render_template('index.html', public_key=PUBLIC_KEY)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': 'BetTV Plus Lifetime License',
                    },
                    'unit_amount': 799,  # 7.99€ = 799 centi
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'success',
            cancel_url=request.host_url + 'cancel',
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 400

@app.route('/success')
def success():
    return "Uplata uspješna! Hvala što podržavaš BetTV Plus."

@app.route('/cancel')
def cancel():
    return "Uplata otkazana."

if __name__ == '__main__':
    app.run(debug=True)
