
from flask import Flask, render_template, request, send_from_directory

app = Flask(__name__)

# Glavna stranica (login forma)
@app.route('/')
def index():
    return render_template('index.html')

# Obrada prijave
@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac')
    code = request.form.get('code')

    # Jednostavna provjera
    if mac == '59:d9:5d:f3:8c:cf' and code == '943169':
        return render_template('success.html')
    else:
        return render_template('error.html')

# Ruta za preuzimanje APK fajla
@app.route('/download')
def download_apk():
    return send_from_directory(
        directory='.', 
        path='BETTVPLUS-PRO.apk', 
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)
