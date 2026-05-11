import numpy as np
import time
import sys
import os

# เพิ่ม path ของ scripts folder
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_path = os.path.join(current_dir, 'scripts')
sys.path.append(scripts_path)
from scripts.feature_extractor import extract_features
import joblib
import warnings

warnings.simplefilter("ignore")

def prediction(classifier_name, test_url):
    try:
        a = int(time.time() * 1000.0)

        # ดึงคุณสมบัติจาก URL
        try:
            features_test = extract_features(test_url)
        except Exception as fe:
            print(f"[ERROR] Feature extraction failed for {test_url}: {fe}")
            return 2  # ถือว่า URL ไม่สามารถเข้าถึงได้
            
        if features_test is None:
            print(f"[INFO] Cannot access URL or extract features: {test_url}")
            return 2
        
        b = int(time.time() * 1000.0)
        # print("Feature selection: "+str((b-a)))

        features_test = np.array(features_test).reshape((1, -1))
        
        # โหลดโมเดลที่ถูกฝึกไว้
        clf = joblib.load(classifier_name + '.pkl')

        a = int(time.time() * 1000.0)
        pred = clf.predict(features_test)
        b = int(time.time() * 1000.0)
        # print("Prediction: "+str((b-a)))

        return pred[0]
    
    except FileNotFoundError:
        print(f"[ERROR] Model file not found: {classifier_name}.pkl")
        return 2
    except ValueError as ve:
        print(f"[ERROR] ValueError encountered - {ve}")
        return 2
    except Exception as e:
        print(f"[ERROR] Unexpected error in prediction: {e}")
        return 2

	
# if __name__ == '__main__':
# print("phising: ")
# print( prediction('app/mlengine/mlp98.87',"https://google.com"))
# print("safe: ")
# print(prediction('models/project_k/mlp94',"https://chatgpt.com/"))