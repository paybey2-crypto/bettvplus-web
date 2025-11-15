
from flask import Flask, render_template, request, redirect, session
import os

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = "supersecretkey"

# -----------------------
# LOGIN STRANICA
# -----------------------
@app.route("/")
def index():
    return render_template("index.html")

# -----------------------
# LOGIN HANDLER
# -----------------------
@app.route("/login", methods=["POST"])
def login():
    mac = request.form.get("mac")
    pin = request.form.get("pin")
    dns = request.form.get("dns")

    # PRIVREMENO dozvoli sve logine
    if mac and pin and dns:
        session["user"] = mac
        return redirect("/dashboard")
    else:
        return "Greška: moraš sve unijeti!"

# -----------------------
# DASHBOARD
# -----------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", mac=session["user"])

# -----------------------
# LOGOUT
# -----------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -----------------------
# RUN
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
