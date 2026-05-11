from flask import Blueprint, render_template, abort, session
from app.models.phish_model import PhishModel
from datetime import datetime
import json

view_blueprint = Blueprint("view", __name__)

@view_blueprint.route("/detail/<phish_id>", methods=["GET"])
def detail(phish_id):
    result = PhishModel.find_phish_id(phish_id)

    if not result:
        abort(404, description="Data not found")

    if isinstance(result, dict):
        details = result.get("details", [])

        for item in details:
            for key, value in item.items():
                if isinstance(value, list):
                    for i, sub_value in enumerate(value):
                        if isinstance(sub_value, datetime):
                            value[i] = sub_value.strftime("%Y-%m-%d %H:%M:%S")
                elif isinstance(value, datetime):
                    item[key] = value.strftime("%Y-%m-%d %H:%M:%S")

        details_json = json.dumps(details, indent=4)
        return render_template(
            "view/detail.html", details=result, details_json=details_json, lang=session["lang"]
        )
    else:
        abort(500, description="Unexpected data format")

@view_blueprint.route("/info", methods=["GET"])
def info():
    return render_template("view/info.html", lang=session["lang"])