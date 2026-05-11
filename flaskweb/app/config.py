import configparser


class Config:

    config = configparser.ConfigParser()
    config.read("config_app.ini")

    SECRET_KEY = config["APP"]["SECRET_KEY"]
    API_KEY = config["APP"]["API_KEY"]
    ADMIN_KEY = config["APP"]["ADMIN_KEY"]

    MONGO_URI = config["DATABASE"]["MONGO_URI"]

    MAIL_SERVER = config["MAIL"]["MAIL_SERVER"]
    MAIL_PORT = int(config["MAIL"]["MAIL_PORT"])
    MAIL_USE_TLS = config["MAIL"].getboolean("MAIL_USE_TLS")
    MAIL_USE_SSL = config["MAIL"].getboolean("MAIL_USE_SSL")
    MAIL_USERNAME = config["MAIL"]["MAIL_USERNAME"]
    MAIL_PASSWORD = config["MAIL"]["MAIL_PASSWORD"]
    MAIL_DEFAULT_SENDER = config["MAIL"]["MAIL_DEFAULT_SENDER"]
    URL_DEFAULT_SENDER = config["MAIL"]["URL_DEFAULT_SENDER"]

    DOMAIN_NAME = config["API"]["DOMAIN_NAME"]

    # Comma-separated API keys for service / admin accounts that should be
    # hidden from the user-management listings. Was previously hardcoded in
    # user.py — that exposed the keys in source. Rotate by editing config.
    _hidden = config.get("APP", "HIDDEN_API_KEYS", fallback="")
    HIDDEN_API_KEYS = [k.strip() for k in _hidden.split(",") if k.strip()]

    # Cookie hardening — overridable via config so dev (HTTP) and prod (HTTPS)
    # can have different defaults. SameSite=Lax blocks cross-site form POSTs,
    # which is the bulk of the CSRF threat for this app.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = config.get("APP", "SESSION_COOKIE_SAMESITE", fallback="Lax")
    SESSION_COOKIE_SECURE = config.getboolean("APP", "SESSION_COOKIE_SECURE", fallback=False)
