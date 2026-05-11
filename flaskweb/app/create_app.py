from flask import Flask, session, request
from flask_pymongo import PyMongo
from flask_mail import Mail
from app.config import Config

mongo = PyMongo()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Cap request body size at 5 MB. Without this, an attacker can stream a
    # multi-GB CSV upload and exhaust memory/disk on the report endpoints.
    # Flask returns 413 (Request Entity Too Large) automatically once exceeded.
    app.config.setdefault('MAX_CONTENT_LENGTH', 5 * 1024 * 1024)

    mongo.init_app(app)
    mail.init_app(app)

    # TTL index for the password-reset rate-limit collection. Idempotent —
    # safe to run on every startup. expireAfterSeconds=86400 = 24h, matching
    # the rate-limit window so old attempts auto-evict.
    with app.app_context():
        try:
            mongo.db.password_reset_attempts.create_index(
                "attempted_at", expireAfterSeconds=86400
            )
        except Exception as e:
            # Don't fail startup if Mongo isn't reachable yet — the rate limit
            # gracefully fails open in that case anyway.
            print(f"[startup] Could not create rate-limit TTL index: {e}")

    # ตั้งค่า default language ใน session ถ้ายังไม่มี หรือเปลี่ยนภาษาตาม query param
    @app.before_request
    def set_default_language():
        lang = request.args.get('lang')
        if lang in ['th', 'en']:
            session['lang'] = lang
        elif "lang" not in session:
            session["lang"] = "en"

    from app.controllers.auth import auth_blueprint
    from app.controllers.get_api import api_blueprint
    from app.controllers.phish_controller import controller_blueprint
    from app.controllers.view import view_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(api_blueprint, url_prefix="/getapi")
    app.register_blueprint(controller_blueprint, url_prefix="/controller")
    app.register_blueprint(view_blueprint, url_prefix="")

    return app
