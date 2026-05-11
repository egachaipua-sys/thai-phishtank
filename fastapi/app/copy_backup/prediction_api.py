from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from pymongo import MongoClient
import sys
import os
import re

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


config = configparser.ConfigParser()
config.read("config_app.ini")

MONGO_DETAILS = config["DATABASE"]["MONGO_DETAILS"]
DATABASE_NAME = config["DATABASE"]["DATABASE_NAME"]
USER_COLLECTION = config["DATABASE"]["USER_COLLECTION"]
BLACK_LIST = config["DATABASE"]["BLACK_LIST"]
API_KEY = config["API_KEY"]["API_KEY"]
DOMAIN_NAME = config["DOMAIN_NAME"]["DOMAIN_NAME"]

app = FastAPI()

client = MongoClient(MONGO_DETAILS)
db = client[DATABASE_NAME]


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


def get_whois_data(url: str):

    try:
        whois_data = whois.whois(url)
        return whois_data
    except Exception as e:
        print(f"WHOIS lookup failed for {url}: {e}")
        return {}


def check_online_status(url: str):
    is_accessible, _, _ = is_URL_accessible(url, timeout=5) # อาจปรับ timeout ตามความเหมาะสม
    
    if is_accessible:
        return "yes"
    else:
        return "no"


def generate_random_id(length=8):
    characters = string.digits
    return "".join(random.choices(characters, k=length))


from fastapi.encoders import jsonable_encoder


@app.post("/api/verifited-url")
async def check_verifited_url(url: str, api_key: str = Depends(verify_admin)):
    # แปลงเวลาปัจจุบันเป็นโซนเวลาไทย
    thai_timezone = pytz.timezone("Asia/Bangkok")
    # submission_time = datetime.now(tz=thai_timezone).isoformat()
    verification_time = datetime.now(tz=thai_timezone).isoformat()

    # ดึงชื่อโดเมนจาก URL
    # extracted = tldextract.extract(url)
    # domain_name = f"{extracted.domain}.{extracted.suffix}"

    # ตรวจสอบว่ามีอยู่ใน BLACK_LIST หรือไม่
    blacklisted_url = db[BLACK_LIST].find_one(
        {"url": {"$regex": f"^{url}$", "$options": "i"}}
    )

    if blacklisted_url:
        # ถ้าไม่มี phish_id ให้สร้างใหม่
        if "phish_id" not in blacklisted_url:
            new_phish_id = generate_random_id()
            db[BLACK_LIST].update_one(
                {"_id": blacklisted_url["_id"]}, {"$set": {"phish_id": new_phish_id}}
            )
            blacklisted_url["phish_id"] = new_phish_id  # อัปเดตค่าที่จะ return ด้วย

        # อัปเดตข้อมูลเพิ่มเติม
        db[BLACK_LIST].update_one(
            {"url": {"$regex": f"^{url}$", "$options": "i"}},
            {
                "$set": {
                    "verifited": "yes",
                    "verification_time": verification_time,
                    "online": check_online_status(url),
                },
                "$addToSet": {"details": get_whois_data(url)},
            },
        )

        # แปลง `_id` เป็น string ก่อนส่งออก
        blacklisted_url["_id"] = str(blacklisted_url["_id"])
        blacklisted_url["verifited"] = "yes"
        blacklisted_url["verification_time"] = verification_time
        blacklisted_url["online"] = check_online_status(url)

        if "prediction" not in blacklisted_url:
            blacklisted_url["prediction"] = "unknown"

        return jsonable_encoder(blacklisted_url)

    # ถ้าไม่พบ URL ใน blacklist ให้ส่งข้อความว่าไม่พบ
    return {"message": "URL not found in blacklist."}


@app.post("/api/phishing-url")
async def check_phishing_url(url: str, api_key: str = Depends(verify_api_key)):
    # Convert current time to Thai timezone
    thai_timezone = pytz.timezone("Asia/Bangkok")
    submission_time = datetime.now(tz=thai_timezone).isoformat()

    # Extract domain name from the URL (ignore protocol and subdomain)
    extracted = tldextract.extract(url)
    domain_name = f"{extracted.domain}.{extracted.suffix}"

    # Step 1: ตรวจสอบว่า URL แบบเต็มอยู่ใน blacklist หรือไม่
    blacklisted_url = db[BLACK_LIST].find_one({"url": url})
    # escaped_domain = re.escape(domain_name)
    # # Step 2: ถ้าไม่เจอ URL ตรงเป๊ะ → ตรวจสอบด้วย domain_name
    # if not blacklisted_url:
    #     regex_pattern = f"(?:^|://)(?:[a-zA-Z0-9-]+\\.)*?{escaped_domain}(?:$|[/?:#])"
    #     blacklisted_url = db[BLACK_LIST].find_one(
    #         {"url": {"$regex": f"{regex_pattern }", "$options": "i"}}
    #     )

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

    # Perform URL prediction
    pre = prediction("app/mlengine/mlp99.31", url)
    # print(f"Prediction for {url}: {pre}")

    if pre == 1:  # Phishing case
        prediction_result = "phishing"
        details = get_whois_data(url)
        online = check_online_status(url)
        random_id = generate_random_id()

        # Save to BLACK_LIST only if it doesn't already exist
        existing_blacklist = db[BLACK_LIST].find_one(
            {"url": url}
        )
        if not existing_blacklist:
            # print(f"Saving to BLACK_LIST: {url}")
            result = db[BLACK_LIST].insert_one(
                {
                    "url": url,
                    "phish_id": random_id,
                    "domain_name": domain_name,  # Optional, can be removed if not needed
                    "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
                    "submission_time": submission_time,
                    "verifited": "no",
                    "verification_time": None,
                    "online": online,
                    "details": [details],  # Save details as an array
                    "reporter": "",
                }
            )
            print(f"Inserted into BLACK_LIST: {result.inserted_id}")

        # Return the full details for the phishing URL
        return {
            "url": url,
            "phish_id": random_id,
            "phish_detail_url": f"{DOMAIN_NAME}/view/detail/{random_id}",
            "submission_time": submission_time,
            "verifited": "no",
            "verification_time": None,
            "online": online,
            "details": [details],  # Save details as an array
            "reporter": "",
            "prediction": prediction_result,
        }

    elif pre == 2:  # Website is not online
        prediction_result = "offline"
        return {
            "url": url,
            "message": f"The domain '{domain_name}' is not online.",
            "prediction": "offline",
        }

    else:  # Safe case
        prediction_result = "safe"

        # Return only the URL and prediction without saving to WHITE_LIST
        return {
            "url": url,
            "message": f"The domain '{domain_name}' is considered safe.",
            "prediction": prediction_result,
        }
