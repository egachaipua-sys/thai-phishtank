# Thai PhishTank

A phishing URL detection system tailored for Thai websites. It combines a machine-learning model with Google Safe Browsing to classify URLs as safe or phishing, maintains community-driven black/white lists, and exposes a web UI plus REST API.

## Architecture

The project is split into two services that share a MongoDB instance:

- **fastapi/** — Prediction API (FastAPI + Uvicorn/Gunicorn). Performs feature extraction, runs the ML model (`mlp99.31`), checks Google Safe Browsing, performs WHOIS and DNS lookups, and updates the black/white lists.
- **flaskweb/** — User-facing web app (Flask + Jinja templates). Handles auth, dashboards, reporting flows, language switching (TH/EN), and proxies requests to the FastAPI service.

```
thai-phishtank/
├── fastapi/      # ML prediction + admin/verification API
│   ├── app/
│   │   ├── prediction_api.py     # FastAPI routes
│   │   ├── mlengine/             # ML model + feature extractor
│   │   └── hosting_platforms.json
│   ├── scripts/create_indexes.py
│   └── requirements.txt
└── flaskweb/     # Web frontend
    ├── app/
    │   ├── controllers/          # auth, api, phish, view blueprints
    │   ├── models/
    │   ├── templates/
    │   └── static/
    └── requirements.txt
```

## Features

- ML-based phishing classification using a pre-trained MLP model
- Google Safe Browsing API cross-check
- Automatic blacklisting on unanimous or Safe-Browsing-confirmed phishing detections
- Whitelist with hosting-platform awareness (e.g. blogspot.com, vercel.app require full-URL match)
- Auto-whitelist for official Thai TLDs (`.go.th`, `.ac.th`, `.or.th`, `.mi.th`)
- WHOIS enrichment with country-code normalization for map visualizations
- IDN/Punycode support for Thai domain names (e.g. `ธกส.ไทย`)
- TTL caches for WHOIS (1h) and online-status checks (5m)
- Admin verification endpoint for manual review
- Bilingual web UI (Thai/English)

## Requirements

- Python 3.10+
- MongoDB 5.0+
- A Google Safe Browsing API key

## Setup

### 1. Clone and create configs

```bash
cp fastapi/config_app.ini.example fastapi/config_app.ini
cp flaskweb/config_app.ini.example flaskweb/config_app.ini
```

Fill in MongoDB URIs, the Google Safe Browsing key, mail credentials, and your domain name in each `config_app.ini`.

### 2. Install dependencies

```bash
# FastAPI service
cd fastapi
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Flask web app
cd ..\flaskweb
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create MongoDB indexes

```bash
cd fastapi
python scripts/create_indexes.py
```

### 4. Run the services

```bash
# Terminal 1 — FastAPI (default :8000)
cd fastapi
uvicorn app.prediction_api:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Flask web (default :5000)
cd flaskweb
python -m app.wsgi
```

Open `http://localhost:5000`.

## Configuration

**fastapi/config_app.ini**

| Section | Key | Description |
| --- | --- | --- |
| DATABASE | MONGO_DETAILS | MongoDB connection URI |
| DATABASE | DATABASE_NAME | Database name (default `phishtank_th`) |
| DATABASE | USER_COLLECTION | API key user collection |
| DATABASE | BLACK_LIST | Phishing URL collection |
| DATABASE | WHITE_LIST | Safe URL collection |
| API_KEY | API_KEY | Admin API key |
| DOMAIN_NAME | DOMAIN_NAME | Public domain used in `phish_detail_url` |
| GOOGLE | SAFE_BROWSING_API_KEY | Google Safe Browsing key |
| GOOGLE | SAFE_BROWSING_URL | Safe Browsing endpoint |

**flaskweb/config_app.ini**

| Section | Key | Description |
| --- | --- | --- |
| app | SECRET_KEY | Flask session secret |
| database | MONGO_URI / DB_NAME | MongoDB connection |
| email | MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD | SMTP for notifications |
| api | GOOGLE_SAFE_BROWSING_KEY, API_KEY | API credentials |

## API

All endpoints require an `api_key` query parameter.

### `POST /api/phishing-url`

Classify a URL. Returns one of `safe`, `phishing`, `split` (sources disagree), `offline`, `not_exist`, or `error`.

```bash
curl -X POST "http://localhost:8000/api/phishing-url?url=https://example.com&api_key=USER_KEY"
```

### `POST /api/verifited-url` (admin)

Manually verify a URL as phishing. Adds or updates the blacklist record.

```bash
curl -X POST "http://localhost:8000/api/verifited-url?url=https://bad.example&api_key=ADMIN_KEY"
```

### `GET /api/cache-status` (admin)

Inspect WHOIS and online-status cache sizes.

### `POST /api/clear-cache` (admin)

Clear all in-memory caches.

## Detection logic

For each URL the prediction API runs:

1. **Format check** — must have a valid TLD or be an IP literal.
2. **Whitelist check** — full URL match passes immediately; domain match passes only if the domain is not a hosting platform listed in `hosting_platforms.json`.
3. **Blacklist check** — return stored record if matched.
4. **Liveness** — DNS lookup (with IDN→Punycode) then HTTP probe. Returns `not_exist` or `offline` if unreachable.
5. **Google Safe Browsing** — if it flags the URL, auto-blacklist and return.
6. **ML model** (`app/mlengine/mlp99.31`) — extract features and predict.
7. **Reconcile** — combine model and Safe Browsing results into `unanimous`, `split`, or `our_system_only` responses; blacklist phishing and whitelist unanimous-safe verdicts.

## License

See repository for license information.
