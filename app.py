from flask import Flask, render_template, request

app = Flask(__name__)

# ---------------------------
# HOME PAGE
# ---------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------
# ADMIN PANEL (LOGIN)
# URL: /admin-LIVNJAK1978
# ---------------------------
@app.route("/admin-LIVNJAK1978", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Možeš promijeniti login podatke
        if username == "admin" and password == "Livnjak1978@@":
            return "Uspješno logovan!"

        return "Pogrešan username ili password!"

    return render_template("admin.html")


# ---------------------------
# STARTER
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
