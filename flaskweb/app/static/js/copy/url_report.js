(function($) {
    $(document).ready(function () {
    const lang = new URLSearchParams(window.location.search).get("lang") || "en";

    const translations = {
        "success_title": { "th": "สำเร็จ", "en": "Success" },
        "error_title": { "th": "ข้อผิดพลาด", "en": "Error" },
        "processing_title": { "th": "กำลังประมวลผล...", "en": "Processing..." },
        "confirm_delete_title": { "th": "ยืนยันการลบ?", "en": "Confirm Deletion?" },
        "confirm_delete_text": { "th": "คุณแน่ใจหรือไม่ที่จะลบรายการนี้?", "en": "Are you sure you want to delete this item?" },
        "yes": { "th": "ใช่", "en": "Yes" },
        "delete": { "th": "ลบ", "en": "Delete" },
        "cancel": { "th": "ยกเลิก", "en": "Cancel" }
    };

    function t(key) { return translations[key] ? translations[key][lang] : key; }

    // Inline language configuration to avoid CORS issues
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
        "order": [[4, "desc"]]
    });

    // Delete Single
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
                fetch(deleteUrl, { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                         Swal.fire(t('success_title'), data.message, 'success').then(() => location.reload());
                    } else {
                         Swal.fire(t('error_title'), data.error, 'error');
                    }
                });
            }
        });
    });
    
      // Bulk Delete
     $('#deleteSelectedBtn').on('click', function () {
        const ids = getSelectedIds();
        if (ids.length === 0) return;

        Swal.fire({
            title: t('confirm_delete_title'),
            text: `${t('confirm_delete_text')} (${ids.length})`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: t('delete'),
            cancelButtonText: t('cancel'),
            confirmButtonColor: '#d33'
        }).then((result) => {
            if (result.isConfirmed) {
                performAction('/controller/delete-selected-reports', ids);
            }
        });
    });

    function getSelectedIds() {
        const ids = [];
        $('.report-checkbox:checked').each(function () { ids.push($(this).data('id')); });
        return ids;
    }

    $('#selectAllCheckbox').on('change', function () {
        $('.report-checkbox').prop('checked', this.checked);
        updateSelectedCount();
    });

    $(document).on('change', '.report-checkbox', function() { updateSelectedCount(); });

    function updateSelectedCount() {
        const count = $('.report-checkbox:checked').length;
        $('#deleteSelectedBtn').prop('disabled', count === 0);
    }
    
     function performAction(url, ids) {
        Swal.fire({ title: t('processing_title'), didOpen: () => Swal.showLoading() });
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ report_ids: ids })
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success') {
                Swal.fire(t('success_title'), data.message, 'success').then(() => location.reload());
            } else {
                Swal.fire(t('error_title'), data.error, 'error');
            }
        })
        .catch(err => Swal.fire(t('error_title'), 'Network Error: ' + err, 'error'));
    }

    $('#searchInput').on('keyup', function () { table.search(this.value).draw(); });
});
})(jQuery);