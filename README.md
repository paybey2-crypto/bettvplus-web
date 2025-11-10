# BetTVPlus Web - jednostavan aktivacijski web sa Stripe plaćanjem

## Što je uključeno
- Flask backend (`app.py`)
- Stripe Checkout integracija
- SQLite DB (`data.db` će se kreirati na prvom pokretanju)
- Jednostavan player endpoint

## Postavljanje (lokalno)
1. Postavi env varijable:
   - `STRIPE_SECRET_KEY` = tvoj Stripe secret key
   - `STRIPE_PUBLIC_KEY` = tvoj Stripe publishable key
2. Instaliraj dependency:
   ```bash
   pip install -r requirements.txt

