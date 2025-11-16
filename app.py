from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/activate", methods=["POST"])
def activate():
    mac = request.form.get("mac")
    code = request.form.get("code")

    if not mac:
        return jsonify({"status": "error", "message": "MAC adresa je obavezna!"}), 400

    # Ovdje ide tvoja logika provjere MAC-a ili generiranja liste
    # Za sada samo vraćamo demo odgovor
    return jsonify({
        "status": "success",
        "message": "MAC uspješno provjeren!",
        "mac": mac,
        "code": code
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
    @app.route("/activate/<mac>")
def activate(mac):
return render_template("activate.html", mac=mac)
