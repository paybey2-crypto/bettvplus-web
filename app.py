from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Aplikacija radi!"

if __name__ == '__main__':
    app.run(debug=True)
    from flask import render_template

@app.route('/')
def home():
    return render_template('index.html')

