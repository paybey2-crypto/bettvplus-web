from flask import Flask, render_template, request, redirect

app = Flask(__name__)

ADMIN_PASSWORD = "LIVNJAK1978"

current_stream = "https://example.com/stream.m3u8"   # default

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/play", methods=["POST"])
def play():
    channel = request.form["channel"]
    return redirect(channel)

@app.route("/admin-LIVNJAK1978", methods=["GET", "POST"])
def admin():
    global current_stream

    if request.method == "POST":
        password = request.form.get("password")
        new_stream = request.form.get("new_stream")

        # LOGIN
        if password:
            if password == ADMIN_PASSWORD:
                return render_template("admin.html", logged_in=True, current_stream=current_stream)
            else:
                return render_template("admin.html", logged_in=False)

        # UPDATE STREAM
        if new_stream:
            current_stream = new_stream
            return render_template("admin.html", logged_in=True, current_stream=current_stream)

    return render_template("admin.html", logged_in=False)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
