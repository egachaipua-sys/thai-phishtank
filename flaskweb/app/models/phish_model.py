from app.create_app import mongo
from collections import OrderedDict
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta
from bson import ObjectId
import pytz

class PhishModel:
    """Model class for managing phishing URL data in MongoDB"""
    
    # Cache for frequently accessed data
    _cache = {}
    _cache_timeout = 300  # 5 minutes
    _last_cache_update = {}

    @staticmethod
    def _get_thai_timezone():
        """Get Thai timezone instance"""
        return pytz.timezone("Asia/Bangkok")

    @staticmethod
    def _get_current_time():
        """Get current time in Thai timezone as ISO format string"""
        thai_tz = PhishModel._get_thai_timezone()
        return datetime.now(tz=thai_tz).isoformat()

    @staticmethod
    def _is_cache_valid(cache_key):
        """Check if cache is still valid"""
        if cache_key not in PhishModel._cache:
            return False
        
        last_update = PhishModel._last_cache_update.get(cache_key, 0)
        return (datetime.now().timestamp() - last_update) < PhishModel._cache_timeout

    @staticmethod
    def _update_cache(cache_key, data):
        """Update cache with new data"""
        PhishModel._cache[cache_key] = data
        PhishModel._last_cache_update[cache_key] = datetime.now().timestamp()

    @staticmethod
    def find_by_url(url):
        """Find phishing URL by URL string"""
        try:
            result = mongo.db.phish_url.find_one({"url": url})
            return result  # Return the actual document, not just True
        except PyMongoError as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def find_index(limit=50):
        """Find phishing URLs for index page with optimized projection"""
        try:
            cache_key = f"index_{limit}"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            # Use projection to get only necessary fields for index page
            # Support both old and new field names for backward compatibility
            projection = {
                "_id": 0,
                "phish_id": 1,
                "url": 1,
                "online": 1,
                "submission_time": 1
            }
            # Add both possible field names for verified status
            projection["verified"] = 1
            projection["verifited"] = 1
            
            results = list(mongo.db.phish_url.find({}, projection).sort("submission_time", -1).limit(limit))
            
            # Normalize field names
            normalized_results = []
            for result in results:
                normalized_result = {k.strip(): v for k, v in result.items()}
                # Ensure we have a verified field (use verifited if verified doesn't exist)
                if "verified" not in normalized_result and "verifited" in normalized_result:
                    normalized_result["verified"] = normalized_result["verifited"]
                normalized_results.append(normalized_result)
            
            PhishModel._update_cache(cache_key, normalized_results)
            return normalized_results
        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def create_indexes():
        """Create database indexes for better performance"""
        try:
            mongo.db.phish_url.create_index([("submission_time", -1)])
            mongo.db.phish_url.create_index([("url", 1)])
            mongo.db.phish_url.create_index([("verified", 1)])
            print("Indexes created successfully.")
        except Exception as e:
            print(f"Error creating indexes: {e}")

    @staticmethod
    def find_country():
        """Find country distribution for the last 7 days"""
        try:
            cache_key = "country_data_v3"  # [CHANGED] new cache key
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            today_date = datetime.now()
            seven_days_ago_date = today_date - timedelta(days=7)
            today_str = today_date.strftime("%Y-%m-%d")
            seven_days_ago_str = seven_days_ago_date.strftime("%Y-%m-%d")

            pipeline = [
                {"$unwind": "$details"},
                {
                    "$match": {
                        "details.country": {"$exists": True, "$ne": "", "$ne": None},
                        "submission_time": {
                            "$gte": seven_days_ago_str,
                            "$lte": today_str + "T23:59:59"
                        }
                    }
                },
                {
                    "$group": {
                        "_id": "$details.country",
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "country": "$_id",  # [CHANGED] ใช้ "country" แทน "name" ให้ชัดเจน
                        "count": 1
                    }
                }
                # [REMOVED] ลบ filter latitude/longitude ออก เพราะใช้ countries_data.json แทน
            ]

            countries = list(mongo.db.phish_url.aggregate(pipeline))
            
            print(f"[find_country] Found {len(countries)} countries: {countries}")  # Debug log
            
            PhishModel._update_cache(cache_key, countries)
            return countries
        except Exception as e:
            print(f"Error fetching country data: {e}")
            return []

    @staticmethod
    def get_country_stats(limit=10):
        """Get aggregated country statistics for dashboard charts"""
        try:
            cache_key = f"country_stats_{limit}"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            pipeline = [
                {"$unwind": "$details"},
                {
                    "$match": {
                        "details.country": {"$exists": True, "$ne": "", "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$details.country",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": limit}
            ]

            results = list(mongo.db.phish_url.aggregate(pipeline))
            
            # Format for Chart.js
            stats = {
                "labels": [r["_id"] for r in results],
                "data": [r["count"] for r in results]
            }
            
            PhishModel._update_cache(cache_key, stats)
            return stats
        except Exception as e:
            print(f"Error get_country_stats: {e}")
            return {"labels": [], "data": []}

    @staticmethod
    def get_monthly_stats():
        """Get monthly submission statistics for the last 6 months"""
        try:
            cache_key = "monthly_stats"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            # Get data from the last 6 months
            today = datetime.now()
            six_months_ago = today - timedelta(days=180)
            
            pipeline = [
                {
                    "$match": {
                        "submission_time": {
                            "$gte": six_months_ago.strftime("%Y-%m-%d"),
                            "$lte": today.strftime("%Y-%m-%d") + "T23:59:59"
                        }
                    }
                },
                {
                    "$addFields": {
                        "month": {"$substr": ["$submission_time", 0, 7]}
                    }
                },
                {
                    "$group": {
                        "_id": "$month",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"_id": 1}}
            ]

            results = list(mongo.db.phish_url.aggregate(pipeline))
            
            stats = {
                "labels": [r["_id"] for r in results],
                "data": [r["count"] for r in results]
            }
            
            PhishModel._update_cache(cache_key, stats)
            return stats
        except Exception as e:
            print(f"Error get_monthly_stats: {e}")
            return {"labels": [], "data": []}

    @staticmethod
    def find_active():
        """Find count of active phishing URLs"""
        try:
            cache_key = "active_count"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            pipeline = [
                {"$match": {"online": "yes"}},
                {"$count": "active_count"}
            ]

            result = list(mongo.db.phish_url.aggregate(pipeline))
            count = result[0]["active_count"] if result else 0
            
            PhishModel._update_cache(cache_key, count)
            return count
        except Exception as e:
            print(f"Error fetching active phishing count: {e}")
            return 0

    @staticmethod
    def find_submit(user_id):
        """Find count of submissions by user"""
        try:
            if not user_id:
                return 0

            cache_key = f"submit_count_{user_id}"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "submission_time": {"$exists": True, "$ne": None}
                }},
                {"$count": "submit_count"}
            ]

            result = list(mongo.db.phish_url.aggregate(pipeline))
            count = result[0]["submit_count"] if result else 0
            
            PhishModel._update_cache(cache_key, count)
            return count

        except Exception as e:
            print(f"Error fetching submitted phishing URL count: {e}")
            return 0

    @staticmethod
    def find_verify(user_id):
        """Find count of verified reports by user"""
        try:
            if not user_id:
                return 0

            cache_key = f"verify_count_{user_id}"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            # Support both old and new field names for backward compatibility
            pipeline = [
                {"$match": {
                    "user_id": user_id,
                    "$or": [
                        {"verified": "yes"},     # New field name
                        {"verifited": "yes"}     # Old field name (backward compatibility)
                    ]
                }},
                {"$count": "verify_count"}
            ]

            result = list(mongo.db.phish_url.aggregate(pipeline))
            count = result[0]["verify_count"] if result else 0
            
            PhishModel._update_cache(cache_key, count)
            return count

        except Exception as e:
            print(f"Error fetching verified phishing URL count: {e}")
            return 0

    @staticmethod
    def find_today():
        """Find count of today's submissions"""
        try:
            cache_key = "today_count"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            thai_tz = PhishModel._get_thai_timezone()
            today = datetime.now(thai_tz).replace(hour=0, minute=0, second=0, microsecond=0)

            pipeline = [
                {"$match": {
                    "submission_time": {"$gte": today.isoformat()}
                }},
                {"$count": "today_count"}
            ]

            result = list(mongo.db.phish_url.aggregate(pipeline))
            count = result[0]["today_count"] if result else 0
            
            PhishModel._update_cache(cache_key, count)
            return count

        except Exception as e:
            print(f"Error fetching today's phishing URL count: {e}")
            return 0

    @staticmethod
    def find_total():
        """Find total count of phishing URLs"""
        try:
            cache_key = "total_count"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]

            pipeline = [
                {"$count": "total_count"}
            ]

            result = list(mongo.db.phish_url.aggregate(pipeline))
            count = result[0]["total_count"] if result else 0
            
            PhishModel._update_cache(cache_key, count)
            return count

        except Exception as e:
            print(f"Error fetching total phishing URL count: {e}")
            return 0

    @staticmethod
    def find_phish_id(phish_id):
        """Find phishing report by ID"""
        try:
            result = mongo.db.phish_url.find_one(
                {"phish_id": phish_id},
                {"_id": 0, "user_id": 0}
            )

            if result:
                # Clean keys by stripping whitespace
                result = {k.strip(): v for k, v in result.items()}
                
                ordered_result = OrderedDict([
                    ("phish_id", result.get("phish_id")),
                    ("url", result.get("url")),
                    ("reporter", result.get("reporter")),
                    ("submission_time", result.get("submission_time")),
                    ("verified", result.get("verified") or result.get("verifited", "no")),  # Support both
                    ("verification_time", result.get("verification_time")),
                    ("online", result.get("online")),
                    ("details", result.get("details"))
                ])
                return ordered_result
            return None

        except PyMongoError as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def save_report(user_id, url, reporter):
        """Save new phishing report"""
        try:
            thai_tz = PhishModel._get_thai_timezone()
            submission_time = datetime.now(tz=thai_tz).isoformat()
            
            # ตรวจสอบว่า URL นี้มีอยู่แล้วหรือไม่
            # ตรวจสอบว่า URL นี้มีอยู่แล้วหรือไม่ (เช็คทั้ง http และ https)
            url_variants = [url]
            if url.startswith("http://"):
                url_variants.append(url.replace("http://", "https://", 1))
            elif url.startswith("https://"):
                url_variants.append(url.replace("https://", "http://", 1))
            
            existing_report = mongo.db.phish_url.find_one({"url": {"$in": url_variants}})
            if existing_report:
                return "duplicate"

            report_data = {
                "user_id": user_id,
                "url": url,
                "reporter": reporter,
                "submission_time": submission_time,
                "verified": "no",  # Use new field name
                "type": "phishing"
            }
            
            result = mongo.db.phish_url.insert_one(report_data)
            PhishModel.invalidate_cache()
            return result.inserted_id
            
        except PyMongoError as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def save_whitelist_report(user_id, url, reporter):
        """Save new whitelist report"""
        try:
            thai_tz = PhishModel._get_thai_timezone()
            submission_time = datetime.now(tz=thai_tz).isoformat()
            
            # ตรวจสอบว่า URL นี้มีอยู่แล้วหรือไม่ (เช็คทั้ง http และ https)
            url_variants = [url]
            if url.startswith("http://"):
                url_variants.append(url.replace("http://", "https://", 1))
            elif url.startswith("https://"):
                url_variants.append(url.replace("https://", "http://", 1))

            existing_report = mongo.db.white_url.find_one({"url": {"$in": url_variants}})
            if existing_report:
                return "duplicate"

            report_data = {
                "user_id": user_id,
                "url": url,
                "reporter": reporter,
                "submission_time": submission_time,
                "verified": "no"  # Use new field name
            }
            
            result = mongo.db.white_url.insert_one(report_data)
            return result.inserted_id
            
        except PyMongoError as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    @staticmethod
    def get_user_reports(user_id):
        """Get all reports by user"""
        try:
            reports = list(
                mongo.db.phish_url.find({"user_id": user_id})
                .sort("submission_time", -1)
            )
            
            # Clean keys
            cleaned_reports = []
            for report in reports:
                cleaned_report = {key.strip(): value for key, value in report.items()}
                cleaned_reports.append(cleaned_report)
            
            return cleaned_reports

        except PyMongoError as e:
            print(f"Database error: {e}")
            return []

        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def get_whitetable_reports(user_id):
        """Get whitelist reports for user"""
        try:
            reports = list(
                mongo.db.white_url.find({"user_id": user_id})
                .sort("submission_time", -1)
            )
            
            # Clean keys
            cleaned_reports = []
            for report in reports:
                cleaned_report = {key.strip(): value for key, value in report.items()}
                cleaned_reports.append(cleaned_report)
            
            return cleaned_reports
            
        except Exception as e:
            print(f"Error in get_whitetable_reports: {e}")
            return []

    @staticmethod
    def get_whitecheck_reports():
        """Get all whitelist reports for admin check"""
        try:
            reports = list(mongo.db.white_url.find().sort("submission_time", -1))
            
            # Clean keys
            cleaned_reports = []
            for report in reports:
                cleaned_report = {key.strip(): value for key, value in report.items()}
                cleaned_reports.append(cleaned_report)
            
            return cleaned_reports
            
        except Exception as e:
            print(f"Error in get_whitecheck_reports: {e}")
            return []

    @staticmethod
    def get_blacktable_reports(user_id):
        """Get blacklisted reports for user (alias for get_user_reports)"""
        return PhishModel.get_user_reports(user_id)

    @staticmethod
    def get_check_reports():
        """Get all reports for admin check"""
        try:
            reports = list(mongo.db.phish_url.find().sort("submission_time", -1))
            
            # Clean keys by stripping whitespace and normalize verified field
            cleaned_reports = []
            for report in reports:
                cleaned_report = {key.strip(): value for key, value in report.items()}
                # Normalize verified field for backward compatibility
                if "verified" not in cleaned_report and "verifited" in cleaned_report:
                    cleaned_report["verified"] = cleaned_report["verifited"]
                cleaned_reports.append(cleaned_report)
            
            return cleaned_reports

        except PyMongoError as e:
            print(f"Database error: {e}")
            return []

        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def delete_report(report_id):
        """Delete a report by ID"""
        try:
            report_id = ObjectId(report_id)

            result = mongo.db.phish_url.delete_one({"_id": report_id})

            if result.deleted_count == 1:
                PhishModel.invalidate_cache()
                return True
            else:
                return None

        except PyMongoError as e:
            print(f"Database error in delete_report: {e}")
            return None

        except Exception as e:
            print(f"Unexpected error in delete_report: {e}")
            return None

    @staticmethod
    def update_report_verification(report_id, verified_status="yes"):
        """Update report verification status"""
        try:
            report_id = ObjectId(report_id)
            thai_tz = PhishModel._get_thai_timezone()
            verification_time = datetime.now(tz=thai_tz).isoformat()

            result = mongo.db.phish_url.update_one(
                {"_id": report_id},
                {
                    "$set": {
                        "verified": verified_status,  # Fixed typo
                        "verification_time": verification_time
                    }
                }
            )

            if result.modified_count > 0:
                PhishModel.invalidate_cache()
                return True
            return False

        except PyMongoError as e:
            print(f"Database error in update_report_verification: {e}")
            return False

        except Exception as e:
            print(f"Unexpected error in update_report_verification: {e}")
            return False

    @staticmethod
    def update_whitelist_verification(report_id, verified_status="yes"):
        """Update whitelist report verification status"""
        try:
            report_id = ObjectId(report_id)
            thai_tz = PhishModel._get_thai_timezone()
            verification_time = datetime.now(tz=thai_tz).isoformat()

            result = mongo.db.white_url.update_one(
                {"_id": report_id},
                {
                    "$set": {
                        "verified": verified_status,  # Fixed typo
                        "verification_time": verification_time
                    }
                }
            )

            return result.modified_count > 0

        except PyMongoError as e:
            print(f"Database error in update_whitelist_verification: {e}")
            return False

        except Exception as e:
            print(f"Unexpected error in update_whitelist_verification: {e}")
            return False

    @staticmethod
    def delete_whitelist_report(report_id):
        """Delete a whitelist report by ID"""
        try:
            report_id = ObjectId(report_id)

            result = mongo.db.white_url.delete_one({"_id": report_id})

            return result.deleted_count == 1

        except PyMongoError as e:
            print(f"Database error in delete_whitelist_report: {e}")
            return False

        except Exception as e:
            print(f"Unexpected error in delete_whitelist_report: {e}")
            return False

    @staticmethod
    def invalidate_cache():
        """Invalidate all cache"""
        PhishModel._cache.clear()
        PhishModel._last_cache_update.clear()

    @staticmethod
    def count_all():
        """Count all documents in phish_url collection"""
        try:
            cache_key = "count_all"
            if PhishModel._is_cache_valid(cache_key):
                return PhishModel._cache[cache_key]
                
            count = mongo.db.phish_url.count_documents({})
            PhishModel._update_cache(cache_key, count)
            return count
            
        except Exception as e:
            print(f"Error count_all: {e}")
            return 0

    @staticmethod
    def count_filtered(query):
        """Count documents matching query"""
        try:
            return mongo.db.phish_url.count_documents(query)
        except Exception as e:
            print(f"Error count_filtered: {e}")
            return 0

    @staticmethod
    def find_for_datatable(query, start, length):
        """Find documents for DataTables with pagination"""
        try:
            # Use projection for optimal performance
            # Support both old and new field names
            projection = {
                "_id": 0,
                "phish_id": 1,
                "url": 1,
                "online": 1,
                "submission_time": 1
            }
            # Add both possible field names for verified status
            projection["verified"] = 1
            projection["verifited"] = 1
            
            results = list(
                mongo.db.phish_url.find(query, projection)
                .sort("submission_time", -1)
                .skip(start)
                .limit(length)
            )
            
            # Normalize results to handle backward compatibility
            normalized_results = []
            for result in results:
                normalized_result = {k.strip(): v for k, v in result.items()}
                
                # [FIX] Ensure phish_id exists to prevent DataTables error
                if "phish_id" not in normalized_result:
                     # หากไม่มี phish_id ให้ลองใช้ _id (ถ้ามี) หรือ "-"
                     normalized_result["phish_id"] = str(result.get("_id", "-"))
                
                # Ensure we have a verified field (use verifited if verified doesn't exist, default to "no")
                if "verified" not in normalized_result:
                    normalized_result["verified"] = normalized_result.get("verifited", "no")
                
                normalized_results.append(normalized_result)
            
            return normalized_results
        except Exception as e:
            print(f"Error find_for_datatable: {e}")
            return []

    @staticmethod
    def count_check_reports(query=None):
        """Count all check reports (unfiltered or filtered)"""
        try:
            if query:
                return mongo.db.phish_url.count_documents(query)
            return mongo.db.phish_url.count_documents({})
        except Exception as e:
            print(f"Error count_check_reports: {e}")
            return 0

    @staticmethod
    def find_check_reports_for_datatable(query, start, length):
        """Find check reports for DataTables with pagination - includes all fields needed for admin"""
        try:
            projection = {
                "_id": 1,
                "url": 1,
                "reporter": 1,
                "submission_time": 1,
                "verified": 1,
                "verifited": 1
            }
            
            results = list(
                mongo.db.phish_url.find(query, projection)
                .sort("submission_time", -1)
                .skip(start)
                .limit(length)
            )
            
            # Normalize results for admin datatable
            normalized_results = []
            for result in results:
                normalized_result = {k.strip(): v for k, v in result.items()}
                # Convert ObjectId to string for JSON serialization
                if "_id" in normalized_result:
                    normalized_result["_id"] = str(normalized_result["_id"])
                # Ensure we have a verified field (use verifited if verified doesn't exist, default to "no")
                if "verified" not in normalized_result:
                    normalized_result["verified"] = normalized_result.get("verifited", "no")
                normalized_results.append(normalized_result)
            
            return normalized_results
        except Exception as e:
            print(f"Error find_check_reports_for_datatable: {e}")
            return []

    @staticmethod
    def count_user_reports(user_id, query=None):
        """Count user reports (unfiltered or filtered)"""
        try:
            base_query = {"user_id": user_id}
            if query:
                base_query.update(query)
            return mongo.db.phish_url.count_documents(base_query)
        except Exception as e:
            print(f"Error count_user_reports: {e}")
            return 0

    @staticmethod
    def find_user_reports_for_datatable(user_id, query, start, length):
        """Find user reports for DataTables with pagination"""
        try:
            base_query = {"user_id": user_id}
            if query:
                base_query.update(query)
            
            projection = {
                "_id": 1,
                "url": 1,
                "reporter": 1,
                "submission_time": 1,
                "verified": 1,
                "verifited": 1
            }
            
            results = list(
                mongo.db.phish_url.find(base_query, projection)
                .sort("submission_time", -1)
                .skip(start)
                .limit(length)
            )
            
            normalized_results = []
            for result in results:
                normalized_result = {k.strip(): v for k, v in result.items()}
                if "_id" in normalized_result:
                    normalized_result["_id"] = str(normalized_result["_id"])
                if "verified" not in normalized_result:
                    normalized_result["verified"] = normalized_result.get("verifited", "no")
                normalized_results.append(normalized_result)
            
            return normalized_results
        except Exception as e:
            print(f"Error find_user_reports_for_datatable: {e}")
            return []

    @staticmethod
    def count_white_check_reports(query=None):
        """Count all whitelist check reports (unfiltered or filtered)"""
        try:
            if query:
                return mongo.db.white_url.count_documents(query)
            return mongo.db.white_url.count_documents({})
        except Exception as e:
            print(f"Error count_white_check_reports: {e}")
            return 0

    @staticmethod
    def find_white_check_reports_for_datatable(query, start, length):
        """Find whitelist check reports for DataTables with pagination"""
        try:
            projection = {
                "_id": 1,
                "url": 1,
                "reporter": 1,
                "submission_time": 1,
                "verified": 1,
                "verifited": 1
            }
            
            results = list(
                mongo.db.white_url.find(query, projection)
                .sort("submission_time", -1)
                .skip(start)
                .limit(length)
            )
            
            normalized_results = []
            for result in results:
                normalized_result = {k.strip(): v for k, v in result.items()}
                if "_id" in normalized_result:
                    normalized_result["_id"] = str(normalized_result["_id"])
                if "verified" not in normalized_result and "verifited" in normalized_result:
                    normalized_result["verified"] = normalized_result["verifited"]
                normalized_results.append(normalized_result)
            
            return normalized_results
        except Exception as e:
            print(f"Error find_white_check_reports_for_datatable: {e}")
            return []

    @staticmethod
    def count_user_white_reports(user_id, query=None):
        """Count user whitelist reports (unfiltered or filtered)"""
        try:
            base_query = {"user_id": user_id}
            if query:
                base_query.update(query)
            return mongo.db.white_url.count_documents(base_query)
        except Exception as e:
            print(f"Error count_user_white_reports: {e}")
            return 0

    @staticmethod
    def find_user_white_reports_for_datatable(user_id, query, start, length):
        """Find user whitelist reports for DataTables with pagination"""
        try:
            base_query = {"user_id": user_id}
            if query:
                base_query.update(query)
            
            projection = {
                "_id": 1,
                "url": 1,
                "reporter": 1,
                "submission_time": 1,
                "verified": 1,
                "verifited": 1
            }
            
            results = list(
                mongo.db.white_url.find(base_query, projection)
                .sort("submission_time", -1)
                .skip(start)
                .limit(length)
            )
            
            normalized_results = []
            for result in results:
                normalized_result = {k.strip(): v for k, v in result.items()}
                if "_id" in normalized_result:
                    normalized_result["_id"] = str(normalized_result["_id"])
                if "verified" not in normalized_result and "verifited" in normalized_result:
                    normalized_result["verified"] = normalized_result["verifited"]
                normalized_results.append(normalized_result)
            
            return normalized_results
        except Exception as e:
            print(f"Error find_user_white_reports_for_datatable: {e}")
            return []

    @staticmethod
    def bulk_verify_reports(report_ids, collection_name="phish_url"):
        """Verify multiple reports at once"""
        try:
            if not report_ids:
                return 0

            object_ids = [ObjectId(report_id) for report_id in report_ids]
            thai_tz = PhishModel._get_thai_timezone()
            verification_time = datetime.now(tz=thai_tz).isoformat()

            result = mongo.db[collection_name].update_many(
                {"_id": {"$in": object_ids}},
                {
                    "$set": {
                        "verified": "yes",  # Fixed typo
                        "verification_time": verification_time
                    }
                }
            )

            if result.modified_count > 0:
                PhishModel.invalidate_cache()

            return result.modified_count

        except Exception as e:
            print(f"Error in bulk_verify_reports: {e}")
            return 0

    @staticmethod
    def migrate_verifited_to_verified():
        """Migrate records from 'verifited' field to 'verified' field for backward compatibility"""
        try:
            print("Starting migration from 'verifited' to 'verified' field...")
            
            # Update phish_url collection
            phish_result = mongo.db.phish_url.update_many(
                {"verifited": {"$exists": True}, "verified": {"$exists": False}},
                {
                    "$set": {"verified": "$verifited"},
                    "$unset": {"verifited": ""}
                }
            )
            
            # Update white_url collection  
            white_result = mongo.db.white_url.update_many(
                {"verifited": {"$exists": True}, "verified": {"$exists": False}},
                {
                    "$set": {"verified": "$verifited"},
                    "$unset": {"verifited": ""}
                }
            )
            
            print(f"Migration completed. Updated {phish_result.modified_count} phish_url records and {white_result.modified_count} white_url records.")
            
            # Invalidate cache after migration
            PhishModel.invalidate_cache()
            
            return True
            
        except Exception as e:
            print(f"Error during migration: {e}")
            return False

    @staticmethod
    def bulk_delete_reports(report_ids, collection_name="phish_url"):
        """Delete multiple reports at once"""
        try:
            if not report_ids:
                return 0

            object_ids = [ObjectId(report_id) for report_id in report_ids]

            result = mongo.db[collection_name].delete_many(
                {"_id": {"$in": object_ids}}
            )

            if result.deleted_count > 0:
                PhishModel.invalidate_cache()

            return result.deleted_count

        except Exception as e:
            print(f"Error in bulk_delete_reports: {e}")
            return 0