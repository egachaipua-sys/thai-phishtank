(function($) {
    $(document).ready(function () {
    const lang = new URLSearchParams(window.location.search).get("lang") || "en";

    const translations = {
        "success_title": { "th": "สำเร็จ", "en": "Success" },
        "error_title": { "th": "ข้อผิดพลาด", "en": "Error" },
        "processing_title": { "th": "กำลังประมวลผล...", "en": "Processing..." },
        "processing_text": { "th": "กรุณารอสักครู่", "en": "Please wait..." },
        "confirm_delete_title": { "th": "ยืนยันการลบ?", "en": "Confirm Deletion?" },
        "confirm_delete_text": { "th": "คุณแน่ใจหรือไม่ที่จะลบรายการนี้?", "en": "Are you sure you want to delete this item?" },
        "confirm_verify_title": { "th": "ยืนยันการตรวจสอบ?", "en": "Confirm Verification?" },
        "confirm_verify_text": { "th": "คุณต้องการยืนยันรายการนี้ใช่หรือไม่?", "en": "Do you want to verify this item?" },
        "yes": { "th": "ใช่", "en": "Yes" },
        "no": { "th": "ไม่", "en": "No" },
        "delete": { "th": "ลบ", "en": "Delete" },
        "cancel": { "th": "ยกเลิก", "en": "Cancel" }
    };

    function t(key) {
        return translations[key] ? translations[key][lang] : key;
    }

    // Client-side DataTables initialization with inline language
    const dtLanguage = lang === 'th' ? {
        "lengthMenu": "แสดง _MENU_ รายการ",
        "zeroRecords": "ไม่พบข้อมูล",
        "info": "แสดง _START_ ถึง _END_ จาก _TOTAL_ รายการ",
        "infoEmpty": "ไม่มีรายการ",
        "infoFiltered": "(กรองจากทั้งหมด _MAX_ รายการ)",
        "search": "ค้นหา:",
        "paginate": { "first": "หน้าแรก", "last": "หน้าสุดท้าย", "next": "ถัดไป", "previous": "ก่อนหน้า" }
    } : {
        "lengthMenu": "Show _MENU_ entries",
        "zeroRecords": "No matching records found",
        "info": "Showing _START_ to _END_ of _TOTAL_ entries",
        "infoEmpty": "No entries available",
        "infoFiltered": "(filtered from _MAX_ total entries)",
        "search": "Search:",
        "paginate": { "first": "First", "last": "Last", "next": "Next", "previous": "Previous" }
    };

    const table = $('#reportsTable').DataTable({
        "pageLength": 20,
        "lengthMenu": [20, 50, 100],
        "responsive": true,
        "language": dtLanguage,
        "order": [[4, "desc"]], // Default sort by date (5th column usually)
    });

    // Handle Verify Single
    $(document).on('click', '.verify-report-btn', function () {
        const apiUrl = $(this).data('url');
        const reportUrl = $(this).data('report-url');
        
        Swal.fire({
             title: t('confirm_verify_title'),
             text: t('confirm_verify_text'),
             icon: 'question',
             showCancelButton: true,
             confirmButtonText: t('yes'),
             cancelButtonText: t('cancel')
        }).then((result) => {
             if (result.isConfirmed) {
                 fetch(apiUrl, {
                     method: 'POST',
                     headers: { 'Content-Type': 'application/json' },
                     body: JSON.stringify({ url: reportUrl })
                 })
                 .then(response => response.json())
                 .then(data => {
                     if (data.status === 'success') {
                         Swal.fire(t('success_title'), data.message || 'Verified', 'success')
                         .then(() => location.reload());
                     } else {
                         Swal.fire(t('error_title'), data.message || 'Error', 'error');
                     }
                 })
                 .catch(err => {
                     Swal.fire(t('error_title'), 'Network Error', 'error');
                 });
             }
        });
    });

    // Handle Delete Single
    $(document).on('click', '.delete-report-btn', function () {
        const deleteUrl = $(this).data('url');
        
        Swal.fire({
            title: t('confirm_delete_title'),
            text: t('confirm_delete_text'),
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: t('delete'),
            cancelButtonText: t('cancel'),
            confirmButtonColor: '#d33'
        }).then((result) => {
            if (result.isConfirmed) {
                fetch(deleteUrl, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                         Swal.fire(t('success_title'), data.message, 'success')
                         .then(() => location.reload());
                    } else {
                         Swal.fire(t('error_title'), data.error || data.message, 'error');
                    }
                })
                .catch(err => Swal.fire(t('error_title'), 'Network error', 'error'));
            }
        });
    });

    // Verify Selected
    $('#verifySelectedBtn').on('click', function () {
        const selectedIds = getSelectedIds();
        if (selectedIds.length === 0) return;
        
        Swal.fire({
            title: t('confirm_verify_title'),
            text: `${t('confirm_verify_text')} (${selectedIds.length})`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: t('yes'),
            cancelButtonText: t('cancel')
        }).then((result) => {
            if (result.isConfirmed) {
                performAction('/controller/verify-selected-reports', selectedIds);
            }
        });
    });

    // Delete Selected
    $('#deleteSelectedBtn').on('click', function () {
        const selectedIds = getSelectedIds();
        if (selectedIds.length === 0) return;

        Swal.fire({
            title: t('confirm_delete_title'),
            text: `${t('confirm_delete_text')} (${selectedIds.length})`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: t('delete'),
            cancelButtonText: t('cancel'),
            confirmButtonColor: '#d33'
        }).then((result) => {
            if (result.isConfirmed) {
                performAction('/controller/delete-selected-reports', selectedIds);
            }
        });
    });

    // Helper: Get Selected IDs
    function getSelectedIds() {
        const ids = [];
        $('.report-checkbox:checked').each(function () {
            ids.push($(this).data('id'));
        });
        return ids;
    }

    // Helper: Select All
    $('#selectAllCheckbox').on('change', function () {
        $('.report-checkbox').prop('checked', this.checked);
        updateSelectedCount();
    });

    // Helper: Update Count (Enable/Disable buttons)
    $(document).on('change', '.report-checkbox', function() {
        updateSelectedCount();
    });

    function updateSelectedCount() {
        const count = $('.report-checkbox:checked').length;
        const btnVerify = $('#verifySelectedBtn');
        const btnDelete = $('#deleteSelectedBtn');

        if (count > 0) {
            btnVerify.prop('disabled', false);
            btnDelete.prop('disabled', false);
        } else {
            btnVerify.prop('disabled', true);
            btnDelete.prop('disabled', true);
        }
    }

    // Helper: Perform AJAX Action
    function performAction(url, ids) {
        Swal.fire({
            title: t('processing_title'),
            text: t('processing_text'),
            allowOutsideClick: false,
            didOpen: () => Swal.showLoading()
        });
        
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ report_ids: ids })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                Swal.fire(t('success_title'), data.message, 'success')
                .then(() => location.reload());
            } else {
                Swal.fire(t('error_title'), data.error || data.message, 'error');
            }
        })
        .catch(err => {
            Swal.fire(t('error_title'), 'Network error', 'error');
        });
    }

    // Search Box Custom
    $('#searchInput').on('keyup', function () {
        table.search(this.value).draw();
    });
});
})(jQuery);
