from flask import Flask, render_template, request, redirect
import requests

app = Flask(__name__)

# ADMIN PODACI
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# -------------------------
#   INDEX
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------
#   PLAYER — Učitavanje kanala
# -------------------------
@app.route("/play")
def play():

    server_url = request.args.get("server_url")
    username = request.args.get("username")
    password = request.args.get("password")

    if not server_url or not username or not password:
        return "Nedostaje server URL, username ili password!"

    # Xtream Codes API
    api_url = f"{server_url}/player_api.php?username={username}&password={password}"

    try:
        response = requests.get(api_url, timeout=10)

        if response.status_code != 200:
            return "Greška: Server nije odgovorio."

        data = response.json()

        if "user_info" not in data:
            return "Login neispravan ili API ne radi!"

        if data["user_info"]["auth"] != 1:
            return "Pogrešan username ili password!"

        channels = data.get("live_streams", [])
        categories = data.get("categories", [])

        return render_template(
            "play.html",
            channels=channels,
            categories=categories,
            server_url=server_url,
            username=username,
            password=password
        )

    except Exception as e:
        return f"Greška pri spajanju: {str(e)}"


# -------------------------
#   ADMIN LOGIN
# -------------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return render_template("admin.html")
        else:
            return "Pogrešan username ili password!", 401

    return render_template("login.html")


# -------------------------
#   START
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
