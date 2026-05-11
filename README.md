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

## Setup (development)

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

## Production deployment (Ubuntu)

Tested stack:

- MongoDB 7.0.18
- Python 3.12.3
- Nginx 1.24.0
- Certbot 2.9.0

The instructions below assume Ubuntu and a non-root user named `cls`. Substitute your own username, paths, and domain (`thaiphishtank.org`) throughout.

### 1. Place the source

Drop the project under `/home/<user>/phishtank_th` (via `git clone`, or `scp` a zip and unpack):

```bash
sudo apt update
sudo apt install -y zip unzip
unzip phishtank_th.zip && rm phishtank_th.zip
unzip backup.zip && rm backup.zip   # only if you have a database dump to restore
```

### 2. Install MongoDB 7.0.18

Add the MongoDB APT repository, install the pinned version, and hold it so unattended upgrades don't bump it:

```bash
curl -fsSL https://pgp.mongodb.com/server-7.0.asc \
  | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/mongodb-org-7.0.gpg

echo "deb [ arch=amd64,arm64 signed-by=/etc/apt/trusted.gpg.d/mongodb-org-7.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/7.0 multiverse" \
  | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt update
sudo apt install -y \
  mongodb-org=7.0.18 \
  mongodb-org-database=7.0.18 \
  mongodb-org-server=7.0.18 \
  mongodb-org-shell=7.0.18 \
  mongodb-org-mongos=7.0.18 \
  mongodb-org-tools=7.0.18

sudo apt-mark hold mongodb-org mongodb-org-database mongodb-org-server \
  mongodb-org-shell mongodb-org-mongos mongodb-org-tools

sudo systemctl enable --now mongod
```

**Backup / restore** the `phishtank_th` database:

```bash
sudo mongodump   --gzip --db phishtank_th --out backup
sudo mongorestore --gzip --db phishtank_th backup/phishtank_th
```

### 3. FastAPI service

Install Python tooling, create the venv, install requirements:

```bash
sudo apt install -y python3-pip python3-dev python3-venv \
  build-essential libssl-dev libffi-dev python3-setuptools

cd ~/phishtank_th/fastapi
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install -r requirements.txt
deactivate
```

Create `/etc/systemd/system/fastapi.service`:

```ini
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=cls
Group=www-data
WorkingDirectory=/home/cls/phishtank_th/fastapi
ExecStart=/home/cls/phishtank_th/fastapi/venv/bin/gunicorn -w 1 --max-requests 100 --max-requests-jitter 30 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.wsgi:app
LimitNOFILE=65535
LimitNPROC=infinity
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable --now fastapi
```

### 4. Swap and Flask service

Allocate 1 GB of swap so the worker doesn't OOM under load spikes, and persist it across reboots:

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

Install Flask dependencies:

```bash
cd ~/phishtank_th/flaskweb
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install -r requirements.txt
deactivate
```

Create `/etc/systemd/system/flaskweb.service`:

```ini
[Unit]
Description=Gunicorn instance to serve flaskweb
After=network.target

[Service]
User=cls
Group=www-data
WorkingDirectory=/home/cls/phishtank_th/flaskweb
Environment="PATH=/home/cls/phishtank_th/flaskweb/venv/bin"
ExecStart=/home/cls/phishtank_th/flaskweb/venv/bin/gunicorn --workers 1 --threads 4 --worker-class gthread --max-requests 100 --max-requests-jitter 30 --bind unix:flaskweb.sock -m 007 app.wsgi:app
Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable --now flaskweb
```

### 5. Nginx + SSL

Install Nginx, Certbot, and open the firewall:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo ufw allow 'Nginx Full'
sudo ufw allow 587               # SMTP submission, only if you send email from the host
```

Issue an SSL certificate (substitute your domain):

```bash
sudo certbot --nginx -d thaiphishtank.org
```

Create `/etc/nginx/sites-available/phishtank_th` — Nginx fronts both services, terminating TLS, sending `/api/` to FastAPI on `:8000` and everything else to the Flask Unix socket:

```nginx
server {
    listen 80;
    server_name thaiphishtank.org;

    location / {
        return 301 https://$host$request_uri;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}

server {
    listen 443 ssl;
    server_name thaiphishtank.org;

    ssl_certificate     /etc/letsencrypt/live/thaiphishtank.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/thaiphishtank.org/privkey.pem;

    location / {
        proxy_read_timeout    300s;
        proxy_connect_timeout 300s;
        proxy_pass http://unix:/home/cls/phishtank_th/flaskweb/flaskweb.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site, validate, and reload:

```bash
sudo ln -s /etc/nginx/sites-available/phishtank_th /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Nginx (running as www-data) needs traverse permission on the home dir
# to reach the Flask Unix socket.
sudo chmod 755 /home/cls

# Plain HTTP rule no longer needed once HTTPS is up.
sudo ufw delete allow 'Nginx HTTP'
```

### 6. Health checks and logs

```bash
# Service status
sudo systemctl status nginx
sudo systemctl status fastapi
sudo systemctl status flaskweb
sudo systemctl status mongod

# Live application logs (Ctrl-C to exit)
sudo journalctl -u fastapi  -f
sudo journalctl -u flaskweb -f
sudo journalctl -u mongod   -f
sudo journalctl -u nginx    -f

# Nginx access / error log files
sudo less /var/log/nginx/access.log
sudo less /var/log/nginx/error.log

# Resources
free -h            # RAM + swap usage
ls -lh /swapfile   # Swap file size on disk
sudo swapon --show # Active swap devices
ps aux | grep gunicorn
top
```

### Updating after a code change

After editing source on the server (or redeploying via scp/git), restart the relevant service so it picks up the new code:

```bash
sudo systemctl restart fastapi   # ML / API changes
sudo systemctl restart flaskweb  # web UI / controller changes
sudo systemctl reload  nginx     # nginx config changes only
```

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

Classify a URL. The response always includes three top-level fields — `code`, `result`, and `detection_type` — that summarise the verdict and where it came from.

```bash
curl -X POST "http://localhost:8000/api/phishing-url?url=https://example.com&api_key=USER_KEY"
```

**Response schema (top-level fields)**

| Field | Type | Values |
| --- | --- | --- |
| `code` | int | `200`, `201`, `300`, `301`, `400`, `401`, `500` |
| `result` | string | `safe`, `phishing`, `NA` |
| `detection_type` | string | `whitelist database`, `blacklist database`, `google safe browsing`, `ML`, `Unable to detect` |

**Code reference**

| `code` | `result` | `detection_type` | When |
| --- | --- | --- | --- |
| 200 | safe | whitelist database | URL/domain matched the whitelist, or it is an official Thai TLD (`.go.th`, `.ac.th`, `.or.th`, `.mi.th`) |
| 201 | phishing | blacklist database | URL matched the blacklist |
| 300 | safe | google safe browsing | *(reserved — Google Safe Browsing currently only escalates phishing verdicts)* |
| 301 | phishing | google safe browsing | Google Safe Browsing flagged the URL (skipping ML), or it flagged it during a split disagreement |
| 400 | safe | ML | ML model classified as safe (Safe Browsing agreed or was unavailable) |
| 401 | phishing | ML | ML model classified as phishing (Safe Browsing agreed, was unavailable, or disagreed and lost) |
| 500 | NA | Unable to detect | Invalid format, domain does not exist, offline, ML feature-extraction failure, or unhandled error |

In addition to the three fields above, the body also contains contextual data (e.g. `url`, `domain_name`, `prediction`, `message`, `result_type`, `online`, `details`, `phish_id`, `phish_detail_url`) for backwards compatibility with existing consumers.

**Split-decision warning**

When the ML model and Google Safe Browsing disagree, the API still returns a single verdict (phishing wins), but flags the response so the client can show a warning:

| Field | Type | Description |
| --- | --- | --- |
| `warning` | bool | `true` when the verdict came from a disagreement between detection systems |
| `warning_message` | string | Human-readable explanation naming which system flagged it and which disagreed |

Example (ML said phishing, Google Safe Browsing said safe):

```json
{
  "code": 401,
  "result": "phishing",
  "detection_type": "ML",
  "warning": true,
  "warning_message": "WARNING: Detection systems disagree. Our ML model flagged this URL as PHISHING, but Google Safe Browsing reports it as SAFE. Proceed with caution.",
  "...": "..."
}
```

Clients should surface `warning_message` (e.g. as a banner or modal) whenever `warning == true`.

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

For each URL the prediction API runs the following pipeline. The first stage that produces a verdict wins and returns the corresponding `code`.

1. **Format check** — must have a valid TLD or be an IP literal. → `500 / NA` on failure.
2. **Whitelist check** — full URL match passes immediately; domain match passes only if the domain is not a hosting platform listed in `hosting_platforms.json`. → `200 / safe / whitelist database`.
3. **Blacklist check** — return stored record if matched. → `201 / phishing / blacklist database`.
4. **Liveness** — DNS lookup (with IDN→Punycode) then HTTP probe. → `500 / NA / Unable to detect` if domain does not exist or the server is offline.
5. **Thai official TLD shortcut** — `.go.th`, `.ac.th`, `.or.th`, `.mi.th` are auto-trusted once liveness passes. → `200 / safe / whitelist database`.
6. **Google Safe Browsing** — if it flags the URL, auto-blacklist and return. → `301 / phishing / google safe browsing`.
7. **ML model** (`app/mlengine/mlp99.31`) — extract features and predict.
8. **Reconcile** — combine ML and Safe Browsing:
   - Both agree → `400 / safe / ML` or `401 / phishing / ML` (also adds to whitelist or blacklist).
   - Safe Browsing unavailable → use ML alone (`400` or `401`).
   - Disagree (split) → phishing wins; attribute to whichever flagged it (`401 / ML` or `301 / google safe browsing`). The response sets `warning: true` and includes a `warning_message` so the client can alert the user that the verdict is uncertain.

## License

See repository for license information.
