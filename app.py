import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify
import stripe

app = Flask(__name__)

# Učitaj Stripe ključeve iz environment varijabli
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")  # tajni ključ
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")  # javni ključ za JS

# Cijena u centima (EUR): 7.99€ -> 799
PRICE_EUR_CENTS = 799

DB_PATH = "data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS activations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT UNIQUE,
        playlist TEXT,
        paid INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template("index.html", stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/activate', methods=['POST'])
def activate():
    """
    Endpoint koji prima MAC i playlist, kreira (ili ažurira) record u bazi i
    pokreće Stripe Checkout sesiju.
    """
    mac = request.form.get('mac', '').strip()
    playlist = request.form.get('playlist', '').strip()

    if not mac or not playlist:
        return "MAC i playlist su obavezni.", 400

    # Spremi ili ažuriraj aktivaciju (paid=0 dok se ne plati)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO activations (mac, playlist, paid) VALUES (?, ?, COALESCE((SELECT paid FROM activations WHERE mac = ?), 0))",
                  (mac, playlist, mac))
        conn.commit()
    finally:
        conn.close()

    # Kreiraj Stripe Checkout sesiju sa metadata mac -> vratit ćemo ga u success route
    YOUR_DOMAIN = request.host_url.rstrip('/')  # npr. https://betvplus-web.onrender.com
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Bet TV Plus - Lifetime activation ({mac})',
                    },
                    'unit_amount': PRICE_EUR_CENTS,
                },
                'quantity': 1,
            }],
            metadata={'mac': mac},
            success_url=YOUR_DOMAIN + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=YOUR_DOMAIN + '/',
        )
    except Exception as e:
        return str(e), 500

    # Vratimo id sesije da JS pozove stripe.redirectToCheckout
    return jsonify({'id': session.id})

@app.route('/success')
def success():
    """
    Nakon povratka sa Stripe Checkout-a (success_url) dohvatimo sesiju i
    ako je plaćeno, ažuriramo paid = 1 za taj mac.
    """
    session_id = request.args.get('session_id')
    if not session_id:
        return "Nema session_id.", 400

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        return f"Greška pri dohvatu sesije: {e}", 500

    mac = session.metadata.get('mac') if session.metadata else None
    payment_status = session.payment_status  # 'paid' kad je plaćeno

    if mac and payment_status == 'paid':
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE activations SET paid = 1 WHERE mac = ?", (mac,))
        conn.commit()
        conn.close()

    return render_template("success.html", mac=mac, paid=(payment_status == 'paid'))

@app.route('/player/<mac>')
def player(mac):
    """
    Jednostavna stranica koja prikazuje playlist za taj mac i (ako paid=1) 
    ponaša se kao otključan player.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT playlist, paid FROM activations WHERE mac = ?", (mac,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "MAC nije aktiviran ili ne postoji.", 404

    playlist, paid = row
    return render_template("player.html", playlist=playlist, paid=bool(paid), mac=mac)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
