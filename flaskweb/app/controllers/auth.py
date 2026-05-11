from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    g,
)
from app.models.user import User
from app.models.phish_model import PhishModel
from app.create_app import mongo, mail
from app.config import Config
from flask_mail import Message
import secrets
from itsdangerous import URLSafeTimedSerializer
from collections import defaultdict
from datetime import datetime, timedelta

auth_blueprint = Blueprint("auth", __name__)

TRANSLATIONS = {
    "add_member_success_message": {
        "th": "เปลี่ยนสถานะเป็นเมมเบอร์สำเร็จ",
        "en": "Status changed to member successfully",
    },
    "add_member_success_text": {
        "th": "ผู้ใช้ได้รับสถานะเมมเบอร์แล้ว",
        "en": "User has been granted member status.",
    },
    "add_member_error_message": {
        "th": "ไม่สามารถเปลี่ยนสถานะเป็นเมมเบอร์ได้",
        "en": "Could not change status to member",
    },
    "add_member_error_text": {
        "th": "ไม่สามารถเปลี่ยนสถานะเป็นเมมเบอร์ได้ กรุณาลองใหม่",
        "en": "Could not change status to member. Please try again.",
    },
    "unexpected_error_message": {
        "th": "เกิดข้อผิดพลาดที่ไม่คาดคิด",
        "en": "An unexpected error occurred",
    },
    "error_title": {
        "th": "เกิดข้อผิดพลาด",
        "en": "Error",
    },
    "success_title": {
        "th": "สำเร็จ",
        "en": "Success",
    },
    "failure_title": {
        "th": "ล้มเหลว",
        "en": "Failed",
    },
    "delete_user_success_title": {
        "th": "ลบสำเร็จ",
        "en": "Deleted Successfully",
    },
    "delete_user_success_text": {
        "th": "ผู้ใช้ถูกลบออกเรียบร้อยแล้ว",
        "en": "User has been deleted successfully.",
    },
    "delete_user_not_found_text": {
        "th": "ไม่พบผู้ใช้ที่ต้องการลบ",
        "en": "User to be deleted not found.",
    },
    "delete_user_unexpected_error_text": {
        "th": "เกิดข้อผิดพลาดที่ไม่คาดคิด: {error_message}",
        "en": "An unexpected error occurred: {error_message}",
    },
    "register_form_empty": {
        "th": "กรุณากรอกข้อมูลให้ครบทุกช่อง!",
        "en": "Please fill in all fields!",
    },
    "passwords_mismatch": {"th": "รหัสผ่านไม่ตรงกัน!", "en": "Passwords do not match!"},
    "email_exists": {"th": "อีเมลมีอยู่แล้ว!", "en": "Email already exists!"},
    "name_exists": {
        "th": "ข้อมูลนี้ได้รับการลงทะเบียนเรียบร้อยแล้ว!",
        "en": "This information has already been registered!",
    },
    "register_success": {
        "th": "ลงทะเบียนสำเร็จ! หากไม่พบอีเมลในกล่องจดหมาย กรุณาตรวจสอบโฟลเดอร์จดหมายขยะ",
        "en": "Registration successful! If you do not see the email in your inbox, please check your junk mail folder.",
    },
    "login_form_empty": {
        "th": "กรุณากรอกข้อมูลให้ครบทุกช่อง!",
        "en": "Please fill in all fields!",
    },
    "user_not_found": {"th": "ไม่พบผู้ใช้!", "en": "User not found!"},
    "incorrect_credentials": {
        "th": "อีเมลหรือรหัสผ่านไม่ถูกต้อง!",
        "en": "Incorrect email or password!",
    },
    "email_not_confirmed": {
        "th": "กรุณายืนยันอีเมลของคุณก่อนที่จะเข้าสู่ระบบ!",
        "en": "Please confirm your email before logging in!",
    },
    "login_success": {"th": "เข้าสู่ระบบสำเร็จ!", "en": "Login successful!"},
    "password_length_alert": {
        "th": "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร",
        "en": "Password must be at least 8 characters",
    },
    "same_password_alert": {
        "th": "รหัสผ่านใหม่ต้องไม่เหมือนรหัสผ่านเดิม",
        "en": "New password must not be the same as the old password",
    },
    "password_reset_success_alert": {
        "th": "รีเซ็ตรหัสผ่านสำเร็จ",
        "en": "Password reset successful",
    },
    "password_reset_success": {
        "th": "รีเซ็ตรหัสผ่านสำเร็จ",
        "en": "Password reset successful",
    },
    "check_email_reset_password_alert": {
        "th": "หากคุณไม่เห็นอีเมลในกล่องจดหมาย กรุณาตรวจสอบโฟลเดอร์จดหมายขยะ",
        "en": "If you do not see the email in your inbox, please check your junk mail folder."
    },
    "check_email_reset_password": {
        "th": "หากคุณไม่เห็นอีเมลในกล่องจดหมาย กรุณาตรวจสอบโฟลเดอร์จดหมายขยะ",
        "en": "If you do not see the email in your inbox, please check your junk mail folder."
    },
    "email_not_found_alert": {
        "th": "ไม่พบผู้ใช้อีเมลนี้",
        "en": "Email not found"
    },
    "email_not_found": {
        "th": "ไม่พบผู้ใช้อีเมลนี้",
        "en": "Email not found"
    },
    "passwords_do_not_match_alert": {
        "th": "รหัสผ่านไม่ตรงกัน",
        "en": "Passwords do not match"
    },
    "passwords_do_not_match": {
        "th": "รหัสผ่านไม่ตรงกัน",
        "en": "Passwords do not match"
    },
    "password_length_alert": {
        "th": "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร",
        "en": "Password must be at least 8 ตัวอักษร"
    },
    "password_length": {
        "th": "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร",
        "en": "Password must be at least 8 characters"
    },
    "same_password_alert": {
        "th": "รหัสผ่านใหม่ต้องไม่เหมือนรหัสผ่านเดิม",
        "en": "New password must not be the same as the old password"
    },
    "same_password": {
        "th": "รหัสผ่านใหม่ต้องไม่เหมือนรหัสผ่านเดิม",
        "en": "New password must not be the same as the old password"
    },
    "password_reset_success_alert": {
        "th": "รีเซ็ตรหัสผ่านสำเร็จ",
        "en": "Password reset successful"
    },
    "password_reset_success": {
        "th": "รีเซ็ตรหัสผ่านสำเร็จ",
        "en": "Password reset successful"
    },
    "too_many_requests_alert": {
        "th": "คุณได้ส่งคำขอรหัสผ่านมากเกินไป กรุณาลองอีกครั้งในวันพรุ่งนี้",
        "en": "You have exceeded the password reset request limit. Please try again tomorrow."
    },
    "warning_title": {
        "th": "คำเตือน",
        "en": "Warning"
    },
    "too_many_requests": {
        "th": "คุณได้ส่งคำขอรีเซ็ตรหัสผ่านมากเกินไป กรุณาลองอีกครั้งในวันพรุ่งนี้",
        "en": "You have exceeded the password reset request limit. Please try again tomorrow."
    },
    "logout_message": {"th": "ออกจากระบบสำเร็จ", "en": "You have been logged out."},
    'confirmation_failed_js': { 'th': 'การยืนยันล้มเหลว โปรดลองอีกครั้ง', 'en': 'Confirmation failed, please try again.'},
    'invalid_token_structure_js': { 'th': 'โค้ดไม่ถูกต้อง', 'en': 'Invalid token.'},
    'invalid_or_expired_token_js': { 'th': 'โค้ดไม่ถูกต้อง', 'en': 'Invalid token.'},
}

def translate(key):
    return TRANSLATIONS.get(key, {}).get(g.lang, key)

@auth_blueprint.before_request
def before_request():
    g.lang = session.get("lang", "en")

@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]
        email = request.form["email"]
        password = request.form["password"]
        organization = request.form["organization"]
        repeatpassword = request.form["repeat"]

        if not all(
            [firstname, lastname, email, organization, password, repeatpassword]
        ):
            return jsonify(
                {
                    "alert": translate("register_form_empty"),
                    "alert_type": "error",
                }
            )

        if password != repeatpassword:
            return jsonify(
                {"alert": translate("passwords_mismatch"), "alert_type": "error"}
            )

        if User.exists(email):
            return jsonify({"alert": translate("email_exists"), "alert_type": "error"})

        if len(password) < 8:
            return jsonify({
                "alert": translate("password_length_alert"),
                "alert_type": "error",
                "sweetalert": {
                    "icon": "error",
                    "title": TRANSLATIONS["error_title"][g.lang],
                    "text": TRANSLATIONS["password_length"][g.lang]
                }
            })

        user_id = User.create(firstname, lastname, email, organization, password)

        token = secrets.token_urlsafe(16)
        User.create_token(user_id,token)

        send_confirmation_email(email, token)

        return jsonify(
            {
                "alert": translate("register_success"),
                "alert_type": "success",
            }
        )

    return render_template("auth/view/register.html", lang=session["lang"])


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        if not email or not password:
            return jsonify(
                {"alert": translate("login_form_empty"), "alert_type": "error"}
            )

        user = User.get_user_by_email(email)

        if not user:
            return jsonify({"alert": translate("user_not_found"), "alert_type": "error"})

        if not User.verify_password(email, password):
            return jsonify(
                {
                    "alert": translate("incorrect_credentials"),
                    "alert_type": "error",
                }
            )

        if not user.get("confirmed", False):
            redirect_url = url_for("auth.verify_email", lang=session["lang"])
            return jsonify(
                {
                    "alert": translate("email_not_confirmed"),
                    "alert_type": "warning",
                    "redirect_url": redirect_url,
                }
            )

        session["user_firstname"] = user["firstname"]
        session["user_lastname"] = user["lastname"]
        session["user_id"] = str(user["_id"])
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]

        if user["role"] == "member":
            redirect_url = url_for("auth.memberdashboard", lang=session["lang"])
        elif user["role"] == "admin":
            redirect_url = url_for("auth.admindashboard", lang=session["lang"])
        else:
            redirect_url = url_for("auth.userinfo", lang=session["lang"])

        return jsonify(
            {
                "alert": translate("login_success"),
                "alert_type": "success",
                "redirect_url": redirect_url,
            }
        )

    return render_template("auth/view/login.html", lang=session["lang"])

@auth_blueprint.route("/verify_email")
def verify_email():
    return render_template("auth/view/confirm.html", lang=session["lang"])


@auth_blueprint.route("/confirm_email", methods=["GET", "POST"])
def confirm_email():
    if request.method == "POST":
        token = request.form["token"]

        token = token.strip()

        if not token:
                return jsonify({"alert": translate("token_missing_error"), "alert_type": "error"})

        token_entry = User.token_entry(token)

        if token_entry:
            if "user_id" in token_entry:
                user_id_from_token = token_entry["user_id"]

                if User.confirm(user_id_from_token):
                    return jsonify({"alert": translate("email_verified_message"), "alert_type": "success"})
                else:
                    return jsonify({"alert": translate("confirmation_failed"), "alert_type": "error"})
            else:
                return jsonify({"alert": translate("invalid_token_structure"), "alert_type": "error"})
        else:
                return jsonify({"alert": translate("invalid_or_expired_token"), "alert_type": "error"})

    return render_template("auth/view/confirm.html", lang=session["lang"])

email_request_counts = defaultdict(int)
email_request_timestamps = defaultdict(list)

@auth_blueprint.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email = request.form["email"]
        user = User.get_user_by_email(email)

        if user:
            now = datetime.now()
            email_request_timestamps[email] = [
                ts for ts in email_request_timestamps[email] if now - ts < timedelta(days=1)
            ]

            if len(email_request_timestamps[email]) >= 3:
                return jsonify({
                    "alert": TRANSLATIONS["too_many_requests_alert"][g.lang],
                    "alert_type": "warning",
                    "sweetalert": {
                        "icon": "warning",
                        "title": TRANSLATIONS["warning_title"][g.lang],
                        "text": TRANSLATIONS["too_many_requests"][g.lang]
                    }
                })

            serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
            token = serializer.dumps(email, salt='reset-password-salt')

            send_reset_email(email, token)

            email_request_timestamps[email].append(now)

            return jsonify({
                "alert": TRANSLATIONS["check_email_reset_password_alert"][g.lang],
                "alert_type": "success",
                "sweetalert": {
                    "icon": "success",
                    "title": TRANSLATIONS["success_title"][g.lang],
                    "text": TRANSLATIONS["check_email_reset_password"][g.lang]
                }
            })

        else:
            return jsonify({
                "alert": TRANSLATIONS["email_not_found_alert"][g.lang],
                "alert_type": "error",
                "sweetalert": {
                    "icon": "error",
                    "title": TRANSLATIONS["error_title"][g.lang],
                    "text": TRANSLATIONS["email_not_found"][g.lang]
                }
            })

    return render_template("auth/view/forgot-password.html", lang=session["lang"])

@auth_blueprint.route("/recover/<token>", methods=["GET", "POST"])
def recover(token):
    try:
        serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
        email = serializer.loads(token, salt='reset-password-salt', max_age=3600)

    except Exception as e:
        flash('ลิงก์รีเซ็ตรหัสผ่านไม่ถูกต้องหรือไม่หมดอายุ', 'error')
        return redirect(url_for('auth.forgot'))

    if request.method == "POST":
        password = request.form["password"]
        repeat = request.form["repeat"]

        if password != repeat:
            return jsonify({
                "alert": TRANSLATIONS["passwords_do_not_match_alert"][g.lang],
                "alert_type": "error",
                "sweetalert": {
                    "icon": "error",
                    "title": TRANSLATIONS["error_title"][g.lang],
                    "text": TRANSLATIONS["passwords_do_not_match"][g.lang]
                }
            })

        if len(password) < 8:
            return jsonify({
                "alert": TRANSLATIONS["password_length_alert"][g.lang],
                "alert_type": "error",
                "sweetalert": {
                    "icon": "error",
                    "title": TRANSLATIONS["error_title"][g.lang],
                    "text": TRANSLATIONS["password_length"][g.lang]
                }
            })

        user = User.get_user_by_email(email)
        if user and User.verify_password(email, password):
            return jsonify({
                "alert": TRANSLATIONS["same_password_alert"][g.lang],
                "alert_type": "error",
                "sweetalert": {
                    "icon": "error",
                    "title": TRANSLATIONS["error_title"][g.lang],
                    "text": TRANSLATIONS["same_password"][g.lang]
                }
            })

        User.reset_password(email, password)

        return jsonify({
            "alert": TRANSLATIONS["password_reset_success_alert"][g.lang],
            "alert_type": "success",
            "sweetalert": {
                "icon": "success",
                "title": TRANSLATIONS["success_title"][g.lang],
                "text": TRANSLATIONS["password_reset_success"][g.lang]
            },
            "redirect_url": url_for('auth.login')
        })

    return render_template('auth/view/recover.html', token=token, lang=session["lang"])

@auth_blueprint.route("/userrequest")
def userrequest():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))

    user_role = session.get("user_role")
    if user_role != "user":
        return redirect(
            url_for("auth.dashboard", lang=session["lang"])
        )

    user_id = session["user_id"]
    api_key = User.get_api(user_id) or ""

    return render_template(
        "auth/user/request.html", api_key=api_key, lang=session["lang"]
    )

@auth_blueprint.route("/userinfo")
def userinfo():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if session.get("user_role") != "user":
        return redirect(url_for("auth.userinfo", lang=session["lang"]))
    return render_template("auth/user/information.html", lang=session["lang"])

@auth_blueprint.route("/memberdashboard")
def memberdashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "member":
        return redirect(url_for("auth.memberdashboard", lang=session["lang"]))
    user_id = session["user_id"]
    submit = PhishModel.find_submit(user_id)
    verify = PhishModel.find_verify(user_id)
    total = PhishModel.find_total()
    country_stats = PhishModel.get_country_stats(10)
    monthly_stats = PhishModel.get_monthly_stats()
    return render_template(
        "auth/member/dashboard.html",
        lang=session["lang"],
        total=total,
        submit=submit,
        verify=verify,
        country_stats=country_stats,
        monthly_stats=monthly_stats,
    )

@auth_blueprint.route("/memberinfo")
def memberinfo():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "member":
        return redirect(url_for("auth.memberinfo", lang=session["lang"]))
    return render_template("auth/member/information.html", lang=session["lang"])

@auth_blueprint.route("/memberrequest")
def memberrequest():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))

    user_role = session.get("user_role")
    if user_role != "member":
        return redirect(
            url_for("auth.dashboard", lang=session["lang"])
        )

    user_id = session["user_id"]
    api_key = User.get_api(user_id) or ""

    return render_template(
        "auth/member/request.html", api_key=api_key, lang=session["lang"]
    )

@auth_blueprint.route("/memberreport")
def memberreport():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "member":
        return redirect(url_for("auth.memberreport", lang=session["lang"]))
    return render_template("auth/member/report.html", lang=session["lang"])

@auth_blueprint.route("/membertable")
def membertable():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "member":
        return redirect(url_for("auth.membertable", lang=session["lang"]))
    # Reports are now loaded via AJAX for better performance
    return render_template(
        "auth/member/table.html", lang=session["lang"]
    )

@auth_blueprint.route("/admindashboard")
def admindashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
#        return redirect(url_for("auth.adminberdashboard", lang=session["lang"]))

    user_id = session["user_id"]
    submit = PhishModel.find_submit(user_id)
    verify = PhishModel.find_verify(user_id)
    total = PhishModel.find_total()
    country_stats = PhishModel.get_country_stats(10)
    monthly_stats = PhishModel.get_monthly_stats()
    return render_template(
        "auth/admin/dashboard.html",
        lang=session["lang"],
        total=total,
        submit=submit,
        verify=verify,
        country_stats=country_stats,
        monthly_stats=monthly_stats,
    )

@auth_blueprint.route("/admininfo")
def admininfo():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admininfo", lang=session["lang"]))
    return render_template("auth/admin/information.html", lang=session["lang"])

@auth_blueprint.route("/adminrequest")
def adminrequest():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))

    user_role = session.get("user_role")
    if user_role != "admin":
        return redirect(url_for("auth.adminrequest", lang=session["lang"]))

    user_id = session["user_id"]
    api_key = User.get_api(user_id) or ""

    return render_template(
        "auth/admin/request.html", api_key=api_key, lang=session["lang"]
    )

@auth_blueprint.route("/adminwhitereport")
def adminwhitereport():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    return render_template("auth/admin/whitereport.html", lang=session["lang"])

@auth_blueprint.route("/adminwhitetable")
def adminwhitetable():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    # Reports are now loaded via AJAX for better performance
    return render_template(
        "auth/admin/whitetable.html", lang=session["lang"]
    )

@auth_blueprint.route("/adminwhitecheck")
def adminwhitecheck():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    # Reports are now loaded via AJAX for better performance
    return render_template(
        "auth/admin/whitecheckreport.html", lang=session["lang"]
    )
    
@auth_blueprint.route("/adminreport")
def adminreport():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    return render_template("auth/admin/report.html", lang=session["lang"])

@auth_blueprint.route("/admintable")
def admintable():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    # Reports are now loaded via AJAX for better performance
    return render_template(
        "auth/admin/table.html", lang=session["lang"]
    )

@auth_blueprint.route("/admincheck")
def admincheck():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    # Reports are now loaded via AJAX for better performance
    return render_template(
        "auth/admin/checkreport.html", lang=session["lang"]
    )

@auth_blueprint.route("/adminmanage")
def adminmanage():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    # Users are now loaded via AJAX for better performance
    return render_template("auth/admin/manage.html", lang=session["lang"])


@auth_blueprint.route("/get_users_data", methods=["POST"])
def get_users_data():
    """Get users data for admin DataTables (server-side processing)"""
    try:
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        draw = request.form.get("draw", type=int, default=1)
        start = request.form.get("start", type=int, default=0)
        length = request.form.get("length", type=int, default=20)
        search_value = request.form.get("search[value]", type=str, default="")

        query = {}
        if search_value:
            query = {
                "$or": [
                    {"firstname": {"$regex": search_value, "$options": "i"}},
                    {"lastname": {"$regex": search_value, "$options": "i"}},
                    {"email": {"$regex": search_value, "$options": "i"}},
                    {"organization": {"$regex": search_value, "$options": "i"}}
                ]
            }

        total_records = User.count_users()
        filtered_records = User.count_users(query) if search_value else total_records
        data = User.find_users_for_datatable(query, start, length)

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    except Exception as e:
        print(f"Error in get_users_data: {e}")
        return jsonify({"error": str(e)}), 500

@auth_blueprint.route("/adminlog")
def adminlog():
    if "user_id" not in session:
        return redirect(url_for("auth.login", lang=session["lang"]))
    if session.get("user_role") != "admin":
        return redirect(url_for("auth.admindashboard", lang=session["lang"]))
    return render_template("auth/admin/logdata.html", lang=session["lang"])

@auth_blueprint.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_firstname", None)
    session.pop("user_lastname", None)
    session.pop("user_email", None)
    session.pop("user_role", None)
    flash(translate("logout_message"), "success")
    return redirect("/")

def send_confirmation_email(to_email, token):
    msg = Message(
        "ThaiPhishTank account email verification code", sender=f"{Config.MAIL_USERNAME}", recipients=[to_email]
    )

    msg.html = f"""
    <p>Please copy the verification code below and enter it on your email confirmation page.</p>
    <p><strong>Your code is: {token}</strong></p>
    <p>If you did not request this confirmation, please ignore this message.</p>
    """
    mail.send(msg)

def send_reset_email(to_email, token):
    msg = Message(
        "Verify Email and Recover Password for ThaiPhishTank Account", sender=f"{Config.MAIL_USERNAME}", recipients=[to_email]
    )

    link = f"{Config.URL_DEFAULT_SENDER}/auth/recover/{token}"

    msg.html = f"""
    <p>Please click the button below to reset your password.</p>
    <a href="{link}" style="
        display: inline-block;
        padding: 10px 20px;
        font-size: 16px;
        color: white;
        background-color: #007bff;
        text-decoration: none;
        border-radius: 5px;
    ">Reset Password</a>
    <p>This link will expire in 1 hour.<p>
    <p>If you did not request this confirmation, please ignore this message.</p>
    """
    mail.send(msg)

@auth_blueprint.route("/add_member/<user_id>", methods=["POST"])
def add_member(user_id):
    try:
        result = User.update_status_to_member(user_id)

        if result:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": translate("add_member_success_message"),
                        "sweetalert": {
                            "icon": "success",
                            "title": translate("success_title"),
                            "text": translate("add_member_success_text"),
                        },
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "error": translate("add_member_error_message"),
                        "sweetalert": {
                            "icon": "error",
                            "title": translate("failure_title"),
                            "text": translate("add_member_error_text"),
                        },
                    }
                ),
                500,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": translate("unexpected_error_message"),
                    "sweetalert": {
                        "icon": "error",
                        "title": translate("error_title"),
                        "text": translate("delete_user_unexpected_error_text", error_message=str(e)),
                    },
                }
            ),
            500,
        )

@auth_blueprint.route("/auth/delete_user/<user_id>", methods=["POST"])
def delete_user(user_id):
    try:
        result = User.delete_user_by_id(user_id)
        if result:
            return (
                jsonify(
                    {
                        "status": "success",
                        "sweetalert": {
                            "icon": "success",
                            "title": translate("delete_user_success_title"),
                            "text": translate("delete_user_success_text"),
                        },
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "status": "error",
                        "sweetalert": {
                            "icon": "error",
                            "title": translate("error_title"),
                            "text": translate("delete_user_not_found_text"),
                        },
                    }
                ),
                404,
            )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "error",
                    "sweetalert": {
                        "icon": "error",
                        "title": translate("error_title"),
                        "text": translate("delete_user_unexpected_error_text", error_message=str(e)),
                    },
                }
            ),
            500,
        )