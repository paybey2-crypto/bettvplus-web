@app.route('/admin/upload', methods=['POST'])
def admin_upload():
    mac = request.form.get("mac")
    pin = request.form.get("pin")
    dns = request.form.get("dns")
    file = request.files.get("playlist")

    if not (mac and pin and dns and file):
        return "Missing data", 400

    # 1️⃣ Spremi playlist fajl
    filename = secure_filename(file.filename)
    file.save(os.path.join("playlists", filename))

    # 2️⃣ Dodaj korisnika u bazu (aktivacija 7 dana)
    active_until = datetime.now() + timedelta(days=7)

    db.execute(
        "INSERT INTO users (mac, pin, dns, active_until, blocked) VALUES (?, ?, ?, ?, ?)",
        (mac, pin, dns, active_until, 0)
    )
    db.commit()

    return redirect("/admin?msg=Korisnik+kreiran+i+playlist+uploadan")
