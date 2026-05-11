document.addEventListener("DOMContentLoaded", function () {
    // translations object นี้จะถูกใช้โดย JavaScript โดยตรง
    const translations = {
        "sending_report": { "th": "กำลังส่งรายงาน...", "en": "Sending report..." },
        "success_title": { "th": "สำเร็จ!", "en": "Success!" },
        "success_message_single": { "th": "ส่งรายงานสำเร็จ", "en": "Report submitted successfully" },
        "success_message_multiple": { "th": "ส่งรายงานสำเร็จ {count} รายการ", "en": "Successfully submitted {count} reports" },
        "partial_success_title": { "th": "รายงานบางส่วนมีปัญหา", "en": "Partial Success!" },
        "partial_success_message": { "th": "มีบาง URL ที่ไม่ถูกต้องหรือบันทึกไม่สำเร็จ: <br>{details}", "en": "Some URLs were invalid or failed to save: <br>{details}" },
        "error_title": { "th": "ข้อผิดพลาด!", "en": "Error!" },
        "error_message": { "th": "ไม่สามารถส่งรายงานได้", "en": "Unable to submit the report" },
        "server_error_message": { "th": "ไม่สามารถเชื่อมต่อกับ Server ได้", "en": "Cannot connect to the server" },
        "confirm_button": { "th": "ตกลง", "en": "OK" },
        "retry_button": { "th": "ลองอีกครั้ง", "en": "Try Again" },
        "url_report_success": { "th": "URL '{url}' บันทึกสำเร็จ", "en": "URL '{url}' saved successfully" },
        "url_report_failed": { "th": "URL '{url}' บันทึกไม่สำเร็จ: {error}", "en": "URL '{url}' failed to save: {error}" },
        "url_invalid_csv": { "th": "แถวที่ {row}: URL '{url}' ไม่ถูกต้อง", "en": "Row {row}: URL '{url}' is invalid" },
        "reporter_missing": { "th": "ข้อมูลผู้รายงานหายไป", "en": "Reporter information is missing." },
        "invalid_single_url": { "th": "รูปแบบ URL ที่กรอกไม่ถูกต้อง", "en": "The entered URL format is invalid." },
        "invalid_file_type_csv": { "th": "ชนิดไฟล์ไม่ถูกต้อง กรุณาอัปโหลดไฟล์ CSV", "en": "Invalid file type. Please upload a CSV file." },
        "error_processing_csv_file": { "th": "เกิดข้อผิดพลาดในการประมวลผลไฟล์ CSV", "en": "Error occurred while processing the CSV file." },
        "no_valid_url_or_csv_data_provided": { "th": "ไม่พบ URL ที่ถูกต้อง หรือข้อมูล CSV ที่ให้มา", "en": "No valid URL or CSV data provided." },
        "all_reports_processed_successfully": { "th": "ประมวลผลรายงานทั้งหมดสำเร็จ", "en": "All reports processed successfully." },
        "only_invalid_urls_found": { "th": "พบเฉพาะ URL ที่ไม่ถูกต้องในไฟล์ CSV เท่านั้น ไม่มีการบันทึก", "en": "Only invalid URLs were found in the CSV file. No records saved." },
        "url_or_csv_note": { "th": "กรอก URL เพียงหนึ่งรายการ หรืออัปโหลดไฟล์ CSV ที่มี URL (หนึ่ง URL ต่อหนึ่งแถวในคอลัมน์แรก)", "en": "Enter a single URL OR upload a CSV file with URLs (one URL per row in the first column)." },
        "csv_file_note": { "th": "อัปโหลดไฟล์ CSV ที่มี URL แต่ละ URL ควรอยู่ในบรรทัดใหม่ในคอลัมน์แรก (เช่น https://malicious.com)", "en": "Upload a CSV file containing URLs. Each URL should be on a new line in the first column. (e.g. https://malicious.com)" }
    };

    const getLangFromURL = () => {
        const params = new URLSearchParams(window.location.search);
        // หากไม่มี 'lang' ใน URL, หรือเป็นค่าอื่นที่ไม่ใช่ 'th', ให้ถือว่าเป็น 'en'
        return params.get('lang') === 'th' ? 'th' : 'en';
    };

    const lang = getLangFromURL();
    const reportForm = document.getElementById('reportForm');

    if (!reportForm) {
        console.error("Report form not found!");
        return; // ออกจากฟังก์ชันถ้าไม่พบฟอร์ม
    }

    reportForm.addEventListener('submit', function (e) {
        e.preventDefault();

        Swal.fire({
            title: translations["sending_report"][lang],
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        const formData = new FormData(reportForm);

        // *** แก้ไขตรงนี้: ใช้ URL ที่ถูกต้องจาก Flask's url_for ซึ่งอยู่ใน action attribute ของฟอร์ม ***
        const formActionUrl = reportForm.action; 

        fetch(formActionUrl, { // ใช้ formActionUrl ที่ได้มาจาก attribute action ของฟอร์ม
            method: 'POST',
            body: formData
        })
        .then(response => {
            // ตรวจสอบว่า response เป็น JSON จริงๆ หรือไม่
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            } else {
                // หากไม่ใช่ JSON (เช่น HTML redirect), ให้ throw error หรือจัดการ
                console.error("Server did not return JSON. Content-Type:", contentType);
                // อาจจะ redirect ไปยังหน้า login/error หากเป็นไปได้
                // window.location.href = response.url; // หรือ URL อื่นๆ ที่เหมาะสม
                throw new TypeError("Server response was not JSON.");
            }
        })
        .then(data => {
            Swal.close();
            handleResponse(data, lang, translations);
        })
        .catch(error => {
            Swal.close();
            console.error("Fetch error:", error); // Log ข้อผิดพลาดจริง
            Swal.fire({
                title: translations["error_title"][lang],
                text: translations["server_error_message"][lang],
                icon: 'error',
                confirmButtonText: translations["retry_button"][lang]
            });
        });
    });

    function handleResponse(data, lang, translations) {
        if (data.status === 'success') {
            const count = data.data?.length || 0;
            const msg = count > 1
                ? translations["success_message_multiple"][lang].replace('{count}', count)
                : translations["success_message_single"][lang];

            Swal.fire({
                title: translations["success_title"][lang],
                text: msg,
                icon: 'success',
                confirmButtonText: translations["confirm_button"][lang]
            }).then((r) => {
                if (r.isConfirmed) {
                    window.location.reload(); // โหลดหน้าใหม่หลังจาก SweetAlert2 ปิด
                }
            });

        } else if (data.status === 'partial_success') {
            let detailsHtml = '';

            if (data.data?.processed_results) {
                for (const item of data.data.processed_results) {
                    if (item.status === 'success') {
                        detailsHtml += `<p>${translations["url_report_success"][lang].replace('{url}', item.url)}</p>`;
                    } else {
                        detailsHtml += `<p class="text-danger">${translations["url_report_failed"][lang]
                            .replace('{url}', item.url)
                            .replace('{error}', item.error || translations["error_message"][lang])}</p>`;
                    }
                }
            }

            if (data.data?.invalid_urls_from_csv?.length) {
                for (const item of data.data.invalid_urls_from_csv) {
                    detailsHtml += `<p class="text-warning">${item}</p>`;
                }
            }

            Swal.fire({
                title: translations["partial_success_title"][lang],
                html: translations["partial_success_message"][lang].replace('{details}', detailsHtml),
                icon: 'warning',
                confirmButtonText: translations["confirm_button"][lang]
            }).then((r) => {
                if (r.isConfirmed) {
                    window.location.reload(); // โหลดหน้าใหม่หลังจาก SweetAlert2 ปิด
                }
            });

        } else { // status is 'error'
            const extra = data.data?.invalid_urls_from_csv?.join('; ') || '';
            Swal.fire({
                title: translations["error_title"][lang],
                text: data.error || `${translations["error_message"][lang]}${extra ? ` (${extra})` : ''}`,
                icon: 'error',
                confirmButtonText: translations["retry_button"][lang]
            });
        }
    }
});