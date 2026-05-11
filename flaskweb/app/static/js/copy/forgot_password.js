document.addEventListener("DOMContentLoaded", function () {
    const forgotForm = document.getElementById('forgot-form');

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
        'network_error_js': { 'th': 'เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย โปรดลองอีกครั้ง', 'en': 'Network error occurred. Please try again.' },
        'reset_link_sent_js': { 'th': 'ลิงก์รีเซ็ตรหัสผ่านถูกส่งไปที่อีเมลของคุณแล้ว', 'en': 'A password reset link has been sent to your email.' }
    };

    function translate(key) {
        return TRANSLATIONS[key][lang] || TRANSLATIONS[key]['en'] || key;
    }

    forgotForm.addEventListener('submit', function(e) {
        e.preventDefault();

        Swal.fire({
            title: translate('checking'),
            html: translate('please_wait'),
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // --- reCAPTCHA v3 integration ---
        grecaptcha.ready(function () {
            grecaptcha.execute('6LeKSZ0rAAAAAFV1_u7CJHPwf5XrtHdKvXw2AAIP', { action: 'submit' }).then(function (token) {
                const formData = new FormData(forgotForm);
                formData.append('g-recaptcha-response', token);

                const actionUrl = forgotForm.getAttribute('action');

                fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
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
                    const loadingTime = data.sweetalert && data.sweetalert.icon === "error" ? 500 : 1500;

                    setTimeout(() => {
                        Swal.close();

                        if (data.sweetalert) {
                            Swal.fire({
                                icon: data.sweetalert.icon,
                                title: data.sweetalert.title || translate('error_title_js'),
                                text: data.sweetalert.text || '',
                                confirmButtonText: translate('ok_button')
                            }).then(() => {
                                if (data.redirect_url) {
                                    const loginUrl = data.redirect_url + '?lang=' + lang;
                                    window.location.href = loginUrl;
                                } else if (data.sweetalert.icon === 'success') {
                                    const loginUrl = window.location.origin + '/auth/login?lang=' + lang;
                                    window.location.href = loginUrl;
                                }
                            });
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: translate('error_title_js'),
                                text: translate('unexpected_error_js'),
                                confirmButtonText: translate('ok_button')
                            });
                        }
                    }, loadingTime);
                })
                .catch(error => {
                    console.error('Error:', error);
                    Swal.close();
                    Swal.fire({
                        icon: 'error',
                        title: translate('error_title_js'),
                        text: translate('network_error_js') + ': ' + error.message,
                        confirmButtonText: translate('ok_button')
                    });
                });
            }).catch(() => {
                Swal.close();
                Swal.fire({
                    icon: 'error',
                    title: translate('error_title_js'),
                    text: translate('recaptcha_failed'),
                    confirmButtonText: translate('ok_button')
                });
            });
        });
        // --- End reCAPTCHA ---
    });
});
