from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import pandas as pd
from scripts.feature_extractor import extract_features
from threading import Lock
import time

print_lock = Lock()
write_lock = Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def get_processed_urls(output_file):
    if os.path.exists(output_file):
        try:
            df = pd.read_csv(output_file)
            return set(df["url"].tolist())
        except Exception:
            return set()
    return set()

def save_result(result, output_file, columns):
    with write_lock:
        df = pd.DataFrame([result], columns=columns)
        df.to_csv(
            output_file, mode="a", header=not os.path.exists(output_file), index=False
        )

def process_url(url, output_file, columns, processed_urls):
    try:
        if url in processed_urls:
            safe_print(f"ข้าม URL ที่ประมวลผลแล้ว: {url}")
            return None

        safe_print(f"กำลังประมวลผล URL: {url}")
        start_time = time.time()

        # กำหนด timeout เป็น 20 วินาที
        try:
            features = extract_features(url, status="0")
            if features:
                features.insert(0, url)
                save_result(features, output_file, columns)
                safe_print(f"สกัดและบันทึกคุณลักษณะสำเร็จ: {url} (ใช้เวลา {time.time() - start_time:.2f} วินาที)")
            else:
                safe_print(f"ไม่สามารถสกัดคุณลักษณะ: {url}")
        except Exception as e:
            safe_print(f"เกิดข้อผิดพลาดกับ URL {url}: {e}")
    except Exception as e:
        safe_print(f"เกิดข้อผิดพลาดในการประมวลผล URL {url}: {e}")

def process_file(input_path, output_file, columns):
    processed_urls = get_processed_urls(output_file)
    try:
        df = pd.read_csv(input_path)
        urls = df["url"].tolist()

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(process_url, url, output_file, columns, processed_urls): url for url in urls}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    future.result(timeout=20)  # กำหนด timeout เป็น 20 วินาที
                except Exception as e:
                    safe_print(f"ข้าม URL เนื่องจากใช้เวลานานเกิน 20 วินาที: {url} ({e})")
    except Exception as e:
        safe_print(f"เกิดข้อผิดพลาดในการอ่านไฟล์ {input_path}: {e}")

def process_folder(input_folder, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    columns = ['url', 'url_length', 'url_length_hostname', 'having_ip_address',
              'count_dots', 'count_hyphens', 'count_at', 'count_exclamation',
              'count_and', 'count_or', 'count_equal', 'count_underscore',
              'count_tilde', 'count_percentage', 'count_slash', 'count_star',
              'count_colon', 'count_comma', 'count_semicolumn', 'count_dollar',
              'count_space', 'check_www', 'check_com', 'count_double_slash',
              'count_http_token', 'https_token', 'ratio_digits_url',
              'ratio_digits_hostname', 'punycode', 'port', 'tld_in_path',
              'tld_in_subdomain', 'abnormal_subdomain', 'count_subdomain',
              'prefix_suffix', 'random_domain', 'shortening_service',
              'path_extension', 'count_redirection', 'count_external_redirection',
              'length_word_raw', 'char_repeat', 'shortest_word_length',
              'shortest_word_length_host', 'shortest_word_length_path',
              'longest_word_length', 'longest_word_length_host',
              'longest_word_length_path', 'average_word_length',
              'average_word_length_host', 'average_word_length_path',
              'phish_hints', 'domain_in_brand', 'brand_in_path_subdomain'
              , 'suspecious_tld', 'statistical_report',
              'nb_hyperlinks', 'internal_hyperlinks', 'external_hyperlinks',
              'null_hyperlinks', 'external_css', 'internal_redirection',
              'external_redirection', 'internal_errors', 'external_errors',
              'login_form', 'external_favicon', 'links_in_tags',
              'submitting_to_email', 'internal_media', 'external_media',
              'sfh', 'iframe', 'popup_window', 'safe_anchor', 'onmouseover',
              'right_clic', 'empty_title', 'domain_in_title',
              'domain_with_copyright', 'whois_registered_domain',
              'domain_registration_length', 'domain_age', 'web_traffic',
              'dns_record', 'google_index', 'page_rank', 'status']

    input_files = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.endswith(".csv")
    ]

    with ThreadPoolExecutor(max_workers=6) as executor:
        for file in input_files:
            executor.submit(process_file, file, output_file, columns)

def process_multiple_folders(folder_list, base_output_folder):
    with ThreadPoolExecutor(max_workers=len(folder_list)) as executor:
        for folder in folder_list:
            input_folder = os.path.join("database", folder)
            output_file = os.path.join(base_output_folder, f"{folder}_features.csv")
            executor.submit(process_folder, input_folder, output_file)

# รันโค้ด
folder_list = [
    "part/part6"
]  # เพิ่มโฟลเดอร์ที่ต้องการประมวลผล
base_output_folder = "output/part"
process_multiple_folders(folder_list, base_output_folder)