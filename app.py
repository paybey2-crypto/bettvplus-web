from flask import Flask, render_template, request

app = Flask(__name__)

# ADMIN PODACI
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return render_template("admin.html")
        else:
            return "Pogrešan username ili password!", 401

    return render_template("login.html")


@app.route("/play")
def play():
    username = request.args.get("username")
    password = request.args.get("password")

    if not username or not password:
        return "Nedostaje username ili password!", 400

    # IPTV URL
    stream_url = f"http://anotv.org:80/get.php?username={username}&password={password}&type=m3u_plus&output=ts"

    return render_template("player.html", stream_url=stream_url)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
