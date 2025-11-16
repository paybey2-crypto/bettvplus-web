from flask import Flask, request, jsonify, render_template
import stripe

app = Flask(__name__)

# ------------------------------------
#  UNESI OVDJE SVOJE STRIPE KLJUČEVE
# ------------------------------------
stripe.api_key = "sk_live_TVOJ_SECRET_KEY"
STRIPE_PUBLIC_KEY = "pk_live_TVOJ_PUBLIC_KEY"

# ------------------------------------
# HOME PAGE – MAC + KOD + UPLATA
# ------------------------------------
@app.route("/")
def index():
    return render_template("index.html", public_key=STRIPE_PUBLIC_KEY)

# ------------------------------------
# STRIPE CHECKOUT – API
# ------------------------------------
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()

    mac = data.get("mac")
    code = data.get("code")
    price_id = data.get("priceId")

    if not mac or not code or not price_id:
        return jsonify({"error": "Nedostaju podaci"}), 400

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1
        }],
        mode="payment",
        success_url="https://YOUR_DOMAIN/success?mac=" + mac,
        cancel_url="https://YOUR_DOMAIN/cancel",
        metadata={
            "mac": mac,
            "code": code
        }
    )

    return jsonify({"sessionId": session.id})

# ------------------------------------
# USPJEŠNA UPLATA
# ------------------------------------
@app.route("/success")
def success():
    mac = request.args.get("mac")

    # OVDE SE AKTIVIRA MAC (ubaci kasnije u bazu)
    # activate_mac(mac)

    return render_template("success.html", mac=mac)

# ------------------------------------
# OTKAZANA UPLATA
# ------------------------------------
@app.route("/cancel")
def cancel():
    return render_template("cancel.html")

# ------------------------------------
# RUN
# ------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
