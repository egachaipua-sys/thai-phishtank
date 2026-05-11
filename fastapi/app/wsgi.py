# wsgi.py
import sys
import os

# กำหนด base directory
base_dir = os.path.dirname(os.path.abspath(__file__))
# เพิ่ม path ของ app folder
app_path = os.path.join(base_dir)
sys.path.append(app_path)

from prediction_api import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)