@app.route('/play')
def play():
    username = request.args.get("username")
    password = request.args.get("password")

    if not username or not password:
        return "Nedostaje username ili password!", 400

    stream_url = f"http://anotv.org:80/get.php?username={username}&password={password}&type=m3u_plus&output=ts"

    return render_template("player.html", stream_url=stream_url)
