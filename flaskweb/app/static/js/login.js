document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");

    function getLangFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('lang') || 'en';
    }
    const lang = getLangFromURL();

    const TRANSLATIONS = {
        'recaptcha_failed': { 'th': 'การยืนยัน reCAPTCHA ล้มเหลว โปรดลองอีกครั้ง', 'en': 'reCAPTCHA verification failed. Please try again.' },
        'checking': { 'th': 'กำลังตรวจสอบ...', 'en': 'Checking...' },
        'please_wait': { 'th': 'กรุณารอสักครู่', 'en': 'Please wait' },
        'ok_button': { 'th': 'ตกลง', 'en': 'OK' },
        'error_title_js': { 'th': 'เกิดข้อผิดพลาด!', 'en': 'Error Occurred!' },
        'unexpected_error_js': { 'th': 'เกิดข้อผิดพลาดที่ไม่คาดคิด', 'en': 'An unexpected error occurred.' },
        'network_error_js': {  'th': 'เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย โปรดลองอีกครั้ง', 'en': 'Network error occurred. Please try again.' }
    };

    function translate(key) {
        return TRANSLATIONS[key][lang] || TRANSLATIONS[key]['en'] || key;
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        Swal.fire({
            title: translate('checking'),
            html: translate('please_wait'),
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // --- reCAPTCHA Integration Start ---
        grecaptcha.ready(function () {
            // ใช้ Site Key เดียวกันกับหน้า register
            grecaptcha.execute('6LeKSZ0rAAAAAFV1_u7CJHPwf5XrtHdKvXw2AAIP', { action: 'submit' }).then(function (token) {
                const formData = new FormData(form);
                formData.append('g-recaptcha-response', token); // เพิ่ม reCAPTCHA token เข้าไปใน form data

                const actionUrl = form.getAttribute("action");

                fetch(actionUrl, {
                    method: "POST",
                    body: formData
                })
                .then(response => {
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.indexOf("application/json") !== -1) {
                        return response.json();
                    } else {
                        throw new Error('Server response was not JSON. Status: ' + response.status);
                    }
                })
                .then(data => {
                    const loadingTime = data.alert_type === "error" ? 500 : 1500;

                    setTimeout(() => {
                        Swal.close();

                        const swalOptions = {
                            title: data.alert,
                            icon: data.alert_type,
                            showConfirmButton: false, // <-- ซ่อนปุ่ม "ตกลง"
                            timer: 2000 // <-- ตั้งเวลาให้ป๊อปอัปหายไปเองใน 2 วินาที
                        };

                        Swal.fire(swalOptions).then(() => {
                            if (data.redirect_url) {
                                const hasLang = data.redirect_url.includes('?') ? '&lang=' : '?lang=';
                                const redirectWithLang = data.redirect_url + hasLang + lang;
                                window.location.href = redirectWithLang;
                            }
                        });
                    }, loadingTime);
                })
                .catch(error => {
                    console.error('Error during fetch or parsing:', error);
                    Swal.close();
                    Swal.fire({
                        icon: 'error',
                        title: translate('error_title_js'),
                        text: translate('network_error_js') + ': ' + error.message,
                        showConfirmButton: false, // <-- ซ่อนปุ่ม "ตกลง" ในกรณีเกิดข้อผิดพลาด
                        timer: 2000 // <-- ตั้งเวลาให้ป๊อปอัปหายไปเองใน 3 วินาที
                    });
                });
            });
        });
        // --- reCAPTCHA Integration End ---
    });
});