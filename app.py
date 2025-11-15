from flask import Flask, request, redirect, render_template, session
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "BETTVPLUS_SECRET_2024"

# ---------------------------
# TAJNI ADMIN LOGIN URL
# ---------------------------

ADMIN_URL = "/admin-LIVNJAK1978"
ADMIN_USER = "admin"
ADMIN_PASS = "Livnjak1978@@"

# ---------------------------
# ADMIN LOGIN
# ---------------------------

@app.route(ADMIN_URL, methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    # POST LOGIN
    user = request.form.get("username")
    password = request.form.get("password")

    if user == ADMIN_USER and password == ADMIN_PASS:
        session["admin"] = True
        return redirect("/admin-panel")

    return "Pogrešan login", 403


# ---------------------------
# ADMIN PANEL
# ---------------------------

@app.route("/admin-panel")
def admin_panel():
    if not session.get("admin"):
        return redirect(ADMIN_URL)

    return render_template("admin_panel.html")
