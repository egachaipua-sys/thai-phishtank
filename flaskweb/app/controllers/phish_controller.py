from flask import Blueprint, json, jsonify, request, session, render_template, send_file
from app.models.phish_model import PhishModel
from app.create_app import mongo
from app.config import Config
from app.decorators import admin_required, login_required
import requests
import re
import io
import csv
from datetime import datetime
import pytz

controller_blueprint = Blueprint("controller", __name__)

def translate_message(message_key):
    language = session.get('lang', 'en')

    translations = {
        'en': {
            'url_required': 'URL is required',
            'report_saved': 'Phishing report saved successfully',
            'error_occurred': 'An error occurred',
            'user_not_logged_in': 'User is not logged in',
            'fields_missing': 'Please fill in the missing fields: {fields}',
            'unable_to_save_report': 'Unable to save the report',
            'url_is_phishing': 'This URL {url} has been identified as a phishing site.',
            'url_is_offline': 'This URL {url} has been identified as not accessible.',
            'url_is_safe': 'This URL {url} has been safe.',
            'successful_deletion': 'The report was deleted successfully.',
            'deletion_failed': 'Unable to delete the report. Please try again.',
            'invalid_api_response': 'Invalid response from verification API.',
            'safe_verified_message': 'URL {url} is verified as safe by Our System and Google Safe Browsing',
            'phishing_verified_message': 'URL {url} is identified as a phishing website',
            'domain_not_exist_message': 'This domain does not exist in the system. Please check the URL and try again.',

            # ---- ข้อความแปลใหม่สำหรับ CSV และการตรวจสอบ URL ----
            'reporter_missing': 'Reporter information is missing.',
            'invalid_single_url': 'The entered URL format is invalid.',
            'invalid_file_type_csv': 'Invalid file type. Please upload a CSV file.',
            'error_processing_csv_file': 'Error occurred while processing the CSV file.',
            'no_valid_url_or_csv_data_provided': 'No valid URL or CSV data provided.',
            'all_reports_processed_successfully': 'All reports processed successfully.',
            'some_urls_had_issues': 'Some URLs had issues during processing.',
            'unable_to_save_single_report': 'Unable to save this URL report.',
            'only_invalid_urls_found': 'Only invalid URLs were found in the CSV file. No records saved.',
            'url_report_success': "URL '{url}' saved successfully",
            'url_report_failed': "URL '{url}' failed to save: {error}",
            'url_invalid_csv': "Row {row}: URL '{url}' is invalid",
            'success_message_single': "Report submitted successfully",
            'success_message_multiple': "Successfully submitted {count} reports",
            'partial_success_title': "Partial Success!",
            'partial_success_message': "Some URLs were invalid or failed to save: <br>{details}",
            'url_or_csv_note': 'Enter a single URL OR upload a CSV file with URLs (one URL per row in the first column).',
            'csv_file_note': 'Upload a CSV file containing URLs. Each URL should be on a new line in the first column. (e.g. https://malicious.com)',
            'report_suspicious_url': 'Report Suspicious URL',
            'url_label': 'URL',
            'url_placeholder': 'Enter the URL to report',
            'reporter_label': 'Your Name',
            'submit_report': 'Submit Report',
            'csv_file_label': 'CSV File (Optional)',
            'unauthorized': 'Unauthorized access.',
            'no_report_selected': 'No reports selected.',
            'url_already_exists': 'This URL has already been reported.',
            'split_phishing_safe': 'Our system has flagged this website as phishing, but Google Safe Browsing has not.',
            'split_safe_phishing': 'Google Safe Browsing has flagged this website as phishing, but our system has not.',
            'split_unknown_google_phishing': 'Our system cannot determine whether this website is phishing, but Google Safe Browsing has flagged it as phishing.',
            'split_google_unknown_our_phishing': 'Google Safe Browsing cannot determine whether this website is phishing, but our system has flagged it as phishing.',
            'both_unknown': 'The phishing status of this website is unknown, as neither our system nor Google Safe Browsing has available information.',
            'split_unknown': 'Different results detected. Our System: {our_val}, Google Safe Browsing: {safe_val}',
            'error_features': 'Unable to extract URL features.',
            'invalid_url_fmt': 'Invalid URL format. Please enter a valid URL (e.g., example.com).',
            'verified_success': 'URL verified as phishing successfully',
            'verification_timed_out': 'Verification timed out. Please try again.',
            'cannot_connect_service': 'Cannot connect to verification service.',
            'verification_completed': 'Verification completed',
            'url_safe_or_not_found': 'URL is not phishing or not found in blacklist',
            'warning_split_title': 'Caution: Detection systems disagree',
            'warning_split_ml_phishing': 'Our ML model flagged this URL as PHISHING, but Google Safe Browsing reports it as SAFE. Proceed with caution.',
            'warning_split_gsb_phishing': 'Google Safe Browsing flagged this URL as PHISHING, but our ML model reports it as SAFE. Proceed with caution.',
            'warning_split_generic': 'Detection systems returned conflicting verdicts. Proceed with caution.',
        },
        'th': {
            'url_required': 'กรุณากรอก URL',
            'report_saved': 'บันทึกข้อมูลรายงานฟิชชิงสำเร็จ',
            'error_occurred': 'เกิดข้อผิดพลาดที่ไม่คาดคิด',
            'user_not_logged_in': 'ผู้ใช้ยังไม่ได้เข้าสู่ระบบ',
            'fields_missing': 'กรุณากรอกข้อมูลให้ครบ: {fields}',
            'unable_to_save_report': 'ไม่สามารถบันทึกรายงานได้',
            'url_is_phishing': 'URL {url} นี้ฟิชชิง',
            'url_is_offline': 'URL {url} นี้ไม่สามารถเข้าถึงได้',
            'url_is_safe': 'URL {url} นี้ปลอดภัย',
            'successful_deletion': 'ลบรายงานสำเร็จ',
            'deletion_failed': 'ไม่สามารถลบรายงานได้ กรุณาลองใหม่',
            'invalid_api_response': 'การตอบกลับจาก API ตรวจสอบไม่ถูกต้อง',

            # ---- ข้อความแปลใหม่สำหรับ CSV และการตรวจสอบ URL ----
            'reporter_missing': 'ไม่พบข้อมูลผู้รายงาน',
            'invalid_single_url': 'รูปแบบ URL ที่กรอกไม่ถูกต้อง',
            'invalid_file_type_csv': 'ชนิดไฟล์ไม่ถูกต้อง กรุณาอัปโหลดไฟล์ CSV',
            'error_processing_csv_file': 'เกิดข้อผิดพลาดในการประมวลผลไฟล์ CSV',
            'no_valid_url_or_csv_data_provided': 'ไม่พบ URL ที่ถูกต้อง หรือข้อมูล CSV ที่ให้มา',
            'all_reports_processed_successfully': 'ประมวลผลรายงานทั้งหมดสำเร็จ',
            'some_urls_had_issues': 'บาง URL มีปัญหาในการประมวลผล',
            'unable_to_save_single_report': 'ไม่สามารถบันทึกรายงาน URL นี้ได้',
            'only_invalid_urls_found': 'พบเฉพาะ URL ที่ไม่ถูกต้องในไฟล์ CSV เท่านั้น ไม่มีการบันทึก',
            'url_report_success': "URL '{url}' บันทึกสำเร็จ",
            'url_report_failed': "URL '{url}' บันทึกไม่สำเร็จ: {error}",
            'url_invalid_csv': "แถวที่ {row}: URL '{url}' ไม่ถูกต้อง",
            'success_message_single': "ส่งรายงานสำเร็จ",
            'success_message_multiple': "ส่งรายงานสำเร็จ {count} รายการ",
            'partial_success_title': "รายงานบางส่วนมีปัญหา",
            'partial_success_message': "มีบาง URL ที่ไม่ถูกต้องหรือบันทึกไม่สำเร็จ: <br>{details}",
            'url_or_csv_note': 'กรอก URL เพียงหนึ่งรายการ หรืออัปโหลดไฟล์ CSV ที่มี URL (หนึ่ง URL ต่อหนึ่งแถวในคอลัมน์แรก)',
            'csv_file_note': 'อัปโหลดไฟล์ CSV ที่มี URL แต่ละ URL ควรอยู่ในบรรทัดใหม่ในคอลัมน์แรก (เช่น https://malicious.com)',
            'report_suspicious_url': 'รายงาน URL ที่น่าสงสัย',
            'url_label': 'URL',
            'url_placeholder': 'กรอก URL ที่ต้องการรายงาน',
            'reporter_label': 'ชื่อของคุณ',
            'submit_report': 'ส่งรายงาน',
            'csv_file_label': 'ไฟล์ CSV (ไม่บังคับ)',
            'unauthorized': 'การเข้าถึงไม่ได้รับอนุญาต',
            'no_report_selected': 'ไม่ได้เลือกรายงาน',
            'url_already_exists': 'URL นี้ได้ถูกรายงานเข้าระบบแล้ว',
            'safe_verified_message': 'URL {url} ได้รับการตรวจสอบแล้วว่าปลอดภัย โดยระบบของเราและ Google Safe Browsing',
            'phishing_verified_message': 'URL {url} นี้ถูกระบุว่าเป็นเว็บไซต์ฟิชชิง',
            'domain_not_exist_message': 'ไม่พบโดเมนนี้ในระบบ โปรดตรวจสอบ URL และลองใหม่อีกครั้ง',
            'split_phishing_safe': 'ระบบของเราได้ทำเครื่องหมายเว็บไซต์นี้ว่าเป็นฟิชชิง แต่ Google Safe Browsing ยังไม่ได้ระบุว่าเป็นฟิชชิง',
            'split_safe_phishing': 'Google Safe Browsing ได้ทำเครื่องหมายเว็บไซต์นี้ว่าเป็นฟิชชิง แต่ระบบของเรายังไม่ได้ระบุว่าเป็นฟิชชิง',
            'split_unknown_google_phishing': 'ระบบของเรายังไม่สามารถระบุได้ว่าเว็บไซต์นี้เป็นฟิชชิงหรือไม่ แต่ Google Safe Browsing ได้ระบุว่าเป็นฟิชชิง',
            'split_google_unknown_our_phishing': 'Google Safe Browsing ยังไม่สามารถระบุได้ว่าเว็บไซต์นี้เป็นฟิชชิงหรือไม่ แต่ระบบของเราได้ทำเครื่องหมายว่าเป็นฟิชชิง',
            'both_unknown': 'ยังไม่สามารถระบุได้ว่าเว็บไซต์นี้เป็นฟิชชิงหรือไม่ เนื่องจากทั้งระบบของเราและ Google Safe Browsing ยังไม่มีข้อมูล',
            'split_unknown': 'ตรวจพบผลลัพธ์ที่แตกต่างกัน ระบบของเรา: {our_val}, Google Safe Browsing: {safe_val}',
            'error_features': 'ไม่สามารถดึงข้อมูลคุณลักษณะของ URL ได้',
            'invalid_url_fmt': 'รูปแบบ URL ไม่ถูกต้อง โปรดป้อน URL ที่ถูกต้อง (เช่น example.com)',
            'verified_success': 'ตรวจสอบและยืนยัน URL เป็นฟิชชิงสำเร็จ',
            'verification_timed_out': 'การตรวจสอบหมดเวลา กรุณาลองใหม่อีกครั้ง',
            'cannot_connect_service': 'ไม่สามารถเชื่อมต่อกับบริการตรวจสอบได้',
            'verification_completed': 'การตรวจสอบเสร็จสมบูรณ์',
            'url_safe_or_not_found': 'URL นี้ปลอดภัย หรือไม่พบในรายการแบล็คลิสต์',
            'warning_split_title': 'คำเตือน: ระบบตรวจจับให้ผลไม่ตรงกัน',
            'warning_split_ml_phishing': 'โมเดล ML ของเราระบุว่า URL นี้เป็น "ฟิชชิง" แต่ Google Safe Browsing ระบุว่า "ปลอดภัย" โปรดใช้ความระมัดระวัง',
            'warning_split_gsb_phishing': 'Google Safe Browsing ระบุว่า URL นี้เป็น "ฟิชชิง" แต่โมเดล ML ของเราระบุว่า "ปลอดภัย" โปรดใช้ความระมัดระวัง',
            'warning_split_generic': 'ระบบตรวจจับให้ผลลัพธ์ที่ขัดแย้งกัน โปรดใช้ความระมัดระวัง',
        }
    }

    return translations.get(language, {}).get(message_key, message_key)

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' # http:// หรือ https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def is_valid_url(url_string):
    """Checks if a string is a valid URL using a regular expression."""
    return re.match(URL_REGEX, url_string) is not None

@controller_blueprint.route("/get_phishing_data", methods=["POST"])
def get_phishing_data():
    try:
        # รับค่า parameters จาก DataTables
        draw = request.form.get("draw", type=int, default=1)
        start = request.form.get("start", type=int, default=0)
        length = request.form.get("length", type=int, default=10)
        # Bound the search value so a long pathological pattern can't pin CPU.
        search_value = (request.form.get("search[value]", type=str, default="") or "")[:100]

        # จัดการ Search filter
        query = {}
        if search_value:
            # re.escape() — without it, user input is interpreted as a regex
            # and becomes a NoSQL-injection / ReDoS vector.
            escaped = re.escape(search_value)
            query = {
                "$or": [
                    {"phish_id": {"$regex": escaped, "$options": "i"}},
                    {"url": {"$regex": escaped, "$options": "i"}}
                ]
            }

        # นับจำนวนทั้งหมด (สำหรับ recordsTotal และ recordsFiltered)
        total_records = PhishModel.count_all()
        filtered_records = PhishModel.count_filtered(query)

        # ดึงข้อมูลตาม limit และ offset
        data = PhishModel.find_for_datatable(query, start, length)

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    except Exception as e:
        print(f"Error in get_phishing_data: {e}")
        return jsonify({"error": str(e)}), 500


@controller_blueprint.route("/get_check_reports_data", methods=["POST"])
def get_check_reports_data():
    """Get check reports data for admin DataTables (server-side processing)"""
    try:
        # Check admin authorization
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        # Get DataTables parameters
        draw = request.form.get("draw", type=int, default=1)
        start = request.form.get("start", type=int, default=0)
        length = request.form.get("length", type=int, default=20)
        search_value = (request.form.get("search[value]", type=str, default="") or "")[:100]

        # Build search query
        query = {}

        # 1. Filter by Search Box
        if search_value:
            escaped = re.escape(search_value)
            query["$or"] = [
                {"url": {"$regex": escaped, "$options": "i"}},
                {"reporter": {"$regex": escaped, "$options": "i"}}
            ]
            
        # 2. Filter by Verified Status
        verified_status = request.form.get("verified_status")
        if verified_status == "yes":
            # Show only verified
            query["$or"] = [{"verified": "yes"}, {"verifited": "yes"}]
        elif verified_status == "no":
            # Show only not verified (no, null, or other values)
            query["$nor"] = [{"verified": "yes"}, {"verifited": "yes"}]

        # Get counts
        total_records = PhishModel.count_check_reports()
        filtered_records = PhishModel.count_check_reports(query) if search_value else total_records

        # Get paginated data
        data = PhishModel.find_check_reports_for_datatable(query, start, length)

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    except Exception as e:
        print(f"Error in get_check_reports_data: {e}")
        return jsonify({"error": str(e)}), 500


@controller_blueprint.route("/get_user_reports_data", methods=["POST"])
def get_user_reports_data():
    """Get user reports data for DataTables (server-side processing)"""
    try:
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 403

        user_id = session.get("user_id")
        draw = request.form.get("draw", type=int, default=1)
        start = request.form.get("start", type=int, default=0)
        length = request.form.get("length", type=int, default=20)
        search_value = (request.form.get("search[value]", type=str, default="") or "")[:100]

        query = {}
        if search_value:
            # re.escape() — without it user input becomes a Mongo regex,
            # opening NoSQL-injection / ReDoS vectors.
            escaped = re.escape(search_value)
            query = {
                "$or": [
                    {"url": {"$regex": escaped, "$options": "i"}},
                    {"reporter": {"$regex": escaped, "$options": "i"}}
                ]
            }

        total_records = PhishModel.count_user_reports(user_id)
        filtered_records = PhishModel.count_user_reports(user_id, query) if search_value else total_records
        data = PhishModel.find_user_reports_for_datatable(user_id, query, start, length)

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    except Exception as e:
        print(f"Error in get_user_reports_data: {e}")
        return jsonify({"error": str(e)}), 500


@controller_blueprint.route("/get_white_check_reports_data", methods=["POST"])
def get_white_check_reports_data():
    """Get whitelist check reports data for admin DataTables (server-side processing)"""
    try:
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        draw = request.form.get("draw", type=int, default=1)
        start = request.form.get("start", type=int, default=0)
        length = request.form.get("length", type=int, default=20)
        search_value = (request.form.get("search[value]", type=str, default="") or "")[:100]

        query = {}
        if search_value:
            # re.escape() — without it user input becomes a Mongo regex,
            # opening NoSQL-injection / ReDoS vectors.
            escaped = re.escape(search_value)
            query = {
                "$or": [
                    {"url": {"$regex": escaped, "$options": "i"}},
                    {"reporter": {"$regex": escaped, "$options": "i"}}
                ]
            }

        # Filter by Verified Status
        verified_status = request.form.get("verified_status")
        if verified_status == "yes":
            # Show only verified
            verified_condition = {"$or": [{"verified": "yes"}, {"verifited": "yes"}]}
            if query:
                query = {"$and": [query, verified_condition]}
            else:
                query = verified_condition
        elif verified_status == "no":
            # Show only not verified
            not_verified_condition = {"$nor": [{"verified": "yes"}, {"verifited": "yes"}]}
            if query:
                 query = {"$and": [query, not_verified_condition]}
            else:
                 query = not_verified_condition

        total_records = PhishModel.count_white_check_reports()
        filtered_records = PhishModel.count_white_check_reports(query) if search_value else total_records
        data = PhishModel.find_white_check_reports_for_datatable(query, start, length)

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    except Exception as e:
        print(f"Error in get_white_check_reports_data: {e}")
        return jsonify({"error": str(e)}), 500


@controller_blueprint.route("/get_user_white_reports_data", methods=["POST"])
def get_user_white_reports_data():
    """Get user whitelist reports data for DataTables (server-side processing)"""
    try:
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 403

        user_id = session.get("user_id")
        draw = request.form.get("draw", type=int, default=1)
        start = request.form.get("start", type=int, default=0)
        length = request.form.get("length", type=int, default=20)
        search_value = (request.form.get("search[value]", type=str, default="") or "")[:100]

        query = {}
        if search_value:
            # re.escape() — without it user input becomes a Mongo regex,
            # opening NoSQL-injection / ReDoS vectors.
            escaped = re.escape(search_value)
            query = {
                "$or": [
                    {"url": {"$regex": escaped, "$options": "i"}},
                    {"reporter": {"$regex": escaped, "$options": "i"}}
                ]
            }

        total_records = PhishModel.count_user_white_reports(user_id)
        filtered_records = PhishModel.count_user_white_reports(user_id, query) if search_value else total_records
        data = PhishModel.find_user_white_reports_for_datatable(user_id, query, start, length)

        return jsonify({
            "draw": draw,
            "recordsTotal": total_records,
            "recordsFiltered": filtered_records,
            "data": data
        })
    except Exception as e:
        print(f"Error in get_user_white_reports_data: {e}")
        return jsonify({"error": str(e)}), 500


@controller_blueprint.route("/check_url", methods=["POST"])
def check_url():
    try:
        data = request.get_json()
        url_to_check = data.get("url")

        if not url_to_check.startswith("http://") and not url_to_check.startswith("https://"):
            url_to_check = "https://" + url_to_check

        if not url_to_check:
            return jsonify({"error": translate_message("url_required"), "status": "error"}), 400
            
        if not is_valid_url(url_to_check):
             return jsonify({"status": "error", "message": translate_message("invalid_url_fmt"), "prediction": "error"}), 200

        fastapi_url = f"{Config.DOMAIN_NAME}/api/phishing-url"
        params = {"url": url_to_check, "api_key": Config.API_KEY}

        with requests.post(fastapi_url, params=params) as response:
            response.raise_for_status()
            fastapi_result = response.json()

        # New API verdict fields (forwarded to the frontend; older clients can ignore).
        api_code = fastapi_result.get("code")
        api_result = fastapi_result.get("result")
        api_detection_type = fastapi_result.get("detection_type")
        api_warning = bool(fastapi_result.get("warning"))

        if fastapi_result.get("result_type") == "split" or fastapi_result.get("prediction") == "split":

            raw_our = fastapi_result.get("our_system")
            raw_safe = fastapi_result.get("safe_browsing")

            # Normalize to "Unknown" if None or "unknown" (case-insensitive)
            our_system = "Unknown" if not raw_our or str(raw_our).lower() == "unknown" else raw_our
            safe_browsing = "Unknown" if not raw_safe or str(raw_safe).lower() == "unknown" else raw_safe

            # Case 3: Both Unknown (explicit check)
            if our_system == "Unknown" and safe_browsing == "Unknown":
                result = {
                    "status": "info",
                    "prediction": "unknown",
                    "message": translate_message("both_unknown"),
                }
            else:
                # Select appropriate translation for other split cases
                if our_system == "Phishing" and safe_browsing == "Safe":
                    msg = translate_message("split_phishing_safe")
                    warning_message = translate_message("warning_split_ml_phishing")
                elif our_system == "Phishing" and safe_browsing == "Unknown":
                    msg = translate_message("split_google_unknown_our_phishing")
                    warning_message = translate_message("warning_split_ml_phishing")
                elif safe_browsing == "Phishing" and our_system == "Safe":
                    msg = translate_message("split_safe_phishing")
                    warning_message = translate_message("warning_split_gsb_phishing")
                elif safe_browsing == "Phishing" and our_system == "Unknown":
                    msg = translate_message("split_unknown_google_phishing")
                    warning_message = translate_message("warning_split_gsb_phishing")
                else:
                    msg = translate_message("split_unknown").format(our_val=our_system, safe_val=safe_browsing)
                    warning_message = translate_message("warning_split_generic")

                result = {
                    "status": "warning",
                    "prediction": "split",
                    "our_system": our_system,
                    "safe_browsing": safe_browsing,
                    "message": msg,
                    "warning": True,
                    "warning_title": translate_message("warning_split_title"),
                    "warning_message": warning_message,
                }
        elif fastapi_result.get("prediction") == "phishing":
            result = {
                "status": "warning",
                "prediction": fastapi_result["prediction"],
                "message": translate_message("phishing_verified_message").format(url=url_to_check),
            }
        elif fastapi_result.get("prediction") == "offline":
             result = {
                "status": "error",
                "prediction": fastapi_result["prediction"],
                "message": translate_message("url_is_offline").format(url=url_to_check),
            }
        elif fastapi_result.get("prediction") == "error":
            # กรณีไม่สามารถสกัดคุณลักษณะ URL ได้
            result = {
                "status": "error",
                "prediction": "error",
                "message": translate_message("error_features"),
            }
        elif fastapi_result.get("prediction") == "not_exist":
            # กรณี Domain ไม่มีจริง (DNS lookup failed)
            result = {
                "status": "error",
                "prediction": "not_exist",
                "message": translate_message("domain_not_exist_message"),
            }
        elif fastapi_result.get("prediction") == "unknown":
            result = {
                "status": "info",
                "prediction": "unknown",
                "message": translate_message("both_unknown"),
            }
        else:
            result = {
                "status": "success",
                "prediction": fastapi_result.get("prediction", "safe"),
                "message": translate_message("safe_verified_message").format(url=url_to_check),
            }

        # Forward the FastAPI verdict triplet so newer frontends can use it directly.
        result["code"] = api_code
        result["result"] = api_result
        result["detection_type"] = api_detection_type
        # If the API itself flagged a warning and the split branch didn't already set one, propagate it.
        if api_warning and not result.get("warning"):
            result["warning"] = True
            result["warning_title"] = translate_message("warning_split_title")
            result["warning_message"] = fastapi_result.get("warning_message") or translate_message("warning_split_generic")

        return jsonify(result)

    except requests.exceptions.RequestException as e:
        print(f"Error calling FastAPI: {e}")
        return jsonify({"status": "error", "message": translate_message("error_occurred"), "error": str(e)}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": translate_message("error_occurred"), "error": str(e)}), 500



@controller_blueprint.route("/report_legitimate", methods=["GET", "POST"])
def report_legitimate():
    if request.method == "GET":
        lang = session.get('lang', 'en')
        return render_template("auth/admin/whitereport.html", lang=lang)

    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "error": translate_message("user_not_logged_in")}), 401

        reporter = request.form.get("reporter")
        if not reporter:
             return jsonify({"status": "error", "error": translate_message("reporter_missing")}), 400

        urls_to_process = []
        processed_results = [] # เก็บผลลัพธ์การบันทึกแต่ละรายการ
        invalid_urls_from_csv = [] # สำหรับเก็บ URL ที่ไม่ถูกต้องจาก CSV พร้อมบอกแถว

        # 1. จัดการ URL เดียวจากฟอร์ม
        url = request.form.get("url")
        if url:
            # Auto-append protocol if missing
            if not url.startswith(('http://', 'https://')):
                 url = 'http://' + url
            
            if is_valid_url(url):
                 urls_to_process.append(url)
            else:
                 return jsonify({"status": "error", "error": translate_message("invalid_single_url")}), 400

        # 2. จัดการไฟล์ CSV ที่อัปโหลด
        if 'csv_file' in request.files:
            csv_file = request.files['csv_file']
            if csv_file.filename != '':
                if not csv_file.filename.lower().endswith('.csv'):
                    return jsonify({"status": "error", "error": translate_message("invalid_file_type_csv")}), 400

                try:
                    stream = io.TextIOWrapper(csv_file.stream, encoding='utf-8')
                    csv_reader = csv.reader(stream)
                    for row_num, row in enumerate(csv_reader, 1):
                        if row:
                            potential_url = row[0].strip() if row[0].strip() else None
                            if potential_url:
                                # Auto-append protocol if missing
                                if not potential_url.startswith(('http://', 'https://')):
                                     potential_url = 'http://' + potential_url

                                if is_valid_url(potential_url):
                                    urls_to_process.append(potential_url)
                                else:
                                    invalid_urls_from_csv.append(
                                        translate_message("url_invalid_csv").format(row=row_num, url=potential_url)
                                    )
                except Exception as e:
                    print(f"Error processing CSV file: {e}")
                    return jsonify({"status": "error", "error": translate_message("error_processing_csv_file"), "message": str(e)}), 500

        # 3. ตรวจสอบว่ามี URL ที่จะประมวลผลหรือไม่
        if not urls_to_process and not invalid_urls_from_csv:
            return jsonify({"status": "error", "error": translate_message("no_valid_url_or_csv_data_provided")}), 400
        elif not urls_to_process and invalid_urls_from_csv:
            return jsonify({
                "status": "error",
                "error": translate_message("only_invalid_urls_found"),
                "data": {"invalid_urls_from_csv": invalid_urls_from_csv}
            }), 400

        # 4. วนลูปและบันทึก URL ลงในฐานข้อมูล
        for url_item in urls_to_process:
            save_result = PhishModel.save_whitelist_report(user_id, url_item, reporter)
            
            if save_result == "duplicate":
                processed_results.append({
                    "url": url_item, 
                    "status": "failed", 
                    "error": translate_message("url_already_exists")
                })
            elif save_result:
                processed_results.append({"url": url_item, "status": "success"})
            else:
                 processed_results.append({"url": url_item, "status": "failed", "error": translate_message("unable_to_save_single_report")})

        # 5. สร้างการตอบกลับตามผลลัพธ์
        if len(urls_to_process) > 0 and all(res['status'] == 'success' for res in processed_results) and not invalid_urls_from_csv:
             return jsonify({
                "status": "success",
                "message": translate_message("all_reports_processed_successfully"),
                "data": processed_results
            }), 200
        else:
             return jsonify({
                "status": "partial_success",
                "message": translate_message("some_urls_had_issues"),
                "data": {
                    "processed_results": processed_results,
                    "invalid_urls_from_csv": invalid_urls_from_csv
                }
            }), 200

    except Exception as e:
        print(f"Error in report_legitimate: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/report_phishing", methods=["GET", "POST"])
def report_phishing():
    if request.method == "GET":
        # ตรวจสอบและกำหนดค่า lang สำหรับการเรนเดอร์เทมเพลต
        # คุณอาจจะมี lang ใน session หรือตั้งค่าเริ่มต้น
        lang = session.get('lang', 'en') 
        # สมมติว่า translations_data (จาก JS) ถูกส่งผ่าน context ให้กับ template
        # ซึ่งใน Flask ปกติจะรวมอยู่ใน Jinja2 environment อยู่แล้ว
        # ถ้าไม่ ให้ส่ง translations_data ไปด้วย เช่น render_template("user-report.html", lang=lang, translations=your_translation_dict)
        return render_template("report.html", lang=lang) # ใช้ report.html ตามชื่อไฟล์ที่คุณให้มา

    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"status": "error", "error": translate_message("user_not_logged_in")}), 401

        reporter = request.form.get("reporter")
        if not reporter:
            return jsonify({"status": "error", "error": translate_message("reporter_missing")}), 400

        urls_to_process = []
        processed_results = [] # เก็บผลลัพธ์การบันทึกแต่ละรายการ
        invalid_urls_from_csv = [] # สำหรับเก็บ URL ที่ไม่ถูกต้องจาก CSV พร้อมบอกแถว

        # 1. จัดการ URL เดียวจากฟอร์ม
        single_url = request.form.get("url")
        if single_url:
            # Auto-append protocol if missing
            if not single_url.startswith(('http://', 'https://')):
                 single_url = 'http://' + single_url
                 
            if is_valid_url(single_url):
                urls_to_process.append(single_url)
            else:
                # ถ้า URL เดียวไม่ถูกต้อง ให้ส่งคืนข้อผิดพลาดทันที
                return jsonify({"status": "error", "error": translate_message("invalid_single_url")}), 400

        # 2. จัดการไฟล์ CSV ที่อัปโหลด
        if 'csv_file' in request.files:
            csv_file = request.files['csv_file']
            if csv_file.filename != '':
                if not csv_file.filename.lower().endswith('.csv'):
                    return jsonify(
                        {
                            "status": "error",
                            "error": translate_message("invalid_file_type_csv")
                        }
                    ), 400

                try:
                    # อ่านไฟล์ CSV ในโหมดข้อความ
                    stream = io.TextIOWrapper(csv_file.stream, encoding='utf-8')
                    csv_reader = csv.reader(stream)

                    # ตัวเลือก: ข้ามแถวหัวข้อ (header row) หาก CSV ของคุณมี
                    # next(csv_reader, None)

                    for row_num, row in enumerate(csv_reader, 1): # เริ่มนับแถวจาก 1
                        if row: # ตรวจสอบว่าแถวไม่ว่างเปล่า
                            # เราจะถือว่าคอลัมน์แรก (index 0) คือ URL
                            potential_url = row[0].strip() if row[0].strip() else None

                            if potential_url:
                                if is_valid_url(potential_url):
                                    urls_to_process.append(potential_url)
                                else:
                                    invalid_urls_from_csv.append(
                                        translate_message("url_invalid_csv").format(row=row_num, url=potential_url)
                                    )
                            # else: แถวว่างเปล่าหรือคอลัมน์แรกว่าง ก็ไม่ต้องทำอะไร

                except Exception as e:
                    print(f"Error processing CSV file: {e}") # สำหรับ debug
                    return jsonify(
                        {
                            "status": "error",
                            "error": translate_message("error_processing_csv_file"),
                            "message": str(e)
                        }
                    ), 500
        
        # 3. ตรวจสอบว่ามี URL ที่จะประมวลผลหรือไม่
        if not urls_to_process and not invalid_urls_from_csv:
            # ไม่มี URL ใดๆ ทั้งจากฟอร์มหรือ CSV ที่ถูกต้อง
            return jsonify(
                {
                    "status": "error",
                    "error": translate_message("no_valid_url_or_csv_data_provided")
                }
            ), 400
        elif not urls_to_process and invalid_urls_from_csv:
            # มีไฟล์ CSV แต่อยู่ในสภาพที่ไม่ถูกต้องทั้งหมด
            return jsonify({
                "status": "error",
                "error": translate_message("only_invalid_urls_found"),
                "data": {"invalid_urls_from_csv": invalid_urls_from_csv}
            }), 400

        # 4. วนลูปและบันทึก URL ลงในฐานข้อมูล (เฉพาะ URL ที่ถูกต้อง)
        for url_item in urls_to_process:
            save_result = PhishModel.save_report(
                user_id=user_id, url=url_item, reporter=reporter
            )
            
            if save_result == "duplicate":
                # กรณีซ้ำ
                processed_results.append({
                    "url": url_item, 
                    "status": "failed", 
                    "error": translate_message("url_already_exists")
                })
            elif save_result:
                # กรณีสำเร็จ (ได้ objectId)
                processed_results.append({"url": url_item, "status": "success"})
            else:
                # กรณี error อื่นๆ
                processed_results.append({"url": url_item, "status": "failed", "error": translate_message("unable_to_save_single_report")})

        # 5. สร้างการตอบกลับตามผลลัพธ์
        if len(urls_to_process) > 0 and all(res['status'] == 'success' for res in processed_results) and not invalid_urls_from_csv:
            # สำเร็จทั้งหมด
            return jsonify({
                "status": "success",
                "message": translate_message("all_reports_processed_successfully"),
                "data": processed_results
            }), 201
        else:
            # มีบางส่วนสำเร็จหรือมีปัญหา (partial_success)
            return jsonify({
                "status": "partial_success",
                "message": translate_message("some_urls_had_issues"),
                "data": {
                    "processed_results": processed_results,
                    "invalid_urls_from_csv": invalid_urls_from_csv
                }
            }), 200 # ใช้ 200 OK สำหรับ partial success

    except Exception as e:
        print(f"Unhandled error: {e}") # สำหรับ debug
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/verify_report", methods=["POST"])
@admin_required
def verify_report():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request data"}), 400
            
        url_to_check = data.get("url")
        report_id = data.get("report_id")  # Optional: for direct update
        
        if not url_to_check:
            return jsonify({"status": "error", "message": translate_message("url_required")}), 400

        if not url_to_check.startswith("http://") and not url_to_check.startswith("https://"):
            url_to_check = "https://" + url_to_check

        fastapi_url = f"{Config.DOMAIN_NAME}/api/verifited-url"
        params = {"url": url_to_check, "api_key": Config.ADMIN_KEY}

        try:
            response = requests.post(fastapi_url, params=params, timeout=30)
            response.raise_for_status()
            
            fastapi_result = response.json()
            
            # Check if FastAPI returned an error
            if fastapi_result.get("error"):
                return jsonify({
                    "status": "error", 
                    "message": fastapi_result.get("message", translate_message("error_occurred")),
                    "prediction": "error"
                }), 500
            
            prediction = fastapi_result.get("prediction", "")
            
            # ถ้า URL อยู่ใน whitelist หรือไม่พบใน blacklist
            if prediction in ["safe", "not_found"]:
                # อัพเดทสถานะ verified เป็น 'no' ในฐานข้อมูล phish_url
                from bson import ObjectId
                thai_timezone = pytz.timezone("Asia/Bangkok")
                verification_time = datetime.now(tz=thai_timezone).isoformat()
                
                # ค้นหา report จาก URL
                report = mongo.db.phish_url.find_one({"url": url_to_check})
                if report:
                    mongo.db.phish_url.update_one(
                        {"_id": report["_id"]},
                        {
                            "$set": {
                                "verifited": "no",
                                "verification_time": verification_time
                            }
                        }
                    )
                
                return jsonify({
                    "status": "success",
                    "prediction": prediction,
                    "url": url_to_check,
                    "message": fastapi_result.get("message", translate_message("url_safe_or_not_found"))
                })
            
            # ถ้าเป็น phishing - Success case
            if prediction == "phishing" or fastapi_result.get("verifited") == "yes":
                # Update status in database
                from bson import ObjectId
                thai_timezone = pytz.timezone("Asia/Bangkok")
                verification_time = datetime.now(tz=thai_timezone).isoformat()
                
                # ค้นหา report จาก URL
                report = mongo.db.phish_url.find_one({"url": url_to_check})
                if report:
                    mongo.db.phish_url.update_one(
                        {"_id": report["_id"]},
                        {
                            "$set": {
                                "verified": "yes",
                                "verifited": "yes",
                                "verification_time": verification_time
                            }
                        }
                    )

                return jsonify({
                    "status": "success",
                    "prediction": "phishing",
                    "url": fastapi_result.get("url", url_to_check),
                    "message": translate_message("verified_success")
                })
            
            # Default case - return what we got from API
            return jsonify({
                "status": "success",
                "prediction": prediction,
                "url": fastapi_result.get("url", url_to_check),
                "message": fastapi_result.get("message", translate_message("verification_completed"))
            })
                
        except requests.exceptions.Timeout:
            print(f"Timeout calling FastAPI for URL: {url_to_check}")
            return jsonify({"status": "error", "message": translate_message("verification_timed_out"), "prediction": "error"}), 504
            
        except requests.exceptions.ConnectionError:
            print(f"Connection error calling FastAPI for URL: {url_to_check}")
            return jsonify({"status": "error", "message": translate_message("cannot_connect_service"), "prediction": "error"}), 503
            
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from FastAPI")
            return jsonify({"status": "error", "message": translate_message("invalid_api_response"), "prediction": "error"}), 500
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling FastAPI: {e}")
        return jsonify({"status": "error", "message": translate_message("error_occurred"), "error": str(e), "prediction": "error"}), 500

    except Exception as e:
        print(f"Unexpected error in verify_report: {e}")
        return jsonify({"status": "error", "message": translate_message("error_occurred"), "error": str(e), "prediction": "error"}), 500


@controller_blueprint.route("/delete_report/<report_id>", methods=["POST"])
@admin_required
def delete_report(report_id):
    try:
        result = PhishModel.delete_report(report_id)

        if result:
            return jsonify({"status": "success", "message": translate_message("successful_deletion")}), 200
        else:
            return jsonify({"status": "error", "error": translate_message("deletion_failed")}), 500

    except Exception as e:
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/whiteverify_report", methods=["POST"])
def whiteverify_report():
    print("DEBUG: whiteverify_report called")
    try:
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"status": "error", "error": translate_message("unauthorized")}), 403

        data = request.get_json()
        print(f"DEBUG: Received data: {data}")
        
        report_ids = data.get("report_ids", [])

        if not report_ids:
            return jsonify({"status": "error", "error": translate_message("no_report_selected")}), 400

        updated_count = 0
        errors = []
        from bson import ObjectId
        from bson.errors import InvalidId

        for report_id in report_ids:
            try:
                # Validate ObjectId
                if not report_id or not isinstance(report_id, str):
                    errors.append(f"Invalid report_id format: {report_id}")
                    continue
                    
                try:
                    object_id = ObjectId(report_id)
                except InvalidId:
                    errors.append(f"Invalid ObjectId: {report_id}")
                    continue
                
                # อัปเดตสถานะ verified เป็น 'yes' และบันทึก verification_time ใน collection white_url
                thai_timezone = pytz.timezone("Asia/Bangkok")
                verification_time = datetime.now(tz=thai_timezone).isoformat()
                
                # Update both 'verified' and 'verifited' for backward compatibility
                result = mongo.db.white_url.update_one(
                    {"_id": object_id},
                    {
                        "$set": {
                            "verified": "yes",
                            "verifited": "yes",
                            "verification_time": verification_time
                        }
                    }
                )
                print(f"DEBUG: Update result for {report_id}: matched={result.matched_count}, modified={result.modified_count}")
                
                if result.modified_count > 0:
                    updated_count += 1
                elif result.matched_count == 0:
                    errors.append(f"Report not found: {report_id}")
                    
            except Exception as e:
                print(f"Error updating whitelist report {report_id}: {e}")
                errors.append(f"Error for {report_id}: {str(e)}")

        if updated_count > 0:
            return jsonify({"status": "success", "message": f"Verified {updated_count} reports successfully"}), 200
        else:
            error_msg = "No reports were updated"
            if errors:
                error_msg += f". Errors: {'; '.join(errors)}"
            return jsonify({"status": "error", "error": error_msg}), 400

    except Exception as e:
        print(f"Error in whiteverify_report: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/whitedelete_report/<report_id>", methods=["POST"])
@admin_required
def whitedelete_report(report_id):
    try:
        from bson import ObjectId
        # ลบข้อมูลออกจาก white_url collection
        result = mongo.db.white_url.delete_one({"_id": ObjectId(report_id)})

        if result.deleted_count > 0:
            return jsonify({"status": "success", "message": translate_message("successful_deletion")}), 200
        else:
            return jsonify({"status": "error", "error": translate_message("deletion_failed")}), 500

    except Exception as e:
        print(f"Error in whitedelete_report: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/delete-selected-reports", methods=["POST"])
def delete_selected_reports():
    """Delete multiple reports at once"""
    try:
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"status": "error", "error": translate_message("unauthorized")}), 403
        
        data = request.get_json()
        report_ids = data.get("report_ids", [])
        
        if not report_ids:
            return jsonify({"status": "error", "error": translate_message("no_report_selected")}), 400
        
        deleted_count = 0
        from bson import ObjectId
        
        for report_id in report_ids:
            try:
                result = mongo.db.phish_url.delete_one({"_id": ObjectId(report_id)})
                if result.deleted_count > 0:
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting report {report_id}: {e}")
        
        if deleted_count > 0:
            PhishModel.invalidate_cache()
            return jsonify({"status": "success", "message": f"Deleted {deleted_count} reports successfully"}), 200
        else:
            return jsonify({"status": "error", "error": "No reports were deleted"}), 400
    
    except Exception as e:
        print(f"Error in delete_selected_reports: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/verify-selected-reports", methods=["POST"])
def verify_selected_reports():
    """Verify multiple reports at once"""
    try:
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"status": "error", "error": translate_message("unauthorized")}), 403
        
        data = request.get_json()
        report_ids = data.get("report_ids", [])
        
        if not report_ids:
            return jsonify({"status": "error", "error": translate_message("no_report_selected")}), 400
        
        updated_count = 0
        from bson import ObjectId
        
        for report_id in report_ids:
            try:
                # Update verification status and add verification time
                thai_timezone = pytz.timezone("Asia/Bangkok")
                verification_time = datetime.now(tz=thai_timezone).isoformat()
                
                result = mongo.db.phish_url.update_one(
                    {"_id": ObjectId(report_id)},
                    {
                        "$set": {
                            "verifited": "yes",
                            "verification_time": verification_time
                        }
                    }
                )
                if result.modified_count > 0:
                    updated_count += 1
            except Exception as e:
                print(f"Error updating report {report_id}: {e}")
        
        if updated_count > 0:
            return jsonify({"status": "success", "message": f"Verified {updated_count} reports successfully"}), 200
        else:
            return jsonify({"status": "error", "error": "No reports were updated"}), 400
    
    except Exception as e:
        print(f"Error in verify_selected_reports: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/whitedelete-selected-reports", methods=["POST"])
def white_delete_selected_reports():
    """Delete multiple white URL reports at once"""
    try:
        if "user_id" not in session or session.get("user_role") != "admin":
            return jsonify({"status": "error", "error": translate_message("unauthorized")}), 403
        
        data = request.get_json()
        report_ids = data.get("report_ids", [])
        
        if not report_ids:
            return jsonify({"status": "error", "error": translate_message("no_report_selected")}), 400
        
        deleted_count = 0
        from bson import ObjectId
        
        for report_id in report_ids:
            try:
                result = mongo.db.white_url.delete_one({"_id": ObjectId(report_id)})
                if result.deleted_count > 0:
                    deleted_count += 1
            except Exception as e:
                print(f"Error deleting white report {report_id}: {e}")
        
        if deleted_count > 0:
            return jsonify({"status": "success", "message": f"Deleted {deleted_count} white reports successfully"}), 200
        else:
            return jsonify({"status": "error", "error": "No reports were deleted"}), 400
    
    except Exception as e:
        print(f"Error in white_delete_selected_reports: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/download_sample_csv")
def download_sample_csv():
    """Download sample CSV file for report"""
    # Create a simple CSV content
    csv_content = "http://example.com\nhttps://phishing-site.com\nwww.google.com"
    
    # Create a BytesIO object
    proxy = io.BytesIO(csv_content.encode('utf-8'))
    
    return send_file(
        proxy,
        mimetype='text/csv',
        as_attachment=True,
        download_name='sample_urls.csv'
    )