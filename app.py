from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Aplikacija radi!"

if __name__ == '__main__':
    app.run(debug=True)
