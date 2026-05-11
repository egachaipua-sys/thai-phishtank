document.addEventListener("DOMContentLoaded", function () {
    const confirmForm = document.getElementById('confirmEmailForm');
    const formActionUrl = confirmForm.action;

    function getLangFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('lang') || 'en';
    }

    const lang = getLangFromURL();

    const TRANSLATIONS = {
        'checking': { 'th': 'กำลังตรวจสอบ...', 'en': 'Checking...' },
        'please_wait': { 'th': 'กรุณารอสักครู่', 'en': 'Please wait' },
        'ok_button': { 'th': 'ตกลง', 'en': 'OK' },
        'error_title_js': { 'th': 'เกิดข้อผิดพลาด!', 'en': 'Error Occurred!' },
        'token_missing_error_js': { 'th': 'กรุณากรอกโทเคน', 'en': 'Please enter a token.' },
        'network_error_js': { 'th': 'เกิดข้อผิดพลาดในการเชื่อมต่อเครือข่าย โปรดลองอีกครั้ง', 'en': 'Network error occurred. Please try again.' },
        'email_verified_message_js': { 'th': 'อีเมลของคุณได้รับการยืนยันเรียบร้อยแล้ว', 'en': 'Your email has been successfully verified.' }
    };

    function translate(key) {
        return TRANSLATIONS[key][lang] || TRANSLATIONS[key]['en'] || key;
    }

    confirmForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const formData = new FormData(confirmForm);
        const token = formData.get('token');

        if (!token) {
            Swal.fire({
                icon: 'error',
                title: translate('error_title_js'),
                text: translate('token_missing_error_js'),
                confirmButtonText: translate('ok_button')
            });
            return;
        }

        Swal.fire({
            title: translate('checking'),
            html: translate('please_wait'),
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        fetch(formActionUrl, {
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

                if (data.alert_type === "error") {
                    Swal.fire({
                        title: data.alert,
                        icon: "error",
                        confirmButtonText: translate('ok_button')
                    });
                } else {
                    Swal.fire({
                        title: translate('email_verified_message_js'),
                        icon: "success",
                        confirmButtonText: translate('ok_button')
                    }).then((result) => {
                        if (result.isConfirmed) {
                            confirmForm.reset();
                            const loginUrl = window.location.origin + '/auth/login?lang=' + lang;
                            window.location.href = loginUrl;
                        }
                    });
                }
            }, loadingTime);
        })
        .catch(error => {
            Swal.close();
            Swal.fire({
                title: translate('error_title_js'),
                text: translate('network_error_js') + ': ' + error.message,
                icon: 'error',
                confirmButtonText: translate('ok_button')
            });
            console.error('Error:', error);
        });
    });
});