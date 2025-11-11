
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "tajna_kljuc_za_sesije"

# --- Baza ---
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            dns_url TEXT,
            active INTEGER DEFAULT 1
        )
        """)
init_db()

# --- Login zahtjev ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# --- Admin zahtjev ---
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get("username") != "admin":
            flash("Samo admin može pristupiti ovom dijelu.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# --- Login stranica ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        dns = request.form["dns"]

        with sqlite3.connect("users.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=? AND active=1", (username, password))
            user = cur.fetchone()

        if user:
            session["username"] = username
            session["dns_url"] = dns
            flash("Prijava uspješna!")
            return redirect(url_for("player"))
        else:
            flash("Neispravno korisničko ime, lozinka ili je račun blokiran.")
            return redirect(url_for("login"))

    return render_template("login.html")

# --- Player stranica ---
@app.route("/player")
@login_required
def player():
    dns_url = session.get("dns_url", "")
    return render_template("player.html", username=session["username"], dns_url=dns_url)

# --- Admin panel ---
@app.route("/admin")
@admin_required
def admin_panel():
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, dns_url, active FROM users")
        users = cur.fetchall()
    return render_template("admin.html", users=users)

# --- Blokiraj / Obriši korisnika ---
@app.route("/toggle_user/<int:user_id>")
@admin_required
def toggle_user(user_id):
    with sqlite3.connect("users.db") as conn:
        cur = conn.cursor()
        cur.execute("SELECT active FROM users WHERE id=?", (user_id,))
        status = cur.fetchone()[0]
        new_status = 0 if status == 1 else 1
        cur.execute("UPDATE users SET active=? WHERE id=?", (new_status, user_id))
        conn.commit()
    flash("Korisnik ažuriran.")
    return redirect(url_for("admin_panel"))

@app.route("/delete_user/<int:user_id>")
@admin_required
def delete_user(user_id):
    with sqlite3.connect("users.db") as conn:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    flash("Korisnik obrisan.")
    return redirect(url_for("admin_panel"))

# --- Odjava ---
@app.route("/logout")
def logout():
    session.clear()
    flash("Odjavljeni ste.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
