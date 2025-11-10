from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac')
    code = request.form.get('code')

    # Provjera MAC adrese i koda
    if mac == '59:d9:5d:f3:8c:cf' and code == '38713':
        return render_template('success.html')
    else:
        return render_template('error.html')

if __name__ == '__main__':
    app.run(debug=True)
