from flask import Flask, session, request
from flask_pymongo import PyMongo
from flask_mail import Mail
from app.config import Config

mongo = PyMongo()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    mongo.init_app(app)
    mail.init_app(app)

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
