document.addEventListener("DOMContentLoaded", function () {
  const urlParams = new URLSearchParams(window.location.search);
  const lang = urlParams.get('lang') || 'en';

  const tableBody = document.getElementById("tableBody");
  if (tableBody) {
    tableBody.style.display = "none";
  }

  const translations = {
    "modal_title": { "th": "รายละเอียด", "en": "Details" },
    "lengthMenu": { "th": "แสดง _MENU_ รายการ", "en": "Show _MENU_ entries" },
    "info": { "th": "แสดง _START_ ถึง _END_ จาก _TOTAL_ รายการ", "en": "Showing _START_ to _END_ of _TOTAL_ entries" },
    "infoEmpty": { "th": "ไม่มีรายการ", "en": "No entries available" },
    "zeroRecords": { "th": "ไม่พบข้อมูล", "en": "No matching records found" },
    "emptyTable": { "th": "ไม่มีข้อมูลในตาราง", "en": "No data available in table" },
    "paginate_first": { "th": "หน้าแรก", "en": "First" },
    "paginate_last": { "th": "หน้าสุดท้าย", "en": "Last" },
    "paginate_next": { "th": "ถัดไป", "en": "Next" },
    "paginate_previous": { "th": "ก่อนหน้า", "en": "Previous" },
    "search": { "th": "ค้นหา:", "en": "Search:" }
  };

  const table = $('#phishingReportsTable').DataTable({
    responsive: false,
    serverSide: false,
    processing: false,
    ajax: null,
    pageLength: 10,
    lengthMenu: [[10, 25, 50, -1], [10, 25, 50, lang === "th" ? "ทั้งหมด" : "All"]],
    order: [],
    dom: "<'row'<'col-12 col-md-6'l><'col-12 col-md-6'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",
    language: {
        lengthMenu: translations["lengthMenu"][lang],
        info: translations["info"][lang],
        infoEmpty: translations["infoEmpty"][lang],
        zeroRecords: translations["zeroRecords"][lang],
        emptyTable: translations["emptyTable"][lang],
        paginate: {
            first: translations["paginate_first"][lang],
            last: translations["paginate_last"][lang],
            next: translations["paginate_next"][lang],
            previous: translations["paginate_previous"][lang]
        },
        search: translations["search"][lang]
    },
    columnDefs: [
      { targets: [0, 2, 3], className: 'text-center' },
      {
        targets: 1,
        render: function (data, type, row) {
          if (type === 'display') {
            try {
              const url = new URL(data);
              return `<p>${url}</p>`;
            } catch (e) {
              return data;
            }
          }
          return data;
        }
      }
    ],
    initComplete: function () {
      const tableBody = document.getElementById("tableBody");
      if (tableBody) {
        tableBody.style.display = "table-row-group";
      }
    }
  });

  $(window).on('resize', function () {
    $('.dataTables_filter input').css('max-width', $(window).width() < 768 ? 'none' : '300px');
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const dataElement = document.getElementById("bubbles-data");
  let bubblesData = [];

  if (dataElement) {
    try {
      bubblesData = JSON.parse(dataElement.value);
    } catch (error) {
      console.error("JSON.parse() Error:", error);
    }
  } else {
    console.error("Element #bubbles-data not found");
  }

  if (bubblesData.length === 0) {
    console.warn("No bubbles data found! Check if Flask is sending data.");
  }

  const mapElement = document.getElementById("world-map");
  if (!mapElement) {
    console.error("Element #world-map not found!");
    return;
  }

  const map = new Datamap({
    element: document.getElementById("world-map"),
    projection: "mercator",
    responsive: true,
    fills: {
      defaultFill: "#1085faed",
      active: "rgba(255, 0, 0, 0.7)",
    },

    geographyConfig: {
      highlightFillColor: "#4e73df",
      popupOnHover: true,
      highlightOnHover: true,
      borderColor: "rgb(255, 255, 255)",
      strokeWidth: 0.5
    },

    bubblesConfig: {
      popupOnHover: true,
      highlightOnHover: true,
      borderWidth: 0,
    },
  });

  if (typeof bubblesData === "string") {
    try {
      bubblesData = JSON.parse(bubblesData);
    } catch (error) {

    }
  }

  bubblesData.forEach(bubble => {
    bubble.latitude = parseFloat(bubble.latitude);
    bubble.longitude = parseFloat(bubble.longitude);
  });

  setTimeout(() => {
    map.bubbles(bubblesData, {
      popupTemplate: function (_geo, data) {
        return `<div class="datamaps-popup">
                          <strong>${data.name}</strong><br>
                          Phishing URLs: ${data.count}
                      </div>`;
      }
    });
  }, 500);

  window.addEventListener("resize", function () {
    map.resize();
  });
});