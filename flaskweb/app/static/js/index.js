// DataTable initialization removed - handled inline in index.html with server-side processing

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
      phishing: "rgba(255, 0, 0, 0.9)" // สีแดงสำหรับจุด Bubbles
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
    bubble.fillKey = "phishing"; // บังคับให้ใช้สีแดง
  });

  // Filter out invalid coordinates to prevent D3 errors
  bubblesData = bubblesData.filter(b => !isNaN(b.latitude) && !isNaN(b.longitude));

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