from flask import Flask, render_template, request, redirect, jsonify
import stripe
from datetime import datetime, timedelta
import os

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

# BAZA – privremeno u memoriji (može se prebaciti u SQLite kasnije)
mac_database = {}


def mac_expired(mac):
    if mac not in mac_database:
        return True
    expiry = mac_database[mac]["expiry"]
    return expiry != "lifetime" and expiry < datetime.now()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/check_mac", methods=["POST"])
def check_mac():
    mac = request.form.get("mac")
    code = request.form.get("code")

    if mac in mac_database:
        if mac_expired(mac):
            return redirect(f"/pay?mac={mac}")
        return render_template("index.html", message="MAC uspješno provjeren!")
    else:
        return render_template("index.html", message="MAC nije registriran. Kupi paket.", redirect_pay=True)


@app.route("/pay")
def pay():
    mac = request.args.get("mac")
    if not mac:
        return "MAC adresa nije proslijeđena", 400
    return render_template("pay.html", mac=mac, public_key=PUBLIC_KEY)


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    mac = request.form["mac"]
    package = request.form["package"]

    if package == "year":
        price_id = "price_1YEAR_STRIPE"     # OVDJE UBACI PRAVI PRICE ID
    elif package == "lifetime":
        price_id = "price_1LIFE_STRIPE"     # OVDJE UBACI PRAVI PRICE ID
    else:
        return "Nevažeći paket", 400

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1
        }],
        mode="payment",
        success_url=f"https://{request.host}/success?mac={mac}&package={package}",
        cancel_url=f"https://{request.host}/pay?mac={mac}"
    )

    return jsonify({"id": session.id})


@app.route("/success")
def success():
    mac = request.args.get("mac")
    package = request.args.get("package")

    if package == "year":
        expiry = datetime.now() + timedelta(days=365)
    else:
        expiry = "lifetime"

    mac_database[mac] = {
        "expiry": expiry,
        "status": "Aktiviran"
    }

    return render_template("success.html", mac=mac, package=package)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        mac = request.form["mac"]
        duration = request.form["duration"]

        if duration == "1_year":
            expiry = datetime.now() + timedelta(days=365)
        else:
            expiry = "lifetime"

        mac_database[mac] = {
            "expiry": expiry,
            "status": "Aktiviran"
        }

    return render_template("admin.html", macs=mac_database)


if __name__ == "__main__":
    app.run(debug=True)
