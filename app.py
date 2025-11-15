from flask import Flask, render_template, request

app = Flask(__name__)

# ADMIN LOZINKE
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Livnjak1978@@"

@app.route('/')
def index():
    return render_template("index.html")

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
