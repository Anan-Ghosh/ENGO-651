const map = L.map('map').setView([51.505, -0.09], 13);

// Base layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

let drawnPolyline = null;
let simplifiedLine = null;

// Feature group to store drawn items
const drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);

// Draw control
const drawControl = new L.Control.Draw({
  draw: {
    polyline: true,
    polygon: false,
    circle: false,
    rectangle: false,
    marker: false,
    circlemarker: false
  },
  edit: {
    featureGroup: drawnItems,
    edit: false,
    remove: false
  }
});
map.addControl(drawControl);

// Handle draw:created event
map.on(L.Draw.Event.CREATED, function (event) {
  if (drawnPolyline) {
    map.removeLayer(drawnPolyline);
  }
  if (simplifiedLine) {
    map.removeLayer(simplifiedLine);
    simplifiedLine = null;
  }

  drawnPolyline = event.layer;
  drawnItems.addLayer(drawnPolyline);
});

// Simplify button
document.getElementById("simplifyBtn").addEventListener("click", () => {
  if (!drawnPolyline) return alert("Please draw a polyline first!");

  const latlngs = drawnPolyline.getLatLngs();
  const coords = latlngs.map(pt => [pt.lng, pt.lat]);

  const line = turf.lineString(coords);
  const simplified = turf.simplify(line, { tolerance: 0.001, highQuality: false });

  const simplifiedLatLngs = simplified.geometry.coordinates.map(c => [c[1], c[0]]);

  if (simplifiedLine) {
    map.removeLayer(simplifiedLine);
  }

  simplifiedLine = L.polyline(simplifiedLatLngs, { color: 'red' }).addTo(map);
});

// Clear button
document.getElementById("clearBtn").addEventListener("click", () => {
  if (drawnPolyline) {
    map.removeLayer(drawnPolyline);
    drawnPolyline = null;
  }
  if (simplifiedLine) {
    map.removeLayer(simplifiedLine);
    simplifiedLine = null;
  }
  drawnItems.clearLayers();
});
