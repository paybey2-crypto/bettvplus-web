from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ovdje ide tvoj login/aktivacijski kod
        return "Prijava uspješna"
    else:
        return render_template('index.html')
