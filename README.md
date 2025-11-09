# BetTVPlusWeb

Ovo je kompletan Flask projekt (na hrvatskom) koji:
- omogućuje javnu web stranicu za unos MAC adrese i upload `.m3u` / `.m3u8` playliste
- sprema fajlove u `uploads/` i zapisuje aktivacije u SQLite bazu `database.db`
- izlaže API endpointe za tvoju Android aplikaciju koji su zaštićeni API ključem:
  - `GET /api/check_mac/<mac>?api_key=YOUR_KEY`
  - `GET /api/get_playlist/<mac>?api_key=YOUR_KEY`

## Pokretanje lokalno

1. Napravi virtualno okruženje:
```
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

2. Instaliraj zahtjeve:
```
pip install -r requirements.txt
```

3. (Opcionalno) Generiraj API ključ:
```
python generate_api_key.py
```

4. Pokreni aplikaciju:
```
export ADMIN_PASSWORD="tvoja_admin_lozinka"   # Linux / macOS
set ADMIN_PASSWORD=tvoja_admin_lozinka         # Windows CMD
python app.py
```

Aplikacija će biti dostupna na `http://127.0.0.1:5000`.

## Deploy (Render / Heroku / VPS)
- Dodaj `requirements.txt` i `Procfile` u repo (već su prisutni).
- Na Render-u odaberi repo i postavi start command `gunicorn app:app`.
- Ne zaboravi postaviti `ADMIN_PASSWORD` kao env var u proizvodnom okruženju.

