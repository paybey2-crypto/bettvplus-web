from flask import Flask, render_template, request, redirect
import stripe
import os

app = Flask(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

PRICE_YEAR = "price_1STQ3XFZy9W3RRoZhswoUF5R"
PRICE_LIFETIME = "price_1STurmFZy9W3RRoZVZ0RSLAX"

YOUR_DOMAIN = "https://bettvplus-web-k3n2.onrender.com"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    mac = request.form.get("mac")
    product_type = request.form.get("product")  # year / lifetime

    if product_type == "year":
        price_id = PRICE_YEAR
    else:
        price_id = PRICE_LIFETIME

    checkout_session = stripe.checkout.Session.create(
        success_url=f"{YOUR_DOMAIN}/success?mac={mac}",
        cancel_url=YOUR_DOMAIN,
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price": price_id,
            "quantity": 1
        }],
        metadata={"mac": mac, "product": product_type}
    )

    return redirect(checkout_session.url, code=303)


@app.route("/success")
def success():
    return "Uspješna uplata! MAC je aktiviran."
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
