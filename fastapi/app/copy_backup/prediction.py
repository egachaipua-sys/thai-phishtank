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
        features_test = extract_features(test_url)
        # features_test = extract_data(test_url)
        if features_test is None:
            print("Error: Failed to extract features.")
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
        print("Error: Model file not found.")
        return 2
    except ValueError as ve:
        print(f"Error: ValueError encountered - {ve}")
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 2

