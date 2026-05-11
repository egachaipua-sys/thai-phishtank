/**
 * DataTables Language Configuration
 * This file provides inline translations to avoid CORS issues with CDN-based language files.
 * 
 * Usage:
 * Include this file before DataTables initialization, then use:
 * $('#table').DataTable({
 *     "language": getDataTablesLanguage(lang)
 * });
 */

function getDataTablesLanguage(lang) {
    if (lang === 'th') {
        return {
            "processing": "กำลังดำเนินการ...",
            "search": "ค้นหา:",
            "lengthMenu": "แสดง _MENU_ รายการ",
            "info": "แสดง _START_ ถึง _END_ จาก _TOTAL_ รายการ",
            "infoEmpty": "แสดง 0 ถึง 0 จาก 0 รายการ",
            "infoFiltered": "(กรองข้อมูลจากทั้งหมด _MAX_ รายการ)",
            "loadingRecords": "กำลังโหลดข้อมูล...",
            "zeroRecords": "ไม่พบข้อมูล",
            "emptyTable": "ไม่มีข้อมูลในตาราง",
            "paginate": {
                "first": "หน้าแรก",
                "previous": "ก่อนหน้า",
                "next": "ถัดไป",
                "last": "หน้าสุดท้าย"
            },
            "aria": {
                "sortAscending": ": เปิดใช้งานเพื่อเรียงลำดับจากน้อยไปมาก",
                "sortDescending": ": เปิดใช้งานเพื่อเรียงลำดับจากมากไปน้อย"
            }
        };
    } else {
        return {
            "processing": "Processing...",
            "search": "Search:",
            "lengthMenu": "Show _MENU_ entries",
            "info": "Showing _START_ to _END_ of _TOTAL_ entries",
            "infoEmpty": "Showing 0 to 0 of 0 entries",
            "infoFiltered": "(filtered from _MAX_ total entries)",
            "loadingRecords": "Loading...",
            "zeroRecords": "No matching records found",
            "emptyTable": "No data available in table",
            "paginate": {
                "first": "First",
                "previous": "Previous",
                "next": "Next",
                "last": "Last"
            },
            "aria": {
                "sortAscending": ": activate to sort column ascending",
                "sortDescending": ": activate to sort column descending"
            }
        };
    }
}
