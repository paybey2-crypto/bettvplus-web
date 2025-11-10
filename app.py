@app.route('/login', methods=['POST'])
def login():
    mac = request.form.get('mac')
    code = request.form.get('code')

    if not mac or not code:
        return render_template('error.html', message="Nedostaju podaci za prijavu.")

    return render_template('success.html', mac=mac)
