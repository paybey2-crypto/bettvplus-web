
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ovdje ide logika prijave (provjera MAC, kod itd.)
        return render_template('success.html')
    else:
        return render_template('index.html')
