from flask import Blueprint, render_template, abort, session
from app.models.phish_model import PhishModel
from datetime import datetime
import json

import os

view_blueprint = Blueprint("view", __name__)

# --- Helper functions for Map Bubbles ---
COUNTRIES_DATA = None

def load_countries_data():
    global COUNTRIES_DATA
    if COUNTRIES_DATA is None:
        # หา path ของไฟล์ json (อยู่ที่ flaskweb/app/countries_data.json)
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            with open(os.path.join(root_path, 'countries_data.json'), 'r', encoding='utf-8') as f:
                COUNTRIES_DATA = json.load(f)
        except Exception as e:
            print(f"Error loading countries data: {e}")
            COUNTRIES_DATA = []
    return COUNTRIES_DATA

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

def get_country_code(country_name):
    """แปลง Country Name เป็น ISO Country Code"""
    if not country_name:
        return None
    
    name_clean = country_name.strip().lower()
    
    # ถ้าเป็น Code 2 ตัวอยู่แล้ว (เช่น TH, US) ให้ใช้ได้เลย
    if len(name_clean) == 2 and name_clean.isalpha():
        return name_clean.upper()
        
    # ค้นหาจาก Mapping
    return COUNTRY_NAME_TO_CODE.get(name_clean)

@view_blueprint.route("/", methods=["GET"])
def index():
    lang = session.get("lang", "en")
    
    # 1. โหลดข้อมูลพิกัดประเทศ
    countries_data_json = load_countries_data()
    formatted_data = {
        c.get("country_code"): {
            "name": c.get("country_name", "Unknown"),
            "latlng": [c.get("latitude", 0), c.get("longitude", 0)],
        }
        for c in countries_data_json if "country_code" in c
    }

    # 2. ดึงสถิติต่างๆ
    active = PhishModel.find_active()
    today = PhishModel.find_today()
    total = PhishModel.find_total()
    
    # 3. เตรียมข้อมูล Bubbles สำหรับแผนที่
    raw_countries = PhishModel.find_country()
    country_count = {}

    for c in raw_countries:
        country_raw = c.get("country")
        if not country_raw: continue
        
        country_code = get_country_code(str(country_raw))
        if not country_code: continue

        country_count[country_code] = country_count.get(country_code, 0) + c.get("count", 1)

    MIN_RADIUS = 3
    MAX_RADIUS = 20
    bubbles_data = []

    for code, count in country_count.items():
        if code in formatted_data:
            bubbles_data.append({
                "name": formatted_data[code].get("name", code),
                "radius": max(MIN_RADIUS, min(count * 5, MAX_RADIUS)),
                "fillKey": "active",
                "latitude": formatted_data[code].get("latlng", [0, 0])[0],
                "longitude": formatted_data[code].get("latlng", [0, 0])[1],
                "count": count,
            })

    return render_template(
        "view/index.html",
        lang=lang,
        active=active,
        today=today,
        total=total,
        bubbles_data=bubbles_data
    )


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