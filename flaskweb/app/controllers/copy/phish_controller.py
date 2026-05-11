from flask import Blueprint, json, jsonify, request, session, render_template
from app.models.phish_model import PhishModel
from app.create_app import mongo
from app.config import Config
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
            'no_report_selected': 'No reports selected.'
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
            'no_report_selected': 'ไม่ได้เลือกรายงาน'
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
        search_value = request.form.get("search[value]", type=str, default="")

        # จัดการ Search filter
        query = {}
        if search_value:
            # ค้นหาจาก phish_id หรือ url
            query = {
                "$or": [
                    {"phish_id": {"$regex": search_value, "$options": "i"}},
                    {"url": {"$regex": search_value, "$options": "i"}}
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

@controller_blueprint.route("/check_url", methods=["POST"])
def check_url():
    try:
        data = request.get_json()
        url_to_check = data.get("url")

        if not url_to_check.startswith("http://") and not url_to_check.startswith("https://"):
            url_to_check = "https://" + url_to_check

        if not url_to_check:
            return jsonify({"error": translate_message("url_required"), "status": "error"}), 400

        fastapi_url = f"{Config.DOMAIN_NAME}/api/phishing-url"
        params = {"url": url_to_check, "api_key": Config.API_KEY}

        with requests.post(fastapi_url, params=params) as response:
            response.raise_for_status()
            fastapi_result = response.json()

        if fastapi_result["prediction"] == "phishing":
            result = {
                "status": "warning",
                "prediction": fastapi_result["prediction"],
                "message": translate_message("url_is_phishing").format(url=url_to_check),
            }
        elif fastapi_result["prediction"] == "offline":
             result = {
                "status": "error",
                "prediction": fastapi_result["prediction"],
                "message": translate_message("url_is_offline").format(url=url_to_check),
            }
        else:
            result = {
                "status": "success",
                "prediction": fastapi_result["prediction"],
                "message": translate_message("url_is_safe").format(url=url_to_check),
            }

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
        url = request.form.get("url")

        if not url or not reporter:
             return jsonify({"status": "error", "error": translate_message("missing_fields")}), 400

        # Validate URL
        if not is_valid_url(url):
             return jsonify({"status": "error", "error": translate_message("invalid_url")}), 400

        # Save Whitelist Report
        success = PhishModel.save_whitelist_report(user_id, url, reporter)
         
        if success:
             return jsonify({"status": "success", "message": translate_message("report_success")}), 200
        else:
             return jsonify({"status": "error", "error": translate_message("report_failed")}), 500

    except Exception as e:
        print(f"Error in report_legitimate: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


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
            save_success = PhishModel.save_report(
                user_id=user_id, url=url_item, reporter=reporter
            )
            if save_success:
                processed_results.append({"url": url_item, "status": "success"})
            else:
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
def verify_report():
    try:
        data = request.get_json()
        url_to_check = data.get("url")

        if not url_to_check.startswith("http://") and not url_to_check.startswith("https://"):
            url_to_check = "https://" + url_to_check

        if not url_to_check:
            return jsonify({"status": "error", "message": translate_message("url_required")}), 400

        fastapi_url = f"{Config.DOMAIN_NAME}/api/verifited-url"
        params = {"url": url_to_check, "api_key": Config.ADMIN_KEY}

        with requests.post(fastapi_url, params=params) as response:
            response.raise_for_status()

            if response.status_code < 400:
                try:
                    fastapi_result = response.json()
                    if "prediction" in fastapi_result and "url" in fastapi_result:
                        result = {
                            "status": "success",
                            "prediction": fastapi_result["prediction"],
                            "url": fastapi_result["url"],
                        }
                        return jsonify(result)
                    else:
                        print(f"Error: Missing keys in FastAPI response: {fastapi_result}")
                        return jsonify({"status": "error", "message": translate_message("invalid_api_response")}), 500

                except json.JSONDecodeError:
                    print("Error: Invalid JSON response from API")
                    return jsonify({"status": "error", "message": translate_message("invalid_api_response")}), 500

            else:
                print(f"Error: FastAPI returned status code {response.status_code}")
                return jsonify({"status": "error", "message": translate_message("error_occurred")}), 500


    except requests.exceptions.RequestException as e:
        print(f"Error calling FastAPI: {e}")
        return jsonify({"status": "error", "message": translate_message("error_occurred"), "error": str(e)}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": translate_message("error_occurred"), "error": str(e)}), 500


@controller_blueprint.route("/delete_report/<report_id>", methods=["POST"])
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
    print("DEBUG: Registering whiteverify_report route")
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
                # อัปเดตสถานะ verifited เป็น 'yes' และบันทึก verification_time ใน collection white_url
                thai_timezone = pytz.timezone("Asia/Bangkok")
                verification_time = datetime.now(tz=thai_timezone).isoformat()
                
                result = mongo.db.white_url.update_one(
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
                print(f"Error updating whitelist report {report_id}: {e}")

        if updated_count > 0:
            return jsonify({"status": "success", "message": f"Verified {updated_count} reports successfully"}), 200
        else:
            return jsonify({"status": "error", "error": "No reports were updated"}), 400

    except Exception as e:
        print(f"Error in whiteverify_report: {e}")
        return jsonify({"status": "error", "error": translate_message("error_occurred"), "message": str(e)}), 500


@controller_blueprint.route("/whitedelete_report/<report_id>", methods=["POST"])
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