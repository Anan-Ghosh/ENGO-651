let client = null;
let isConnected = false;

let map = L.map("map", {
  zoomAnimation: true,
  zoomControl: true,
  fadeAnimation: true
}).setView([0, 0], 2);

L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
  attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
  subdomains: "abcd",
  maxZoom: 19
}).addTo(map);

let marker = null;

const startBtn = document.getElementById("startBtn");
const endBtn = document.getElementById("endBtn");
const statusText = document.getElementById("status");
const hostInput = document.getElementById("host");
const portInput = document.getElementById("port");

function startConnection() {
  if (isConnected) return;

  const host = hostInput.value;
  const port = parseInt(portInput.value);
  if (!host || !port) {
    alert("Please enter a valid host and port.");
    return;
  }

  const clientId = "clientId-" + Math.random().toString(16).substr(2, 8);
  client = new Paho.MQTT.Client(host, port, clientId);

  client.onConnectionLost = onConnectionLost;
  client.onMessageArrived = onMessageArrived;

  client.connect({
    onSuccess: onConnect,
    onFailure: err => {
      console.error("Connection failed:", err.errorMessage);
      statusText.textContent = "Connection failed.";
      statusText.className = "red";
    },
    useSSL: false
  });

  statusText.textContent = "Connecting...";
  statusText.className = "orange";
}

function onConnect() {
  isConnected = true;
  statusText.textContent = "Connected to broker";
  statusText.className = "green";
  client.subscribe("engo651/Anan_Ghosh/my_temperature");

  hostInput.disabled = true;
  portInput.disabled = true;
  startBtn.disabled = true;
  endBtn.disabled = false;
}

function onConnectionLost(response) {
  isConnected = false;
  statusText.textContent = "Disconnected. Reconnecting...";
  statusText.className = "red";
  setTimeout(() => {
    if (client && !isConnected) startConnection();
  }, 3000);
}

function onMessageArrived(message) {
  try {
    const payload = JSON.parse(message.payloadString);
    const coords = payload.geometry.coordinates;
    const temperature = payload.properties.temperature;

    let color = "blue";
    if (temperature >= 10 && temperature < 30) color = "green";
    else if (temperature >= 30) color = "red";

    const customIcon = L.icon({
      iconUrl: getColoredMarkerIcon(color),
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34]
    });

    if (marker) {
      marker.setLatLng([coords[1], coords[0]]);
      marker.setPopupContent(`🌡 Temperature: ${temperature} °C`);
      marker.setIcon(customIcon);
    } else {
      marker = L.marker([coords[1], coords[0]], { icon: customIcon })
        .addTo(map)
        .bindPopup(`🌡 Temperature: ${temperature} °C`);
    }

    map.setView([coords[1], coords[0]], 14);
    marker.openPopup();

    // Add bounce animation
    if (marker._icon) {
      marker._icon.classList.add("leaflet-marker-bounce");
      setTimeout(() => marker._icon.classList.remove("leaflet-marker-bounce"), 600);
    }
  } catch (e) {
    console.error("Error processing message:", e);
  }
}

function getColoredMarkerIcon(color) {
  const colors = {
    blue: "https://maps.gstatic.com/mapfiles/ms2/micons/blue-dot.png",
    green: "https://maps.gstatic.com/mapfiles/ms2/micons/green-dot.png",
    red: "https://maps.gstatic.com/mapfiles/ms2/micons/red-dot.png",
  };
  return colors[color] || colors.blue;
}

function endConnection() {
  if (client && isConnected) {
    client.disconnect();
    isConnected = false;
    statusText.textContent = "Disconnected";
    statusText.className = "";
    hostInput.disabled = false;
    portInput.disabled = false;
    startBtn.disabled = false;
    endBtn.disabled = true;
  }
}

function publishMessage() {
  if (!isConnected) return alert("Connect to the broker first.");
  const topic = document.getElementById("topic").value;
  const msg = document.getElementById("message").value;
  if (!topic || !msg) return alert("Topic and message are required.");
  const message = new Paho.MQTT.Message(msg);
  message.destinationName = topic;
  client.send(message);
  alert("Message published!");
}

function shareStatus() {
  if (!isConnected) return alert("Connect to the broker first.");
  if (!navigator.geolocation) return alert("Geolocation not supported.");

  navigator.geolocation.getCurrentPosition(
    sendStatusAsGeoJSON,
    (error) => {
      console.error("Geolocation error:", error.code, error.message);
      alert(`Geolocation error [${error.code}]: ${error.message}`);
    }
  );
}

function sendStatusAsGeoJSON(position) {
  const latitude = position.coords.latitude;
  const longitude = position.coords.longitude;
  const temperature = (Math.random() * 60 - 10).toFixed(2);

  const geojson = {
    type: "Feature",
    geometry: {
      type: "Point",
      coordinates: [longitude, latitude]
    },
    properties: {
      temperature: parseFloat(temperature)
    }
  };

  const topic = "engo651/Anan_Ghosh/my_temperature";
  const message = new Paho.MQTT.Message(JSON.stringify(geojson));
  message.destinationName = topic;
  client.send(message);
  alert("Status shared with temperature: " + temperature + " °C");
}

startBtn.addEventListener("click", startConnection);
endBtn.addEventListener("click", endConnection);
