from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    mac = request.form["mac"]
    pin = request.form["pin"]
    dns = request.form["dns"]

    return f"MAC: {mac}<br>PIN: {pin}<br>DNS: {dns}"

if __name__ == "__main__":
    app.run(debug=True)
