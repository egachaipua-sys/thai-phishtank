document.addEventListener('DOMContentLoaded', function () {
    console.log("DOMContentLoaded event fired. Script started.");

    const table = document.getElementById('reportsTable');
    if (!table) {
        console.error("Error: The table with ID 'reportsTable' was not found.");
        return;
    }

    const tbody = table.querySelector('tbody');
    const searchInput = document.getElementById('searchInput');
    const lang = document.documentElement.lang || 'en';

    const allRows = tbody ? Array.from(tbody.querySelectorAll('tr')) : [];
    console.log(`Found a total of ${allRows.length} rows in the table.`);

    const entriesPerPage = 25;
    let currentPage = 1;
    let currentFilteredAndSortedRows = [...allRows];
    let currentSort = { column: null, direction: 'asc' };

    const translations = {
        title: { "th": "การจัดการสมาชิก", "en": "Member Management" },
        search_placeholder: { "th": "ค้นหารายการ...", "en": "Search entries..." },
        no: { "th": "ไม่", "en": "No" },
        yes: { "th": "ใช่", "en": "Yes" },
        showing: { "th": "กำลังแสดง", "en": "Showing" },
        to: { "th": "ถึง", "en": "to" },
        of: { "th": "จาก", "en": "of" },
        entries: { "th": "รายการ", "en": "entries" },
        prev: { "th": "ก่อนหน้า", "en": "Previous" },
        next: { "th": "ถัดไป", "en": "Next" },
        processing_title: { "th": "กำลังประมวลผล...", "en": "Processing..." },
        processing_text: { "th": "กรุณารอสักครู่", "en": "Please wait..." },
        success_title: { "th": "สำเร็จ", "en": "Success" },
        error_title: { "th": "เกิดข้อผิดพลาด", "en": "Error" },
        error_text: { "th": "ไม่สามารถดำเนินการตามคำขอได้", "en": "Could not process the request." },
        no_results_found: { "th": "ไม่พบข้อมูลที่ตรงกัน", "en": "No matching records found" },
        confirm_add: { "th": "คุณแน่ใจหรือไม่ว่าต้องการเพิ่มสมาชิกนี้?", "en": "Are you sure you want to add this member?" },
        confirm_delete: { "th": "คุณแน่ใจหรือไม่ว่าต้องการลบผู้ใช้นี้?", "en": "Are you sure you want to delete this user?" },
        confirm_button: { "th": "ยืนยัน", "en": "Confirm" },
        cancel_button: { "th": "ยกเลิก", "en": "Cancel" }
    };

    function translate(key) {
        return translations[key]?.[lang] || key;
    }

    function updateTableView() {
        console.log("updateTableView() called.");
        const searchTerm = searchInput.value.trim().toLowerCase();

        let processedRows = allRows.filter(row => {
            if (!searchTerm) return true;
            const cells = row.querySelectorAll('td');
            return Array.from(cells).some(cell =>
                cell.textContent.toLowerCase().includes(searchTerm)
            );
        });

        if (currentSort.column !== null) {
            processedRows.sort((a, b) => {
                const aText = a.children[currentSort.column].textContent.trim();
                const bText = b.children[currentSort.column].textContent.trim();
                const sortType = document.querySelector(`th.sortable:nth-child(${currentSort.column + 1})`).dataset.sort;
                let comparison;

                if (sortType === 'number') {
                    comparison = parseInt(aText) - parseInt(bText);
                } else if (sortType === 'date') {
                    const parseDate = (text) => {
                        const parts = text.split(" ");
                        if (parts.length < 2) return new Date(0);
                        const [datePart, timePart] = parts;
                        const [day, month, year] = datePart.split("/");
                        const [hour, minute] = timePart.split(":");
                        return new Date(`${year}-${month}-${day}T${hour}:${minute}`);
                    };
                    comparison = parseDate(aText) - parseDate(bText);
                } else {
                    comparison = aText.localeCompare(bText, undefined, { numeric: true, sensitivity: 'base' });
                }

                return currentSort.direction === 'asc' ? comparison : -comparison;
            });
        }

        currentFilteredAndSortedRows = processedRows;
        console.log(`Finished filtering and sorting. Found ${currentFilteredAndSortedRows.length} matching rows.`);
        displayPage(1);
    }

    function displayPage(page) {
        console.log(`displayPage() called for page ${page}.`);
        currentPage = page;
        const totalRows = currentFilteredAndSortedRows.length;
        const start = (page - 1) * entriesPerPage;
        const end = start + entriesPerPage;

        allRows.forEach(row => (row.style.display = 'none'));

        const existingNoResultsRow = tbody.querySelector('.no-results-row');
        if (existingNoResultsRow) existingNoResultsRow.remove();

        if (totalRows === 0) {
            console.log("No matching rows found. Displaying 'no results' message.");
            const noResultsRow = tbody.insertRow();
            noResultsRow.classList.add('no-results-row');
            const cell = noResultsRow.insertCell();
            cell.colSpan = table.querySelector('thead tr').children.length;
            cell.textContent = translate('no_results_found');
            cell.style.textAlign = 'center';
            cell.style.padding = '1rem';
        } else {
            console.log(`Displaying rows from index ${start} to ${end}.`);
            currentFilteredAndSortedRows.slice(start, end).forEach(row => {
                row.style.display = '';
            });
        }

        updatePaginationControls(page, totalRows);
        updateInfoText(start, end, totalRows);
        updateSelectAllCheckboxState();
    }

    function updatePaginationControls(currentPage, totalRows) {
        const paginationUl = document.querySelector('#pagination ul');
        if (!paginationUl) {
            console.warn("Warning: Pagination UL element not found.");
            return;
        }
        const totalPages = Math.ceil(totalRows / entriesPerPage);

        paginationUl.innerHTML = '';
        if (totalPages <= 1) return;

        let pageItems = [];
        const maxVisibleButtons = 7;

        pageItems.push(
            `<li class="paginate_button page-item ${currentPage === 1 ? 'disabled' : ''}" data-page="${currentPage - 1}">
                <a href="#" class="page-link">${translate('prev')}</a>
            </li>`
        );

        if (totalPages <= maxVisibleButtons) {
            for (let i = 1; i <= totalPages; i++) {
                pageItems.push(
                    `<li class="paginate_button page-item ${i === currentPage ? 'active' : ''}" data-page="${i}">
                        <a href="#" class="page-link">${i}</a>
                    </li>`
                );
            }
        } else {
            let startPage, endPage;
            if (currentPage <= Math.ceil(maxVisibleButtons / 2)) {
                startPage = 1;
                endPage = maxVisibleButtons - 2;
            } else if (currentPage + Math.floor(maxVisibleButtons / 2) >= totalPages) {
                startPage = totalPages - (maxVisibleButtons - 3);
                endPage = totalPages;
            } else {
                startPage = currentPage - Math.floor((maxVisibleButtons - 4) / 2);
                endPage = currentPage + Math.ceil((maxVisibleButtons - 5) / 2);
            }

            pageItems.push(
                `<li class="paginate_button page-item ${1 === currentPage ? 'active' : ''}" data-page="1">
                    <a href="#" class="page-link">1</a>
                </li>`
            );

            if (startPage > 2) {
                pageItems.push(
                    `<li class="paginate_button page-item disabled">
                        <a href="#" class="page-link">...</a>
                    </li>`
                );
            }

            for (let i = startPage; i <= endPage; i++) {
                if (i > 1 && i < totalPages) {
                    pageItems.push(
                        `<li class="paginate_button page-item ${i === currentPage ? 'active' : ''}" data-page="${i}">
                            <a href="#" class="page-link">${i}</a>
                        </li>`
                    );
                }
            }

            if (endPage < totalPages - 1) {
                pageItems.push(
                    `<li class="paginate_button page-item disabled">
                        <a href="#" class="page-link">...</a>
                    </li>`
                );
            }

            pageItems.push(
                `<li class="paginate_button page-item ${totalPages === currentPage ? 'active' : ''}" data-page="${totalPages}">
                    <a href="#" class="page-link">${totalPages}</a>
                </li>`
            );
        }

        pageItems.push(
            `<li class="paginate_button page-item ${currentPage === totalPages ? 'disabled' : ''}" data-page="${currentPage + 1}">
                <a href="#" class="page-link">${translate('next')}</a>
            </li>`
        );

        paginationUl.innerHTML = pageItems.join('');
    }

    function updateInfoText(start, end, total) {
        document.getElementById('showingStart').textContent = total > 0 ? start + 1 : 0;
        document.getElementById('showingEnd').textContent = Math.min(end, total);
        document.getElementById('totalEntries').textContent = total;
    }

    const selectAllCheckbox = document.getElementById("selectAllCheckbox");
    const memberCheckboxes = document.querySelectorAll(".report-checkbox");
    const addSelectedBtn = document.getElementById("addSelectedBtn");
    const deleteSelectedBtn = document.getElementById("deleteSelectedBtn");

    if (!selectAllCheckbox) {
        console.warn("Warning: 'Select All' checkbox with ID 'selectAllCheckbox' not found. Bulk actions will not work.");
    }
    if (memberCheckboxes.length === 0) {
        console.warn("Warning: No checkboxes with class 'report-checkbox' found. Bulk actions will not work.");
    }

    function updateSelectedButtons() {
        const anyCheckboxChecked = Array.from(memberCheckboxes).some(cb => cb.checked);
        if (addSelectedBtn) addSelectedBtn.disabled = !anyCheckboxChecked;
        if (deleteSelectedBtn) deleteSelectedBtn.disabled = !anyCheckboxChecked;
    }

    function updateSelectAllCheckboxState() {
        const visibleCheckboxes = Array.from(memberCheckboxes).filter(cb => cb.closest('tr').style.display !== 'none');
        if (selectAllCheckbox) {
             if (visibleCheckboxes.length > 0) {
                selectAllCheckbox.checked = visibleCheckboxes.every(cb => cb.checked);
            } else {
                selectAllCheckbox.checked = false;
            }
        }
    }

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener("change", () => {
            const isChecked = selectAllCheckbox.checked;
            Array.from(memberCheckboxes).forEach(checkbox => {
                if (checkbox.closest('tr').style.display !== 'none') {
                    checkbox.checked = isChecked;
                }
            });
            updateSelectedButtons();
        });
    }


    memberCheckboxes.forEach(checkbox => {
        checkbox.addEventListener("change", () => {
            updateSelectedButtons();
            updateSelectAllCheckboxState();
        });
    });

    if (addSelectedBtn) {
        addSelectedBtn.addEventListener("click", () => {
            const selectedIds = Array.from(memberCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.dataset.id);
            if (selectedIds.length === 0) return;

            Swal.fire({
                title: translate("confirm_add"),
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: translate("confirm_button"),
                cancelButtonText: translate("cancel_button")
            }).then((result) => {
                if (result.isConfirmed) {
                    Swal.fire({
                        title: translate("processing_title"),
                        text: translate("processing_text"),
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        didOpen: () => Swal.showLoading(),
                    });
                    fetch("members/bulk-add", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ ids: selectedIds }),
                    })
                    .then(res => res.json())
                    .then(data => {
                        Swal.fire({
                            icon: data.success ? "success" : "error",
                            title: data.success ? translate("success_title") : translate("error_title"),
                            text: data.message,
                        }).then(() => data.success && location.reload());
                    })
                    .catch(() => Swal.fire({
                        icon: "error",
                        title: translate("error_title"),
                        text: translate("error_text"),
                    }));
                }
            });
        });
    }

    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener("click", () => {
            const selectedIds = Array.from(memberCheckboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.dataset.id);
            if (selectedIds.length === 0) return;

            Swal.fire({
                title: translate("confirm_delete"),
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: translate("confirm_button"),
                cancelButtonText: translate("cancel_button")
            }).then((result) => {
                if (result.isConfirmed) {
                    Swal.fire({
                        title: translate("processing_title"),
                        text: translate("processing_text"),
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        didOpen: () => Swal.showLoading(),
                    });
                    fetch("members/bulk-delete", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ ids: selectedIds }),
                    })
                    .then(res => res.json())
                    .then(data => {
                        Swal.fire({
                            icon: data.success ? "success" : "error",
                            title: data.success ? translate("success_title") : translate("error_title"),
                            text: data.message,
                        }).then(() => data.success && location.reload());
                    })
                    .catch(() => Swal.fire({
                        icon: "error",
                        title: translate("error_title"),
                        text: translate("error_text"),
                    }));
                }
            });
        });
    }

    if (searchInput) {
        searchInput.placeholder = translate('search_placeholder');
        searchInput.addEventListener('input', updateTableView);
    }

    document.querySelectorAll('th.sortable').forEach((header, index) => {
        header.addEventListener('click', function () {
            if (currentSort.column === index) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = index;
                currentSort.direction = 'asc';
            }
            document.querySelectorAll('th.sortable').forEach(h => h.classList.remove('sorted-asc', 'sorted-desc'));
            this.classList.add(`sorted-${currentSort.direction}`);
            updateTableView();
        });
    });

    document.querySelector('#pagination ul').addEventListener('click', (e) => {
        e.preventDefault();
        const target = e.target.closest('.paginate_button');
        if (target && !target.classList.contains('disabled') && !target.classList.contains('active')) {
            displayPage(parseInt(target.dataset.page));
        }
    });

    if (tbody) {
        tbody.style.display = '';
        updateTableView();
    }
});