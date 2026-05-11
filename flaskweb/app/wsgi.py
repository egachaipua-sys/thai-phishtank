import sys
import os
from flask import redirect, url_for, request, session
from app.create_app import create_app
from app.models.phish_model import PhishModel

app = create_app()

with app.app_context():
    PhishModel.create_indexes()

@app.before_request
def set_language():
    # ข้ามไฟล์ Static
    if request.endpoint == 'static':
        return

    # ข้าม POST requests
    if request.method == "POST":
        return

    # ตรวจสอบ lang จาก query param
    lang = request.args.get("lang")
    if not lang:
        # ถ้าไม่มี lang ใน URL ให้ดึงจาก session หรือ default เป็น en
        lang = session.get("lang", "en")
        # แล้ว redirect เพื่อเติม lang ใน URL
        if request.endpoint:
            # ใช้ view.index แทน index ถ้าหา endpoint ไม่เจอ
            endpoint = request.endpoint
            try:
                return redirect(url_for(endpoint, lang=lang, **(request.view_args or {})))
            except:
                return redirect(url_for('view.index', lang=lang))
        else:
            return redirect(url_for('view.index', lang=lang))

    session["lang"] = lang

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)