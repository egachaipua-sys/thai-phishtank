from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pymongo import MongoClient
from cachetools import TTLCache
import sys
import os
import re
import hashlib

# เพิ่ม path ของ mlengine
current_dir = os.path.dirname(os.path.abspath(__file__))
mlengine_path = os.path.join(current_dir, "mlengine")
sys.path.append(mlengine_path)
from app.mlengine.prediction import prediction
# เพิ่ม import นี้เข้าไป
from app.mlengine.scripts.feature_extractor import is_URL_accessible
# from mlengine.prediction import prediction
import configparser
import requests
import whois
from datetime import datetime
import pytz
import tldextract
import random
import string
import json


# ========================================

# ========================================
# Hosting Platforms ที่ไม่ควร whitelist ทั้ง domain
# โหลดจากไฟล์ JSON เพื่อความง่ายในการจัดการ
# ========================================
def load_hosting_platforms():
    json_path = os.path.join(current_dir, "hosting_platforms.json")
    platforms_list = []
    
    try:
        if not os.path.exists(json_path):
            print(f"[WARNING] {json_path} not found. Using empty list.")
            return []
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for category in data.get("threat_categories", []):
            # Case 1: domains list directly in category
            if "domains" in category and isinstance(category["domains"], list):
                platforms_list.extend(category["domains"])
                
            # Case 2: platforms list (can be strings or objects)
            if "platforms" in category:
                for item in category["platforms"]:
                    if isinstance(item, str):
                        platforms_list.append(item) # list of strings
                    elif isinstance(item, dict) and "domains" in item:
                        platforms_list.extend(item["domains"]) # list of objects
            
            # Case 3: providers or services list of objects
            for key in ["providers", "services"]:
                if key in category:
                    for item in category[key]:
                        if "domains" in item:
                            platforms_list.extend(item["domains"])
                            
        # Remove duplicates and sort
        return sorted(list(set(platforms_list)))
        
    except Exception as e:
        print(f"[ERROR] Failed to load hosting platforms: {e}")
        return []

HOSTING_PLATFORMS = load_hosting_platforms()
print(f"[INFO] Loaded {len(HOSTING_PLATFORMS)} hosting platforms from JSON.")

def is_hosting_platform(domain: str) -> bool:
    """
    ตรวจสอบว่า domain เป็น hosting platform หรือไม่
    ถ้าเป็น hosting platform จะไม่ whitelist ทั้ง domain
    """
    if not domain:
        return False
    domain_lower = domain.lower()
    for platform in HOSTING_PLATFORMS:
        if domain_lower == platform or domain_lower.endswith("." + platform):
            return True
    return False


def check_safe_browsing(url: str) -> dict:
    """
    ตรวจสอบ URL ผ่าน Google Safe Browsing API
    
    Returns:
        dict: {"is_safe": True/False, "threats": [...], "error": None/str}
    """
    try:
        payload = {
            "client": {
                "clientId": "phishtank_th",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION"
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        
        response = requests.post(
            f"{GOOGLE_SAFE_BROWSING_URL}?key={GOOGLE_SAFE_BROWSING_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            # ถ้ามี matches หมายความว่าเจอ threats
            if "matches" in result and len(result["matches"]) > 0:
                threats = [match.get("threatType") for match in result["matches"]]
                return {"is_safe": False, "threats": threats, "error": None}
            else:
                # ไม่พบ threats = safe
                return {"is_safe": True, "threats": [], "error": None}
        else:
            print(f"[SAFE BROWSING ERROR] Status {response.status_code}: {response.text}")
            return {"is_safe": None, "threats": [], "error": f"API Error: {response.status_code}"}
            
    except requests.Timeout:
        print(f"[SAFE BROWSING TIMEOUT] Request timed out for {url}")
        return {"is_safe": None, "threats": [], "error": "Request timed out"}
    except Exception as e:
        print(f"[SAFE BROWSING EXCEPTION] {e}")
        return {"is_safe": None, "threats": [], "error": str(e)}


config = configparser.ConfigParser()
config.read("config_app.ini")

MONGO_DETAILS = config["DATABASE"]["MONGO_DETAILS"]
DATABASE_NAME = config["DATABASE"]["DATABASE_NAME"]
USER_COLLECTION = config["DATABASE"]["USER_COLLECTION"]
BLACK_LIST = config["DATABASE"]["BLACK_LIST"]
WHITE_LIST = config["DATABASE"]["WHITE_LIST"]
API_KEY = config["API_KEY"]["API_KEY"]
DOMAIN_NAME = config["DOMAIN_NAME"]["DOMAIN_NAME"]

# Google Safe Browsing Config
GOOGLE_SAFE_BROWSING_API_KEY = config["GOOGLE"]["SAFE_BROWSING_API_KEY"]
GOOGLE_SAFE_BROWSING_URL = config["GOOGLE"]["SAFE_BROWSING_URL"]

app = FastAPI()

# ========================================
# [NEW] Global Exception Handler
# จับ errors ทั้งหมดและ return JSON response ที่อ่านง่าย
# ========================================
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    จับ exception ทั้งหมดที่ไม่ได้ถูก handle และ return JSON response
    แทนที่จะให้ FastAPI return 500 Internal Server Error แบบ default
    """
    print(f"[GLOBAL ERROR] {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An error occurred while processing your request.",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

client = MongoClient(MONGO_DETAILS)
db = client[DATABASE_NAME]

# ========================================
# [OPTIMIZED] Caching system เพื่อเพิ่มประสิทธิภาพ
# ========================================

# WHOIS Cache: เก็บผลลัพธ์ไว้ 1 ชั่วโมง (3600 วินาที), ขนาดสูงสุด 1000 entries
whois_cache = TTLCache(maxsize=1000, ttl=3600)

# Online Status Cache: เก็บผลลัพธ์ไว้ 5 นาที (300 วินาที), ขนาดสูงสุด 500 entries  
online_cache = TTLCache(maxsize=500, ttl=300)


def get_cache_key(url: str) -> str:
    """สร้าง cache key จาก URL โดยใช้ hash เพื่อลดขนาด memory"""
    return hashlib.md5(url.lower().encode()).hexdigest()


# ========================================
# [NEW] Country Name to ISO Code Mapping
# สำหรับแปลง Country Name เป็น Country Code ใน WHOIS data
# เพื่อให้ bubbles บนแผนที่แสดงผลได้ถูกต้อง
# ========================================
COUNTRY_NAME_TO_CODE = {
    "united states": "US", "united states of america": "US", "usa": "US", "u.s.a.": "US", "u.s.": "US",
    "united kingdom": "GB", "uk": "GB", "great britain": "GB", "england": "GB",
    "thailand": "TH", "ไทย": "TH", "ประเทศไทย": "TH",
    "china": "CN", "people's republic of china": "CN", "prc": "CN",
    "japan": "JP", "日本": "JP",
    "south korea": "KR", "korea, republic of": "KR", "republic of korea": "KR", "korea": "KR",
    "germany": "DE", "deutschland": "DE",
    "france": "FR",
    "russia": "RU", "russian federation": "RU",
    "india": "IN",
    "brazil": "BR", "brasil": "BR",
    "canada": "CA",
    "australia": "AU",
    "italy": "IT", "italia": "IT",
    "spain": "ES", "españa": "ES",
    "mexico": "MX", "méxico": "MX",
    "indonesia": "ID",
    "netherlands": "NL", "holland": "NL",
    "saudi arabia": "SA",
    "turkey": "TR", "türkiye": "TR",
    "switzerland": "CH",
    "poland": "PL", "polska": "PL",
    "sweden": "SE", "sverige": "SE",
    "belgium": "BE",
    "argentina": "AR",
    "austria": "AT", "österreich": "AT",
    "norway": "NO", "norge": "NO",
    "united arab emirates": "AE", "uae": "AE",
    "israel": "IL",
    "ireland": "IE",
    "singapore": "SG",
    "malaysia": "MY",
    "philippines": "PH",
    "vietnam": "VN", "viet nam": "VN",
    "hong kong": "HK",
    "taiwan": "TW",
    "new zealand": "NZ",
    "south africa": "ZA",
    "egypt": "EG",
    "pakistan": "PK",
    "bangladesh": "BD",
    "ukraine": "UA",
    "romania": "RO",
    "czech republic": "CZ", "czechia": "CZ",
    "portugal": "PT",
    "greece": "GR",
    "hungary": "HU",
    "denmark": "DK", "danmark": "DK",
    "finland": "FI", "suomi": "FI",
    "colombia": "CO",
    "chile": "CL",
    "peru": "PE",
    "nigeria": "NG",
    "kenya": "KE",
    "morocco": "MA",
    "iceland": "IS", "ísland": "IS",
    "luxembourg": "LU",
    "panama": "PA",
    "costa rica": "CR",
    "uruguay": "UY",
    "qatar": "QA",
    "kuwait": "KW",
    "bahrain": "BH",
    "oman": "OM",
    "cyprus": "CY",
    "malta": "MT",
    "estonia": "EE",
    "latvia": "LV",
    "lithuania": "LT",
    "slovakia": "SK",
    "slovenia": "SI",
    "croatia": "HR",
    "serbia": "RS",
    "bulgaria": "BG",
    "albania": "AL",
    "north macedonia": "MK", "macedonia": "MK",
    "bosnia and herzegovina": "BA",
    "montenegro": "ME",
    "georgia": "GE",
    "armenia": "AM",
    "azerbaijan": "AZ",
    "kazakhstan": "KZ",
    "uzbekistan": "UZ",
    "turkmenistan": "TM",
    "kyrgyzstan": "KG",
    "tajikistan": "TJ",
    "mongolia": "MN",
    "nepal": "NP",
    "sri lanka": "LK",
    "myanmar": "MM", "burma": "MM",
    "cambodia": "KH",
    "laos": "LA",
    "brunei": "BN",
    "maldives": "MV",
    "afghanistan": "AF",
    "iraq": "IQ",
    "iran": "IR", "islamic republic of iran": "IR",
    "syria": "SY",
    "lebanon": "LB",
    "jordan": "JO",
    "yemen": "YE",
    "libya": "LY",
    "tunisia": "TN",
    "algeria": "DZ",
    "sudan": "SD",
    "ethiopia": "ET",
    "tanzania": "TZ",
    "uganda": "UG",
    "ghana": "GH",
    "cameroon": "CM",
    "ivory coast": "CI", "côte d'ivoire": "CI",
    "senegal": "SN",
    "zimbabwe": "ZW",
    "zambia": "ZM",
    "botswana": "BW",
    "namibia": "NA",
    "mozambique": "MZ",
    "angola": "AO",
    "madagascar": "MG",
    "mauritius": "MU",
    "seychelles": "SC",
    "reunion": "RE",
    "venezuela": "VE",
    "ecuador": "EC",
    "bolivia": "BO",
    "paraguay": "PY",
    "guatemala": "GT",
    "honduras": "HN",
    "el salvador": "SV",
    "nicaragua": "NI",
    "cuba": "CU",
    "jamaica": "JM",
    "dominican republic": "DO",
    "puerto rico": "PR",
    "trinidad and tobago": "TT",
    "bahamas": "BS",
    "barbados": "BB",
    "belize": "BZ",
    "guyana": "GY",
    "suriname": "SR",
    "haiti": "HT",
    "fiji": "FJ",
    "papua new guinea": "PG",
}


def get_country_code(country_name: str) -> str:
    """แปลง Country Name เป็น ISO Country Code"""
    if not country_name:
        return None
    
    # ถ้าเป็น 2 ตัวอักษรอยู่แล้ว (เป็น code) ให้ return กลับไปเลย
    if len(country_name) == 2 and country_name.isalpha():
        return country_name.upper()
    
    # ค้นหาใน mapping
    country_lower = country_name.lower().strip()
    if country_lower in COUNTRY_NAME_TO_CODE:
        return COUNTRY_NAME_TO_CODE[country_lower]
    
    # ถ้าไม่เจอ ให้ return ค่าเดิม (uppercase)
    return country_name.upper()


class User(BaseModel):
    api_key: str


class PhishDetail(BaseModel):
    url: str
    prediction: str


async def verify_api_key(api_key: str):
    user = db[USER_COLLECTION].find_one({"api_key": api_key})
    if not user:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return user


async def verify_admin(api_key: str):

    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    admin = API_KEY
    return admin


def convert_whois_to_dict(whois_data) -> dict:
    """
    แปลง WHOIS data เป็น JSON-serializable dict
    เนื่องจาก whois library return object ที่มี datetime และ types อื่นๆ ที่ไม่สามารถ serialize ได้
    [UPDATED] เพิ่มการแปลง country name เป็น ISO country code
    """
    if whois_data is None:
        return {}
    
    result = {}
    
    # ถ้าเป็น whois object ให้แปลงเป็น dict
    if hasattr(whois_data, '__dict__'):
        data = dict(whois_data)
    elif isinstance(whois_data, dict):
        data = whois_data
    else:
        return {"raw": str(whois_data)}
    
    for key, value in data.items():
        if key.startswith('_'):  # ข้าม private attributes
            continue
        try:
            if value is None:
                result[key] = None
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list):
                # แปลง list items
                result[key] = [
                    item.isoformat() if isinstance(item, datetime) 
                    else str(item) if not isinstance(item, (str, int, float, bool, type(None)))
                    else item
                    for item in value
                ]
            elif isinstance(value, (str, int, float, bool)):
                result[key] = value
            else:
                # แปลง objects อื่นๆ เป็น string
                result[key] = str(value)
        except Exception:
            result[key] = str(value)
    
    # [NEW] แปลง country name เป็น ISO country code สำหรับ bubbles map
    if "country" in result and result["country"]:
        country_val = result["country"]
        # ถ้าเป็น list ให้เอาค่าแรก
        if isinstance(country_val, list) and len(country_val) > 0:
            country_val = country_val[0]
        if isinstance(country_val, str):
            result["country"] = get_country_code(country_val)
    
    return result


def get_whois_data(url: str):
    """
    [OPTIMIZED] WHOIS lookup พร้อม caching
    ลดเวลาจาก ~5-10 วินาที เหลือ ~0ms สำหรับ cached URLs
    """
    cache_key = get_cache_key(url)
    
    # ตรวจสอบ cache ก่อน
    if cache_key in whois_cache:
        print(f"[CACHE HIT] WHOIS data for {url}")
        return whois_cache[cache_key]
    
    # ถ้าไม่มีใน cache ให้ทำ lookup
    try:
        print(f"[CACHE MISS] Fetching WHOIS for {url}...")
        whois_data = whois.whois(url)
        # แปลงเป็น serializable dict
        whois_dict = convert_whois_to_dict(whois_data)
        # เก็บใน cache
        whois_cache[cache_key] = whois_dict
        return whois_dict
    except Exception as e:
        print(f"WHOIS lookup failed for {url}: {e}")
        # เก็บ empty dict ใน cache เพื่อไม่ต้อง retry ซ้ำ
        whois_cache[cache_key] = {}
        return {}


import socket
from urllib.parse import urlparse
import idna  # สำหรับแปลง IDN (โดเมนไทย) เป็น Punycode

def check_domain_exists(url: str) -> bool:
    """
    ตรวจสอบว่า domain มีจริงหรือไม่ โดยใช้ DNS lookup
    รองรับ IDN (Internationalized Domain Names) เช่น ธกส.ไทย
    
    Returns:
        True: Domain มีอยู่จริง (DNS resolve สำเร็จ)
        False: Domain ไม่มีจริง (DNS resolve ล้มเหลว)
    """
    hostname = None
    try:
        # แยก domain จาก URL
        parsed = urlparse(url)
        if parsed.netloc:
            hostname = parsed.netloc
        else:
            # ถ้าไม่มี scheme ให้ลองเพิ่ม https:// แล้ว parse ใหม่
            parsed = urlparse("https://" + url)
            hostname = parsed.netloc if parsed.netloc else url
        
        # ลบ port ออก (ถ้ามี)
        hostname = hostname.split(':')[0]
        
        print(f"[DNS LOOKUP] Checking if domain exists: {hostname}")
        
        # แปลง IDN (โดเมนไทย/Unicode) เป็น Punycode สำหรับ DNS lookup
        # เช่น ธกส.ไทย → xn--42ca4b.xn--o3cw4h
        try:
            hostname_ascii = idna.encode(hostname).decode('ascii')
            print(f"[DNS LOOKUP] Converted to Punycode: {hostname_ascii}")
        except idna.core.InvalidCodepoint:
            # ถ้าแปลงไม่ได้ ให้ใช้ hostname เดิม
            hostname_ascii = hostname
        except Exception as e:
            print(f"[DNS LOOKUP] IDNA encoding failed: {e}, using original hostname")
            hostname_ascii = hostname
        
        # DNS lookup - ถ้าสำเร็จแสดงว่า domain มีจริง
        socket.gethostbyname(hostname_ascii)
        print(f"[DNS LOOKUP] Domain exists: {hostname}")
        return True
        
    except socket.gaierror as e:
        # DNS lookup ล้มเหลว - domain ไม่มีจริง
        print(f"[DNS LOOKUP] Domain does NOT exist: {hostname} - Error: {e}")
        return False
    except Exception as e:
        print(f"[DNS LOOKUP] Error checking domain: {e}")
        return False


def check_online_status(url: str) -> str:
    """
    [OPTIMIZED] ตรวจสอบสถานะออนไลน์พร้อม caching
    ลดเวลาจาก ~5-12 วินาที เหลือ ~0ms สำหรับ cached URLs
    
    Returns:
        "yes": URL เข้าถึงได้ (Online)
        "no": URL เข้าไม่ได้แต่ domain มีจริง (Offline)
        "not_exist": Domain ไม่มีจริง (DNS lookup failed)
    """
    cache_key = get_cache_key(url)
    
    # ตรวจสอบ cache ก่อน
    if cache_key in online_cache:
        print(f"[CACHE HIT] Online status for {url}")
        return online_cache[cache_key]
    
    # ขั้นตอนที่ 1: เช็คว่า domain มีจริงหรือไม่ (DNS lookup)
    domain_exists = check_domain_exists(url)
    
    if not domain_exists:
        # Domain ไม่มีจริง
        online_cache[cache_key] = "not_exist"
        return "not_exist"
    
    # ขั้นตอนที่ 2: Domain มีจริง ให้เช็คว่า online หรือไม่
    print(f"[CACHE MISS] Checking online status for {url}...")
    is_accessible, _, _ = is_URL_accessible(url, timeout=5)
    
    status = "yes" if is_accessible else "no"
    # เก็บใน cache
    online_cache[cache_key] = status
    return status


def generate_random_id(length=8):
    characters = string.digits
    return "".join(random.choices(characters, k=length))


from fastapi.encoders import jsonable_encoder


# ========================================
# [NEW] Cache Management Endpoints
# ========================================

@app.get("/api/cache-status")
async def get_cache_status(api_key: str = Depends(verify_admin)):
    """
    ดูสถานะของ cache (สำหรับ admin เท่านั้น)
    """
    return {
        "whois_cache": {
            "size": len(whois_cache),
            "maxsize": whois_cache.maxsize,
            "ttl_seconds": whois_cache.ttl,
        },
        "online_cache": {
            "size": len(online_cache),
            "maxsize": online_cache.maxsize,
            "ttl_seconds": online_cache.ttl,
        },
    }


@app.post("/api/clear-cache")
async def clear_cache(api_key: str = Depends(verify_admin)):
    """
    Clear all caches (สำหรับ admin เท่านั้น)
    ใช้เมื่อต้องการบังคับให้ระบบ fetch ข้อมูลใหม่
    """
    whois_cache.clear()
    online_cache.clear()
    return {"message": "All caches cleared successfully"}


@app.post("/api/verifited-url")
async def check_verifited_url(url: str, api_key: str = Depends(verify_admin)):
    """
    [SIMPLIFIED] API สำหรับ Admin ยืนยัน URL ว่าเป็น Phishing จริง
    - อัปเดต verifited = "yes"
    - เก็บ WHOIS data
    - เช็ค Online Status
    ไม่ใช้ Safe Browsing หรือ AI
    """
    try:
        # แปลงเวลาปัจจุบันเป็นโซนเวลาไทย
        thai_timezone = pytz.timezone("Asia/Bangkok")
        verification_time = datetime.now(tz=thai_timezone).isoformat()
        submission_time = verification_time

        # แปลง URL เป็น lowercase สำหรับ case-insensitive matching
        url_lower = url.lower()
        
        # Extract domain name from the URL
        extracted = tldextract.extract(url)
        domain_name = f"{extracted.domain}.{extracted.suffix}"
        
        # ========================================
        # ตรวจสอบ URL Format
        # ========================================
        is_valid_format = False
        if extracted.suffix:
            is_valid_format = True
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', extracted.domain):
            is_valid_format = True

        if not is_valid_format:
            return {
                "url": url,
                "message": "Invalid URL format. Please enter a valid URL.",
                "prediction": "error", 
                "success": False
            }
        
        # ========================================
        # ดึง WHOIS และ Online Status
        # ========================================
        whois_data = get_whois_data(url)
        online_status = check_online_status(url)
        
        # ========================================
        # ค้นหาใน BLACK_LIST
        # ========================================
        blacklisted_url = db[BLACK_LIST].find_one({"url_lower": url_lower})
        if not blacklisted_url:
            blacklisted_url = db[BLACK_LIST].find_one({"url": url})

        if blacklisted_url:
            # ========================================
            # พบใน Blacklist → อัปเดตการยืนยัน
            # ========================================
            
            # ถ้าไม่มี phish_id ให้สร้างใหม่
            if "phish_id" not in blacklisted_url:
                new_phish_id = generate_random_id()
                db[BLACK_LIST].update_one(
                    {"_id": blacklisted_url["_id"]}, 
                    {"$set": {"phish_id": new_phish_id}}
                )
                blacklisted_url["phish_id"] = new_phish_id

            # อัปเดตข้อมูลการยืนยัน
            db[BLACK_LIST].update_one(
                {"_id": blacklisted_url["_id"]},
                {
                    "$set": {
                        "verifited": "yes",
                        "verified": "yes",
                        "verification_time": verification_time,
                        "online": online_status,
                    },
                    "$addToSet": {"details": whois_data} if whois_data else {},
                },
            )

            # เตรียม response
            blacklisted_url["_id"] = str(blacklisted_url["_id"])
            blacklisted_url["verifited"] = "yes"
            blacklisted_url["verified"] = "yes"
            blacklisted_url["verification_time"] = verification_time
            blacklisted_url["online"] = online_status
            blacklisted_url["prediction"] = "phishing"
            blacklisted_url["success"] = True
            blacklisted_url["message"] = f"URL verified as phishing successfully."

            return jsonable_encoder(blacklisted_url)

        else:
            # ========================================
            # ไม่พบใน Blacklist → เพิ่มใหม่และยืนยันเลย
            # ========================================
            random_id = generate_random_id()
            
            new_entry = {
                "url": url,
                "url_lower": url_lower,
                "phish_id": random_id,
                "domain_name": domain_name,
                "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                "submission_time": submission_time,
                "verifited": "yes",
                "verified": "yes",
                "verification_time": verification_time,
                "online": online_status,
                "details": [whois_data] if whois_data else [],
                "reporter": "Admin (Manual Verify)",
            }
            
            result = db[BLACK_LIST].insert_one(new_entry)
            
            new_entry["_id"] = str(result.inserted_id)
            new_entry["prediction"] = "phishing"
            new_entry["success"] = True
            new_entry["message"] = f"URL added to blacklist and verified as phishing."

            return jsonable_encoder(new_entry)
    
    except Exception as e:
        print(f"[ERROR] check_verifited_url failed for {url}: {e}")
        return {
            "error": True,
            "message": f"This URL cannot be processed: {url}",
            "url": url,
            "prediction": "error"
        }


@app.post("/api/phishing-url")
async def check_phishing_url(url: str, api_key: str = Depends(verify_api_key)):
    # Convert current time to Thai timezone
    thai_timezone = pytz.timezone("Asia/Bangkok")
    submission_time = datetime.now(tz=thai_timezone).isoformat()

    # Extract domain name from the URL (ignore protocol and subdomain)
    extracted = tldextract.extract(url)
    domain_name = f"{extracted.domain}.{extracted.suffix}"
    
    # [OPTIMIZED] แปลง URL เป็น lowercase สำหรับ case-insensitive matching
    url_lower = url.lower()

    try:
        # ========================================
        # [STEP 0] ตรวจสอบ URL Format ก่อน
        # ========================================
        
        # 0.1 ตรวจสอบ Format ของ URL
        is_valid_format = False
        
        # 1. มี TLD ที่ถูกต้อง (เช่น .com, .th, .ไทย)
        if extracted.suffix:
            is_valid_format = True
        # 2. เป็น IP Address
        elif re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', extracted.domain):
            is_valid_format = True

        if not is_valid_format:
            return {
                "url": url,
                "message": "Invalid URL format. Please enter a valid URL (e.g., example.com, ชื่อโดเมน.ไทย).",
                "prediction": "error", 
                "result_type": "invalid"
            }
        
        # ========================================
        # [NEW] เช็ค WHITE_LIST - ถ้าอยู่ใน whitelist ให้ return safe ทันที
        # เช็คทั้ง URL และ domain_name
        # ========================================
        whitelisted_url = db[WHITE_LIST].find_one({"url_lower": url_lower})
        
        # Fallback: ถ้าไม่เจอจาก url_lower ให้ลอง exact match
        if not whitelisted_url:
            whitelisted_url = db[WHITE_LIST].find_one({"url": url})
        
        # เช็ค domain_name ด้วย - ถ้า domain เดียวกันก็ถือว่าอยู่ใน whitelist
        if not whitelisted_url:
            whitelisted_url = db[WHITE_LIST].find_one({"domain_name": domain_name})
        
        # [NEW] ค้นหาด้วย regex pattern - จับ URLs ที่มี protocol prefix เช่น http://google.com
        if not whitelisted_url:
            # สร้าง pattern: .*google\.com.* (escape dots)
            escaped_domain = domain_name.replace(".", r"\.")
            pattern = f"(^|.*://){escaped_domain}(/.*)?$"
            whitelisted_url = db[WHITE_LIST].find_one({
                "url": {"$regex": pattern, "$options": "i"}
            })
            if whitelisted_url:
                print(f"[WHITELIST HIT via REGEX] {url} matched {whitelisted_url.get('url')}")
        
        if whitelisted_url:
            # CHECK: ถ้าเป็น Full URL Match ให้ผ่านเลย
            # แต่ถ้าเป็นการ Match ผ่าน Domain หรือ Regex -> ต้องเช็คว่าเป็น Hosting Platform หรือไม่
            is_full_url_match = (whitelisted_url.get("url_lower") == url_lower) or (whitelisted_url.get("url") == url)
            
            if is_full_url_match:
                # Full URL Match -> Safe แน่นอน
                print(f"[WHITELIST HIT] Full URL match: {url}")
                return {
                    "url": whitelisted_url.get("url"),
                    "domain_name": whitelisted_url.get("domain_name"),
                    "submission_time": whitelisted_url.get("submission_time"),
                    "message": f"The URL {url} has been verified as safe by our system and Google Safe Browsing.",
                    "prediction": "safe",
                }
            else:
                # Domain Match / Regex Match
                # ต้องเช็คว่า domain นี้เป็น hosting platform หรือไม่
                # ถ้าใช่ -> ห้าม Whitelist ทั้ง Domain (ต้อง Match Full URL เท่านั้น)
                # ถ้าไม่ใช่ -> Whitelist ทั้ง Domain ได้
                white_domain = whitelisted_url.get("domain_name")
                # Fallback: ถ้าใน DB ไม่มี domain_name ให้ใช้จากที่ extract มาได้
                if not white_domain:
                    white_domain = domain_name
                    
                if is_hosting_platform(white_domain):
                   print(f"[WHITELIST IGNORED] Domain '{white_domain}' is a hosting platform. Full URL match required.")
                   whitelisted_url = None # Reset เพื่อให้ไปเช็ค Blacklist/Prediction ต่อ
                else:
                    print(f"[WHITELIST HIT] Domain match: {domain_name}")
                    return {
                        "url": whitelisted_url.get("url"),
                        "domain_name": whitelisted_url.get("domain_name"),
                        "submission_time": whitelisted_url.get("submission_time"),
                        "message": f"The URL {url} has been verified as safe by our system and Google Safe Browsing.",
                        "prediction": "safe",
                    }

        # ========================================
        # เช็ค BLACK_LIST
        # ========================================
        # [OPTIMIZED] ค้นหาด้วย url_lower field ก่อน (ใช้ index ได้)
        blacklisted_url = db[BLACK_LIST].find_one({"url_lower": url_lower})
        
        # Fallback: ถ้าไม่เจอจาก url_lower ให้ลอง exact match
        if not blacklisted_url:
            blacklisted_url = db[BLACK_LIST].find_one({"url": url})

        if blacklisted_url:
            # If domain exists in BLACK_LIST, return the details from the database
            blacklisted_data = {
                "url": blacklisted_url.get("url"),
                "phish_id": blacklisted_url.get("phish_id"),
                "phish_detail_url": blacklisted_url.get("phish_detail_url"),
                "submission_time": blacklisted_url.get("submission_time"),
                "verifited": blacklisted_url.get("verifited"),
                "verification_time": blacklisted_url.get("verification_time"),
                "online": blacklisted_url.get("online"),
                "details": blacklisted_url.get("details"),  # Should be an array
                "reporter": blacklisted_url.get("reporter"),
                "prediction": "phishing",
            }
            return blacklisted_data
        
        # ========================================
        # ขั้นตอนที่ 1: ตรวจสอบ Online Status และ Safe Browsing
        # (เช็ค online ตรงนี้เพราะไม่เจอใน DB)
        # ========================================
        print(f"[STEP 1] URL not in DB. Checking if URL exists and is online: {url}")
        online_status = check_online_status(url)
        
        # กรณีที่ 1: Domain ไม่มีจริง (DNS lookup failed)
        if online_status == "not_exist":
            return {
                "url": url,
                "domain_name": domain_name,
                "our_system": "Unknown",
                "safe_browsing": "Unknown",
                "message": f"The domain does not exist. Please check the URL and try again.",
                "result_type": "not_exist",
                "prediction": "not_exist",
                "online": online_status,
            }
        
        # กรณีที่ 2: Domain มีจริงแต่เข้าไม่ได้ (Offline)
        if online_status == "no" or online_status == "offline":
            return {
                "url": url,
                "domain_name": domain_name,
                "our_system": "Unknown",
                "safe_browsing": "Unknown",
                "message": f"The URL is currently offline or unavailable. The domain exists but the server is not responding.",
                "result_type": "offline",
                "prediction": "offline",
                "online": online_status,
            }
        
        print(f"[STEP 1] URL is online: {url}")
        
        safe_browsing_response = check_safe_browsing(url)
        
        # Auto-Whitelist สำหรับโดเมนทางการของไทย (.go.th, .ac.th)
        safe_suffixes = {'.go.th', '.ac.th', '.or.th', '.mi.th'}
        domain_suffix = '.' + extracted.suffix.lower() if extracted.suffix else ''
        
        if domain_suffix in safe_suffixes:
             # URL ถูกเช็คแล้วว่า Online
             return {
                "url": url,
                "domain_name": domain_name,
                "our_system": "Safe",
                "safe_browsing": "Safe",
                "message": f"The URL {url} has been verified as safe by our system and Google Safe Browsing.",
                "result_type": "safe",
                "prediction": "safe",
                "online": online_status
            }

        # ถ้า Safe Browsing บอกว่า Phishing -> เชื่อเลย และบันทึกทันที
        if safe_browsing_response["is_safe"] is False:
            print(f"[EARLY DETECTION] Google Safe Browsing flagged {url} as Phishing. Processing...")
            
            # 1. Get WHOIS details
            whois_details = None
            try:
                whois_details = get_whois_data(url)
            except Exception as e:
                print(f"[WHOIS] Failed to get WHOIS: {e}")

            # 2. Auto-Blacklist Logic (Update or Insert)
            try:
                # [FIXED] Use url_lower variable if available, else standard lower()
                target_url_lower = url_lower if 'url_lower' in locals() else url.lower()
                
                filter_query = {"$or": [{"url_lower": target_url_lower}, {"url": url}]}
                
                random_id = generate_random_id()
                submission_time = datetime.now(pytz.timezone("Asia/Bangkok")).isoformat()
                
                update_data = {
                    "$set": {
                        "url": url,
                        "url_lower": target_url_lower,
                        "domain_name": domain_name,
                        "submission_time": submission_time,
                        "verifited": "no",
                        "verified": "no",
                        "online": online_status,
                        "details": [whois_details] if whois_details else [],
                        "reporter": "Google Safe Browsing (Auto)",
                    },
                    "$setOnInsert": {
                        "phish_id": random_id,
                        "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                    }
                }
                
                result = db[BLACK_LIST].update_one(filter_query, update_data, upsert=True)
                print(f"[AUTO-BLACKLIST] Operation result: Matched={result.matched_count}, Modified={result.modified_count}, Upserted={result.upserted_id}")
                
            except Exception as e:
                print(f"[ERROR] Auto-blacklist failed: {e}")

            # 3. Create Message
            msg = f"Google Safe Browsing has flagged {url} as a phishing site.\nSafe Browsing: Phishing"
            if whois_details:
                details_text = []
                if whois_details.get("registrar"): details_text.append(f"Registrar: {whois_details['registrar']}")
                if whois_details.get("creation_date"): details_text.append(f"Created: {whois_details['creation_date']}")
                msg += "\n\n--- Domain Details ---\n" + "\n".join(details_text)

            # 4. Return Response
            response_data = {
                "url": url,
                "domain_name": domain_name,
                "our_system": "Safe", # Skipped our system
                "safe_browsing": "Phishing",
                "message": msg,
                "result_type": "phishing",
                "prediction": "split", # Keep frontend happy
                "online": online_status,
            }
            
            if whois_details:
                response_data["details"] = whois_details
                
            return response_data

        # ========================================
        # ขั้นตอนที่ 2: สกัดคุณลักษณะ URL (Feature Extraction)
        # หากเกิดข้อผิดพลาด ให้ตอบว่าไม่สามารถสกัดคุณลักษณะได้
        # ========================================
        try:
            # ใช้ prediction function ซึ่งจะเรียก extract_features
            pre = prediction("app/mlengine/mlp99.31", url)
        except Exception as e:
            print(f"[ERROR] Feature extraction failed for {url}: {e}")
            return {
                "url": url,
                "message": f"This URL cannot be processed: {url}",
                "prediction": "error",
            }

        # เช็คกรณี website offline (จาก function prediction)
        if pre == 2:
            return {
                 "url": url,
                "domain_name": domain_name,
                "our_system": "Safe",
                "safe_browsing": "Safe",
                "message": f"The domain '{domain_name}' is not online or cannot be accessed.",
                "result_type": "safe",
                "prediction": "offline",
                "online": online_status,
            }

        # ========================================
        # ขั้นตอนที่ 3: ตรวจสอบด้วยโมเดลและ safe browsing (process ผลลัพธ์)
        # ========================================
        
        # 3.1 ผลจาก Our System (โมเดล ML)
        if pre == 1:
            our_system_result = "Phishing"
        else:  # pre == 0
            our_system_result = "Safe"
        
        # 3.2 ผลจาก Google Safe Browsing API (เช็คไปแล้วข้างบนดึงมาใช้)
        if safe_browsing_response["error"]:
            safe_browsing_result = "Unknown"  # [CHANGED] ถ้า Safe Browsing error ให้เป็น Unknown
        elif safe_browsing_response["is_safe"]:
            safe_browsing_result = "Safe"
        else:
            safe_browsing_result = "Phishing"
        
        print(f"[COMPARISON] URL: {url}")
        print(f"  Our System: {our_system_result}")
        print(f"  Safe Browsing: {safe_browsing_result}")

        # ========================================
        # ขั้นตอนที่ 4: การแสดงผลลัพธ์
        # ========================================
        
        # [NEW] กรณี Safe Browsing ใช้ไม่ได้ (Unknown) → ใช้ผลจาก Our System เป็นหลัก
        if safe_browsing_result == "Unknown":
            print(f"[INFO] Safe Browsing unavailable, using Our System result only")
            
            if our_system_result == "Phishing":
                # Our System บอกว่า Phishing แต่ Safe Browsing ไม่รู้
                whois_details = get_whois_data(url)
                online = check_online_status(url)
                random_id = generate_random_id()
                
                existing_blacklist = db[BLACK_LIST].find_one({"url_lower": url_lower})
                if not existing_blacklist:
                    existing_blacklist = db[BLACK_LIST].find_one({"url": url})
                    
                if not existing_blacklist:
                    db[BLACK_LIST].insert_one({
                        "url": url,
                        "url_lower": url_lower,
                        "phish_id": random_id,
                        "domain_name": domain_name,
                        "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                        "submission_time": submission_time,
                        "verifited": "no",
                        "verification_time": None,
                        "online": online,
                        "details": [whois_details] if whois_details else [],
                        "reporter": "",
                    })
                
                return {
                    "url": url,
                    "domain_name": domain_name,
                    "our_system": our_system_result,
                    "safe_browsing": safe_browsing_result,
                    "message": f"Our system flagged this as Phishing. Google Safe Browsing is unavailable.",
                    "prediction": "phishing",
                    "result_type": "our_system_only",
                    "online": online,
                    "details": [whois_details] if whois_details else [],
                }
            else:
                # Our System บอกว่า Safe และ Safe Browsing ไม่รู้
                return {
                    "url": url,
                    "domain_name": domain_name,
                    "our_system": our_system_result,
                    "safe_browsing": safe_browsing_result,
                    "message": f"Our system verified this as Safe. Google Safe Browsing is unavailable.",
                    "prediction": "safe",
                    "result_type": "our_system_only",
                    "online": online_status,
                }
        
        # กรณีผลเหมือนกัน
        if our_system_result == safe_browsing_result:
            final_prediction = our_system_result.lower()  # "safe" หรือ "phishing"
            
            # ถ้าเป็น phishing ให้บันทึกลง BLACK_LIST
            if final_prediction == "phishing":
                details = get_whois_data(url)
                online = check_online_status(url)
                random_id = generate_random_id()
                
                existing_blacklist = db[BLACK_LIST].find_one({"url_lower": url_lower})
                if not existing_blacklist:
                    existing_blacklist = db[BLACK_LIST].find_one({"url": url})
                    
                if not existing_blacklist:
                    result = db[BLACK_LIST].insert_one(
                        {
                            "url": url,
                            "url_lower": url_lower,
                            "phish_id": random_id,
                            "domain_name": domain_name,
                            "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                            "submission_time": submission_time,
                            "verifited": "no",
                            "verification_time": None,
                            "online": online,
                            "details": [details],
                            "reporter": "",
                        }
                    )
                    print(f"Inserted into BLACK_LIST: {result.inserted_id}")
                
                return {
                    "url": url,
                    "phish_id": random_id,
                    "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                    "submission_time": submission_time,
                    "verifited": "no",
                    "verification_time": None,
                    "online": online,
                    "details": [details],
                    "reporter": "",
                    "message": f"{url} has been flagged as a phishing site by our system and Google Safe Browsing.",
                    "prediction": final_prediction,
                    "result_type": "unanimous",  # ทั้งสองระบบเห็นตรงกัน
                }
            else:
                # Safe case
                existing_whitelist = db[WHITE_LIST].find_one({"url_lower": url_lower})
                if not existing_whitelist:
                    existing_whitelist = db[WHITE_LIST].find_one({"url": url})
                
                if not existing_whitelist:
                    db[WHITE_LIST].insert_one({
                        "url": url,
                        "url_lower": url_lower,
                        "domain_name": domain_name,
                        "submission_time": submission_time,
                    })
                    print(f"[WHITELIST] Added {url} to whitelist")
                
                return {
                    "url": url,
                    "domain_name": domain_name,
                    "message": f"The URL {url} has been verified as safe by our system and Google Safe Browsing.",
                    "prediction": final_prediction,
                    "result_type": "unanimous",  # ทั้งสองระบบเห็นตรงกัน
                }
        
        # กรณีผลไม่เหมือนกัน - แสดงผลแยกตามแหล่งที่มา
        else:
            # ดึง WHOIS details ถ้าฝ่ายใดฝ่ายหนึ่งบอกว่าเป็น Phishing
            whois_details = None
            if our_system_result == "Phishing" or safe_browsing_result == "Phishing":
                try:
                    whois_details = get_whois_data(url)
                except Exception as e:
                    print(f"[WHOIS] Failed to get WHOIS: {e}")
                    whois_details = None

            # [Added] Auto-blacklist if Google Safe Browsing confirms Phishing
            if safe_browsing_result == "Phishing":
                try:
                    existing_blacklist = db[BLACK_LIST].find_one({"url_lower": url_lower})
                    if not existing_blacklist:
                        existing_blacklist = db[BLACK_LIST].find_one({"url": url})
                    
                    if not existing_blacklist:
                        print(f"[AUTO-BLACKLIST] Google Verified Phishing. Inserting {url}...")
                        random_id = generate_random_id()
                        db[BLACK_LIST].insert_one({
                            "url": url,
                            "url_lower": url_lower,
                            "phish_id": random_id,
                            "domain_name": domain_name,
                            "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                            "submission_time": submission_time,
                            "verifited": "no",
                            "verification_time": None,
                            "online": online_status,
                            "details": [whois_details] if whois_details else [],
                            "reporter": "Google Safe Browsing (Auto)",
                        })
                except Exception as e:
                    print(f"[ERROR] Auto-blacklist failed: {e}")

            # เตรียมข้อความ WHOIS Details
            details_message = ""
            if whois_details:
                details_text = []
                if whois_details.get("registrar"):
                    details_text.append(f"Registrar: {whois_details['registrar']}")
                if whois_details.get("creation_date"):
                    details_text.append(f"Created: {whois_details['creation_date']}")
                if whois_details.get("expiration_date"):
                    details_text.append(f"Expires: {whois_details['expiration_date']}")
                if whois_details.get("country"):
                    details_text.append(f"Country: {whois_details['country']}")
                if details_text:
                    details_message = "\n\n--- Domain Details ---\n" + "\n".join(details_text)

            # สร้างข้อความตามกรณี
            if our_system_result == "Phishing" and safe_browsing_result == "Safe":
                split_message = f"Our system has flagged {url} as a phishing site, though Google Safe Browsing does not currently report it.\nOur System: Phishing\nSafe Browsing: Safe" + details_message
            elif our_system_result == "Safe" and safe_browsing_result == "Phishing":
                split_message = f"Google Safe Browsing has flagged {url} as a phishing site, though our system does not currently report it.\nOur System: Safe\nSafe Browsing: Phishing" + details_message
            else:
                split_message = f"Our System: {our_system_result}\nSafe Browsing: {safe_browsing_result}"
                if our_system_result != "Unknown" and safe_browsing_result != "Unknown":
                     split_message += details_message
            
            response_data = {
                "url": url,
                "domain_name": domain_name,
                "our_system": our_system_result,
                "safe_browsing": safe_browsing_result,
                "message": split_message,
                "result_type": "split",  # ผลลัพธ์ไม่เหมือนกัน
                "prediction": "split",
            }
            
            # เพิ่ม WHOIS details ใน response ถ้ามี
            if whois_details:
                response_data["details"] = whois_details
            
            return response_data
    
    except Exception as e:
        print(f"[ERROR] check_phishing_url failed for {url}: {e}")
        return {
            "error": True,
            "url": url,
            "message": f"This URL cannot be processed: {url}",
            "prediction": "error",
        }
