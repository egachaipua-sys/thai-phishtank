document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        function getLangFromURL() {
            const params = new URLSearchParams(window.location.search);
            return params.get('lang') || 'en';
        }

        const lang = getLangFromURL();

        const TRANSLATIONS = {
            'recaptcha_failed': { 'th': 'การยืนยัน reCAPTCHA ล้มเหลว โปรดลองอีกครั้ง', 'en': 'reCAPTCHA verification failed. Please try again.' },
            'checking': { 'th': 'กำลังตรวจสอบ...', 'en': 'Checking...' },
            'please_wait': { 'th': 'กรุณารอสักครู่', 'en': 'Please wait' },
            'ok': { 'th': 'ตกลง', 'en': 'OK' },
            'error_title': { 'th': 'ข้อผิดพลาด!', 'en': 'Error!' }
        };

        function translate(key) {
            return TRANSLATIONS[key][lang] || TRANSLATIONS[key]['en'] || key;
        }

        Swal.fire({
            title: translate('checking'),
            html: translate('please_wait'),
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // เรียก reCAPTCHA ก่อนส่งฟอร์ม
        grecaptcha.ready(function () {
            grecaptcha.execute('6LeKSZ0rAAAAAFV1_u7CJHPwf5XrtHdKvXw2AAIP', { action: 'submit' }).then(function (token) {
                const formData = new FormData(form);
                formData.append('g-recaptcha-response', token); // ใส่ token เข้า form

                const actionUrl = form.getAttribute("action");

                fetch(actionUrl, {
                    method: "POST",
                    body: formData
                })
                    .then(response => response.json())
                    .then(data => {
                        const loadingTime = data.alert_type === "error" ? 500 : 1500;

                        setTimeout(() => {
                            Swal.close();

                            if (data.alert_type === "error") {
                                Swal.fire({
                                    title: data.alert,
                                    icon: "error",
                                    confirmButtonText: translate('ok')
                                });
                            } else {
                                Swal.fire({
                                    title: data.alert,
                                    icon: "success",
                                    confirmButtonText: translate('ok')
                                }).then((result) => {
                                    if (result.isConfirmed) {
                                        form.reset();
                                        window.location.href = `https://thaiphishtank.org/auth/verify_email?lang=${lang}`;
                                    }
                                });
                            }
                        }, loadingTime);
                    })
                    .catch(error => {
                        Swal.close();
                        Swal.fire({
                            title: translate('error_title'),
                            text: error.message,
                            icon: 'error',
                            confirmButtonText: translate('ok')
                        });
                        console.error('Error:', error);
                    });
            });
        });
    });
});
