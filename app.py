from flask import Flask, render_template, request, redirect
import stripe
import os

app = Flask(__name__)

# Učitavanje environment varijabli
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_YEAR = os.getenv("PRICE_YEAR")
PRICE_LIFETIME = os.getenv("PRICE_LIFETIME")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")


@app.route("/")
def index():
    return render_template("index.html", 
                           stripe_public_key=STRIPE_PUBLIC_KEY,
                           price_year=PRICE_YEAR,
                           price_lifetime=PRICE_LIFETIME)


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    price_id = request.form.get("price_id")

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://bettvplus-web-k3n2.onrender.com/success",
            cancel_url="https://bettvplus-web-k3n2.onrender.com/cancel",
        )

        return redirect(session.url, code=303)

    except Exception as e:
        return str(e), 400


@app.route("/success")
def success():
    return "<h1>Uplata uspješna ✔️</h1>"


@app.route("/cancel")
def cancel():
    return "<h1>Uplata otkazana ❌</h1>"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
