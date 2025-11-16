from flask import Flask, request, jsonify, send_from_directory
import stripe
import os

app = Flask(__name__)

# Stripe API ključ
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Tvoji price ID-evi
PRICE_YEARLY = "price_1STQ3XFZy9W3RRoZhswoUF5R"
PRICE_LIFETIME = "price_1STurmFZy9W3RRoZVZ0RSLAX"

YOUR_DOMAIN = "https://bettvplus-web-k3n2.onrender.com"

@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.json
    mac = data.get("mac")
    plan = data.get("plan")  # "yearly" ili "lifetime"

    if not mac or not plan:
        return jsonify({"error": "MAC ili plan nedostaje"}), 400

    # Biranje price ID-a
    if plan == "yearly":
        price_id = PRICE_YEARLY
    elif plan == "lifetime":
        price_id = PRICE_LIFETIME
    else:
        return jsonify({"error": "Nepoznat plan"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{YOUR_DOMAIN}/success.html",
            cancel_url=f"{YOUR_DOMAIN}/cancel.html",
            metadata={"mac": mac, "plan": plan}
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
