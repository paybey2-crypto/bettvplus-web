import os
import sqlite3
import stripe
import secrets
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Load stripe keys from environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
# Your domain (set on Render environment: e.g. https://your-app.onrender.com)
DOMAIN = os.getenv("DOMAIN", "http://localhost:5000")

DB_PATH = "data.db"

# Prices in cents
PRICES = {
    "lifetime": 1177,   # 11.77 EUR -> 1177 cents
    "year": 777         # 7.77 EUR -> 777 cents
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
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

def get_activation(mac):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,mac,device_key,playlist,trial_start,paid_until,paid_type FROM activations WHERE mac = ?", (mac,))
    row = c.fetchone()
    conn.close()
    return row

def create_activation(mac, playlist=None):
    device_key = secrets.token_hex(3)  # 6 hex chars ~ like 6-digit code
    trial_start = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO activations (mac, device_key, playlist, trial_start) VALUES (?,?,?,?)",
                  (mac, device_key, playlist, trial_start))
        conn.commit()
    except sqlite3.IntegrityError:
        # already exists
        pass
    conn.close()
    return get_activation(mac)

def update_playlist(mac, playlist):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE activations SET playlist = ? WHERE mac = ?", (playlist, mac))
    conn.commit()
    conn.close()

def mark_paid(mac, paid_type):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow()
    if paid_type == "lifetime":
        paid_until = (now + timedelta(days=36500)).isoformat()  # far future ~ lifetime
    else:
        paid_until = (now + timedelta(days=365)).isoformat()
    c.execute("UPDATE activations SET paid_until = ?, paid_type = ? WHERE mac = ?", (paid_until, paid_type, mac))
    conn.commit()
    conn.close()

def is_active(row):
    # row: (id, mac, device_key, playlist, trial_start, paid_until, paid_type)
    if not row:
        return False
    _, mac, device_key, playlist, trial_start, paid_until, paid_type = row
    now = datetime.utcnow()
    # check paid_until
    if paid_until:
        try:
            paid_dt = datetime.fromisoformat(paid_until)
            if paid_dt > now:
                return True
        except:
            pass
    # check trial (7 days)
    if trial_start:
        try:
            trial_dt = datetime.fromisoformat(trial_start)
            if now - trial_dt <= timedelta(days=7):
                return True
        except:
            pass
    return False

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', public_key=STRIPE_PUBLIC_KEY)

@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac', '').strip()
    device_key = request.form.get('device_key', '').strip()
    if not mac:
        return "Unesi MAC adresu", 400
    row = get_activation(mac)
    if row:
        # exists: check device key
        if device_key:
            if device_key == row[2]:
                # success login
                if is_active(row):
                    # active -> show player
                    return redirect(url_for('player', mac=mac))
                else:
                    # not active -> show payment/options
                    return redirect(url_for('pay_prompt', mac=mac))
            else:
                return "Device key netočan", 403
        else:
            # user did not supply device_key -> ask for it
            return render_template('need_key.html', mac=mac, device_key=row[2])
    else:
        # new MAC: create activation and give trial immediately
        new = create_activation(mac)
        # new is tuple
        return render_template('new_created.html', mac=new[1], device_key=new[2], playlist=new[3])

@app.route('/player/<mac>', methods=['GET', 'POST'])
def player(mac):
    row = get_activation(mac)
    if not row:
        return "MAC nije aktiviran. Unesite MAC i device key.", 404
    if not is_active(row):
        return redirect(url_for('pay_prompt', mac=mac))
    if request.method == 'POST':
        # update playlist
        playlist = request.form.get('playlist')
        update_playlist(mac, playlist)
        row = get_activation(mac)
    playlist = row[3]
    return render_template('player.html', mac=mac, device_key=row[2], playlist=playlist)

@app.route('/pay_prompt/<mac>', methods=['GET'])
def pay_prompt(mac):
    row = get_activation(mac)
    if not row:
        return "MAC nije pronađen", 404
    return render_template('pay.html', mac=mac, public_key=STRIPE_PUBLIC_KEY, prices=PRICES)

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    mac = data.get('mac')
    plan = data.get('plan')  # 'lifetime' or 'year'
    if plan not in PRICES:
        return jsonify({'error':'Neispravan plan'}), 400
    # create checkout session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'BetTVPlus - {plan}'
                    },
                    'unit_amount': PRICES[plan],
                },
                'quantity': 1
            }],
            metadata={'mac': mac, 'plan': plan},
            success_url=DOMAIN + url_for('checkout_success') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=DOMAIN + url_for('pay_prompt', mac=mac),
        )
        return jsonify({'url': session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/checkout-success')
def checkout_success():
    session_id = request.args.get('session_id')
    if not session_id:
        return "Nema session_id", 400
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        mac = session.metadata.get('mac')
        plan = session.metadata.get('plan')
        # mark as paid in DB
        if mac and plan:
            mark_paid(mac, plan)
            return render_template('success.html', mac=mac)
        else:
            return "Nije moguće dohvatiti podatke o plaćanju", 400
    except Exception as e:
        return f"Greška: {e}", 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
