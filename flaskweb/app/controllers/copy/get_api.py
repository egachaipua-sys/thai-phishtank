import secrets
from flask import Blueprint, jsonify, session, g
from app.create_app import mongo
from app.models.user import User
from bson.objectid import ObjectId

api_blueprint = Blueprint("getapi", __name__)

TRANSLATIONS = {
    "user_not_logged_in": {"th": "ผู้ใช้ไม่ได้เข้าสู่ระบบ", "en": "User not logged in"},
    "user_not_found": {"th": "ไม่พบข้อมูลผู้ใช้", "en": "User not found"},
    "api_key_save_error": {
        "th": "เกิดข้อผิดพลาดในการบันทึก API Key",
        "en": "Error saving API Key",
    },
    "api_key_created": {"th": " API Key ถูกสร้างขึ้นแล้ว!", "en": "API Key created!"},
    "api_key_retrieved": {"th": "ดึง API Key สำเร็จแล้ว!", "en": "API Key retrieved!"},
    "api_key_not_found": {"th": "ไม่พบ API Key", "en": "API Key not found"},
}


def translate(key):
    return TRANSLATIONS.get(key, {}).get(g.lang, key)

@api_blueprint.before_request
def before_request():
    g.lang = session.get("lang", "en")

@api_blueprint.route("/request_api_key", methods=["POST"])
def request_api_key():
    user_id = session.get("user_id")
    if not user_id:
        return (
            jsonify(
                {
                    "alert": translate("user_not_logged_in"),
                    "alert_type": "error",
                }
            ),
            403,
        )
    user_id = ObjectId(user_id)
    api_key = secrets.token_hex(16)
    result = User.save_api_key(user_id, api_key)
    if result is None:
        return jsonify(
            {
                "alert": translate("api_key_save_error"),
                "alert_type": "error",
            }
        )
    return (
        jsonify(
            {
                "alert": translate("api_key_created"),
                "alert_type": "success",
                "api_key": api_key,
            }
        ),
        200,
    )

@api_blueprint.route("/get_api_key", methods=["GET"])
def get_api_key():
    user_id = session.get("user_id")
    user_id = ObjectId(user_id)
    api_key = User.get_api(user_id)
    if api_key:
        return jsonify(
            {
                "api_key": api_key,
                "alert": translate("api_key_retrieved"),
                "alert_type": "success",
            }
        )
    else:
        return (
            jsonify(
                {
                    "alert": translate("api_key_not_found"),
                    "alert_type": "error",
                }
            ),
            404,
        )