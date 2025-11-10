from flask import Flask, render_template, request, redirect, jsonify
import stripe, sqlite3

app = Flask(__name__)  # ⬅️ ovo mora postojati!
from flask import Flask, render_template, request, redirect, jsonify
import stripe, sqlite3

app = Flask(__name__)  # ⬅️ ovo mora postojati!
@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "Bet TV Plus - Lifetime Access",
                        },
                        "unit_amount": 799,  # 7.99 € u centima
                    },
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=request.host_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.host_url + "cancel",
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return str(e)
