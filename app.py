
import os
import json
from flask import Flask, request, render_template, redirect, url_for, jsonify
import stripe
from datetime import datetime, timedelta

app = Flask(__name__)

# Stripe init
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

ACTIVATED_FILE = "activated_macs.json"

# Helper: load/save activated macs
def load_activated():
    if not os.path.exists(ACTIVATED_FILE):
        return {}
    with open(ACTIVATED_FILE, "r") as f:
        return json.load(f)

def save_activated(data):
    with open(ACTIVATED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def activate_mac(mac, package):
    """package: 'year' or 'lifetime'"""
    data = load_activated()
    now = datetime.utcnow().isoformat()
    if package == "year":
        expires = (datetime.utcnow() + timedelta(days=365)).isoformat()
    else:
        expires = None  # lifetime has no expiry
    # store entry
    data[mac.lower()] = {
        "activated_at": now,
        "package": package,
        "expires_at": expires
    }
    save_activated(data)

def is_mac_active(mac):
    data = load_activated()
    rec = data.get(mac.lower())
    if not rec:
        return False
    if rec.get("expires_at"):
        exp = datetime.fromisoformat(rec["expires_at"])
        return datetime.utcnow() < exp
    return True

# ---- Routes ----

@app.route('/')
def index():
    return render_template('index.html', key=STRIPE_PUBLISHABLE_KEY)

@app.route('/login', methods=["POST"])
def login():
    mac = request.form.get('mac', '').strip().lower()
    pin = request.form.get('pin', '').strip()
    dns = request.form.get('dns', '').strip()
    # if mac active and pin correct: do your normal check
    if is_mac_active(mac) and pin == "YOUR_PIN_CHECK":  # <-- prilagodi logiku pin provjere
        return render_template('success.html', mac=mac)
    else:
        return render_template('index.html', error="MAC or PIN not valid", key=STRIPE_PUBLISHABLE_KEY)

# Create checkout session
@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    mac = request.form.get('mac').strip().lower()
    package = request.form.get('package')  # 'year' ili 'lifetime'
    if not mac or package not in ("year", "lifetime"):
        return jsonify({"error":"invalid"}), 400

    # Define price in cents (Euro)
    if package == "year":
        amount = 799  # €7.99 -> 799 cents
        desc = "BetTVPlus - 1 year activation"
    else:
        amount = 1199
        desc = "BetTVPlus - Lifetime activation"

    # Create a Checkout Session
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': desc,
                    },
                    'unit_amount': amount,
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=BASE_URL + '/checkout-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=BASE_URL + '/checkout-cancel',
            metadata={
                "mac": mac,
                "package": package
            }
        )
        return jsonify({'id': session.id})
    except Exception as e:
        return jsonify(error=str(e)), 500

# Simple success page
@app.route('/checkout-success')
def checkout_success():
    return render_template('checkout_success.html')

@app.route('/checkout-cancel')
def checkout_cancel():
    return render_template('checkout_cancel.html')

# Stripe webhook to listen for payment success
@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return '', 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # session.metadata contains mac and package
        mac = session.get('metadata', {}).get('mac')
        package = session.get('metadata', {}).get('package')
        payment_status = session.get('payment_status')

        if mac and package and payment_status == 'paid':
            # Activate mac
            activate_mac(mac, package)
            # optionally record payment details, e.g. session.id
    return '', 200

# route to download apk (if you want)
@app.route('/download')
def download_apk():
    # If you have APK stored in static folder, return it or generate URL
    return redirect(url_for('static', filename='BETTVPLUS-PRO.apk'))

if __name__ == "__main__":
    app.run(debug=True)
