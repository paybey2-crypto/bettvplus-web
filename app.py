from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
import os, json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change_this_secret")

DB_FILE = "db.json"   # spremište mac+pin

# Helper: učitaj db (ako ne postoji, kreiraj s primjerom)
def load_db():
    if not os.path.exists(DB_FILE):
        example = {
            "devices": {
                "59:d9:5d:f3:8c:cf": "943169"
            }
        }
        with open(DB_FILE, "w") as f:
            json.dump(example, f, indent=2)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    mac = request.form.get("mac", "").strip()
    code = request.form.get("code", "").strip()
    db = load_db()
    devices = db.get("devices", {})
    # jednostavna provjera
    if mac and code and mac in devices and devices[mac] == code:
        return render_template("success.html", mac=mac)
    else:
        # možeš flash poruku i vratiti se na index
        flash("MAC adresa ili PIN nisu ispravni.")
        return redirect(url_for("index"))

# Ruta za preuzimanje APK fajla (stavi apk u static/ folder)
@app.route("/download")
def download_apk():
    # ime fajla koje si uploadao u static/
    apk_name = "BETTVPLUS-PRO.apk"
    static_dir = os.path.join(app.root_path, "static")
    if not os.path.exists(os.path.join(static_dir, apk_name)):
        return "APK not found. Upload it to the static folder.", 404
    return send_from_directory(static_dir, apk_name, as_attachment=True)

# Admin ruta za upravljanje device > pin (zahtijeva admin_key param kao jednostavna zaštita)
# POZOR: ovo je minimalna zaštita za brzo testiranje. Ne koristiti bez TLS/pravog auth-a u produkciji.
ADMIN_KEY = os.environ.get("ADMIN_KEY", "supersecretadmin")

@app.route("/admin", methods=["GET","POST"])
def admin():
    key = request.args.get("key","")
    if key != ADMIN_KEY:
        return "Access denied. Provide ?key=ADMIN_KEY", 403

    db = load_db()
    if request.method == "POST":
        action = request.form.get("action")
        mac = request.form.get("mac","").strip()
        pin = request.form.get("pin","").strip()
        if action == "add" and mac and pin:
            db.setdefault("devices", {})[mac] = pin
            save_db(db)
            flash(f"Added/updated {mac}")
        elif action == "delete" and mac:
            if mac in db.get("devices", {}):
                del db["devices"][mac]
                save_db(db)
                flash(f"Deleted {mac}")
        return redirect(url_for("admin", key=key))
    return render_template("admin.html", db=db)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
    
{
  "devices": {
    "59:d9:5d:f3:8c:cf": "943169"
  }
}
