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
