print("Primljen zahtjev za login")
print("MAC:", mac, "CODE:", code)
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac')
    code = request.form.get('code')

    if not mac or not code:
        return render_template('error.html', message="Nedostaju podaci za prijavu.")

    return render_template('success.html', mac=mac)

if __name__ == '__main__':
    app.run(debug=True)
