"""
MongoDB Index Creation Script
สคริปต์สำหรับสร้าง Index ใน MongoDB เพื่อเพิ่มประสิทธิภาพการ query

การใช้งาน:
    python scripts/create_indexes.py
"""

from pymongo import MongoClient, ASCENDING
import configparser
import sys
import os

# เพิ่ม path ของ app
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# อ่าน config
config = configparser.ConfigParser()
config.read(os.path.join(parent_dir, "config_app.ini"))

MONGO_DETAILS = config["DATABASE"]["MONGO_DETAILS"]
DATABASE_NAME = config["DATABASE"]["DATABASE_NAME"]
USER_COLLECTION = config["DATABASE"]["USER_COLLECTION"]
BLACK_LIST = config["DATABASE"]["BLACK_LIST"]


def create_indexes():
    """สร้าง indexes ทั้งหมดที่จำเป็น"""
    
    print("กำลังเชื่อมต่อ MongoDB...")
    client = MongoClient(MONGO_DETAILS)
    db = client[DATABASE_NAME]
    
    print(f"ฐานข้อมูล: {DATABASE_NAME}")
    print("-" * 50)
    
    # ========================================
    # 1. Index สำหรับ BLACK_LIST collection
    # ========================================
    print(f"\nสร้าง Index สำหรับ collection: {BLACK_LIST}")
    
    # Index สำหรับ url (exact match - เร็วมาก)
    try:
        result = db[BLACK_LIST].create_index(
            [("url", ASCENDING)],
            name="idx_url_exact",
            unique=False  # ไม่ต้อง unique เพราะอาจมี URL ซ้ำจากแหล่งต่างๆ
        )
        print(f"  สร้าง index 'idx_url_exact' สำเร็จ: {result}")
    except Exception as e:
        print(f"  Index 'idx_url_exact' อาจมีอยู่แล้ว: {e}")
    
    # Index สำหรับ url_lower (case-insensitive matching)
    try:
        result = db[BLACK_LIST].create_index(
            [("url_lower", ASCENDING)],
            name="idx_url_lower",
            unique=False
        )
        print(f"  สร้าง index 'idx_url_lower' สำเร็จ: {result}")
    except Exception as e:
        print(f"  Index 'idx_url_lower' อาจมีอยู่แล้ว: {e}")
    
    # Index สำหรับ domain_name (สำหรับ domain-based lookup)
    try:
        result = db[BLACK_LIST].create_index(
            [("domain_name", ASCENDING)],
            name="idx_domain_name"
        )
        print(f"  สร้าง index 'idx_domain_name' สำเร็จ: {result}")
    except Exception as e:
        print(f"  Index 'idx_domain_name' อาจมีอยู่แล้ว: {e}")
    
    # Index สำหรับ phish_id (สำหรับ detail lookup)
    try:
        result = db[BLACK_LIST].create_index(
            [("phish_id", ASCENDING)],
            name="idx_phish_id",
            unique=True,
            sparse=True  # ข้าม documents ที่ไม่มี phish_id
        )
        print(f"  สร้าง index 'idx_phish_id' สำเร็จ: {result}")
    except Exception as e:
        print(f"  Index 'idx_phish_id' อาจมีอยู่แล้ว: {e}")
    
    # Compound index สำหรับ filtering (verifited + submission_time)
    try:
        result = db[BLACK_LIST].create_index(
            [("verifited", ASCENDING), ("submission_time", ASCENDING)],
            name="idx_verifited_time"
        )
        print(f"  สร้าง index 'idx_verifited_time' สำเร็จ: {result}")
    except Exception as e:
        print(f"  Index 'idx_verifited_time' อาจมีอยู่แล้ว: {e}")
    
    # ========================================
    # 2. Index สำหรับ USER collection
    # ========================================
    print(f"\nสร้าง Index สำหรับ collection: {USER_COLLECTION}")
    
    # Index สำหรับ api_key (unique)
    try:
        result = db[USER_COLLECTION].create_index(
            [("api_key", ASCENDING)],
            name="idx_api_key",
            unique=True
        )
        print(f"  สร้าง index 'idx_api_key' สำเร็จ: {result}")
    except Exception as e:
        print(f"  Index 'idx_api_key' อาจมีอยู่แล้ว: {e}")
    
    # ========================================
    # 3. Migration: เพิ่ม url_lower field
    # ========================================
    print(f"\nMigration: เพิ่ม 'url_lower' field ให้กับ documents ที่มีอยู่...")
    
    # หา documents ที่ยังไม่มี url_lower
    docs_without_lower = db[BLACK_LIST].count_documents({"url_lower": {"$exists": False}})
    print(f"  พบ {docs_without_lower} documents ที่ยังไม่มี 'url_lower'")
    
    if docs_without_lower > 0:
        # ใช้ bulk update สำหรับประสิทธิภาพ
        from pymongo import UpdateOne
        
        cursor = db[BLACK_LIST].find(
            {"url_lower": {"$exists": False}},
            {"_id": 1, "url": 1}
        )
        
        operations = []
        count = 0
        
        for doc in cursor:
            if "url" in doc and doc["url"]:
                operations.append(
                    UpdateOne(
                        {"_id": doc["_id"]},
                        {"$set": {"url_lower": doc["url"].lower()}}
                    )
                )
                count += 1
                
                # ทำ batch update ทุก 1000 records
                if len(operations) >= 1000:
                    db[BLACK_LIST].bulk_write(operations)
                    print(f"    อัปเดตแล้ว {count} documents...")
                    operations = []
        
        # อัปเดต batch สุดท้าย
        if operations:
            db[BLACK_LIST].bulk_write(operations)
        
        print(f"  เพิ่ม 'url_lower' ให้กับ {count} documents สำเร็จ")
    else:
        print("  ทุก documents มี 'url_lower' แล้ว")
    
    # ========================================
    # 4. แสดงสรุป indexes ทั้งหมด
    # ========================================
    print("\n" + "=" * 50)
    print("สรุป Indexes ทั้งหมด:")
    print("=" * 50)
    
    print(f"\n{BLACK_LIST}:")
    for index in db[BLACK_LIST].list_indexes():
        print(f"  - {index['name']}: {index['key']}")
    
    print(f"\n{USER_COLLECTION}:")
    for index in db[USER_COLLECTION].list_indexes():
        print(f"  - {index['name']}: {index['key']}")
    
    print("\nสร้าง indexes เสร็จสมบูรณ์!")
    print("\nTips:")
    print("  - รัน script นี้ซ้ำได้เสมอ (idempotent)")
    print("  - ควรรัน script นี้หลังจาก import ข้อมูลใหม่")
    
    client.close()


if __name__ == "__main__":
    create_indexes()
