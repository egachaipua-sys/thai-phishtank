document.addEventListener("DOMContentLoaded", function () {
    const requestApiKeyBtn = document.getElementById('requestApiKeyBtn');
    const copyApiKeyBtn = document.getElementById('copyApiKeyBtn');
    const apiKeyInput = document.getElementById('apiKey');

    function getLangFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get('lang') || 'en';
    }
    const lang = getLangFromURL();

    const TRANSLATIONS = {
        'success_title': { 'th': 'สำเร็จ', 'en': 'Success' },
        'error_title': { 'th': 'ข้อผิดพลาด', 'en': 'Error' },
        'try_again': { 'th': 'ลองใหม่', 'en': 'Try Again' },
        'oops': { 'th': 'โอ๊ะ...เกิดข้อผิดพลาด', 'en': 'Oops... An error occurred' },
        'generic_error': { 'th': 'เกิดข้อผิดพลาดบางอย่าง กรุณาลองใหม่อีกครั้งภายหลัง', 'en': 'Something went wrong. Please try again later' },
        'close': { 'th': 'ปิด', 'en': 'Close' },
        'copied': { 'th': 'คัดลอกแล้ว!', 'en': 'Copied!' },
        'copied_to_clipboard': { 'th': 'API Key ของคุณได้ถูกคัดลอกไปยังคลิปบอร์ดแล้ว', 'en': 'Your API Key has been copied to the clipboard' },
        'ok': { 'th': 'ตกลง', 'en': 'OK' },
        'request_api_key': { 'th': 'ขอรับ API Key', 'en': 'Request API Key' },
        'copy_api_key': { 'th': 'คัดลอก', 'en': 'Copy' }
    };

    function translate(key) {
        return TRANSLATIONS[key][lang] || TRANSLATIONS[key]['en'] || key;
    }

    if (requestApiKeyBtn) {
        requestApiKeyBtn.textContent = translate('request_api_key');
    }
    if (copyApiKeyBtn) {
        copyApiKeyBtn.textContent = translate('copy_api_key');
    }

    if (requestApiKeyBtn) {
        requestApiKeyBtn.addEventListener('click', function () {
            fetch('/getapi/request_api_key', {
                method: 'POST',
                credentials: 'include'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.alert_type === "success") {
                        apiKeyInput.value = data.api_key;
                        Swal.fire({
                            icon: 'success',
                            title: translate('success_title'),
                            text: data.alert,
                            confirmButtonText: translate('ok')
                        });
                    } else {
                        Swal.fire({
                            icon: 'error',
                            title: translate('error_title'),
                            text: data.alert,
                            confirmButtonText: translate('try_again')
                        });
                    }
                })
                .catch(error => {
                    Swal.fire({
                        icon: 'error',
                        title: translate('oops'),
                        text: translate('generic_error'),
                        confirmButtonText: translate('close')
                    });
                });
        });
    }

    if (copyApiKeyBtn) {
        copyApiKeyBtn.addEventListener('click', function () {
            apiKeyInput.select();
            document.execCommand('copy');
            Swal.fire({
                icon: 'success',
                title: translate('copied'),
                text: translate('copied_to_clipboard'),
                confirmButtonText: translate('ok')
            });
        });
    }
});