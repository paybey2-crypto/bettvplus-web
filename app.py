from flask import Flask, render_template, request, redirect, jsonify
import sqlite3, stripe

app = Flask(__name__)

stripe.api_key = "pk_live_51S1UQSFZy9W3RRoZSsCTntCqymYTneZKjtndO5vOB7cmw7bNgLvFABjQDTcaZrt8xFbdtbDbBwpHZxUcPUK72UXZ00yg9sjrO2"  # <- Ovdje zalijepi svoj ključ

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

    # Napravi Stripe checkout sesiju
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': f'Bet TV Plus aktivacija ({mac})'},
                'unit_amount': 500,  # 5.00 EUR u centima
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=f'http://localhost:5000/payment_success?mac={mac}&playlist={playlist}',
        cancel_url='http://localhost:5000/',
    )

    return redirect(session.url, code=303)

@app.route('/payment_success')
def payment_success():
    mac = request.args.get('mac')
    playlist = request.args.get('playlist')

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO activations (mac, playlist, paid) VALUES (?, ?, 1)", (mac, playlist))
    conn.commit()
    conn.close()

    return f"<h2>MAC {mac} je uspješno aktiviran!</h2><a href='/player?mac={mac}'>Otvori player</a>"

@app.route('/get_playlist')
def get_playlist():
    mac = request.args.get('mac')
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT playlist FROM activations WHERE mac=? AND paid=1", (mac,))
    row = c.fetchone()
    conn.close()
    return jsonify({'playlist': row[0] if row else None})

@app.route('/player')
def player():
    return render_template('player.html')

if __name__ == '__main__':
    app.run(debug=True)
