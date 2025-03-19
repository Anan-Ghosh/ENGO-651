$(document).ready(function () {
    let today = moment().format('YYYY-MM-DD');
    let lastMonth = moment().subtract(30, 'days').format('YYYY-MM-DD');
    $('#fromDate').val(lastMonth);
    $('#toDate').val(today);

    $('#fromDate, #toDate').daterangepicker({
        singleDatePicker: true,
        autoUpdateInput: true,
        locale: { format: 'YYYY-MM-DD' }
    });

    let map = L.map('map').setView([51.0447, -114.0719], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let markersCluster = L.markerClusterGroup();
    map.addLayer(markersCluster);

    let mapboxLayer = L.tileLayer('https://api.mapbox.com/styles/v1/ananghosh/cm8g7h5jh011o01r033nz4p7h/tiles/{z}/{x}/{y}?access_token=pk.eyJ1IjoiYW5hbmdob3NoIiwiYSI6ImNtOGczMTN4ODBoeHAyc290cnZrOGR5a2gifQ.Co_L4QQ2-re2dIcRBQPgsA', {
        tileSize: 512,
        zoomOffset: -1
    });
    let isMapboxLayerAdded = false;

    $('#toggleMapbox').click(function () {
        if (isMapboxLayerAdded) {
            map.removeLayer(mapboxLayer);
        } else {
            map.addLayer(mapboxLayer);
        }
        isMapboxLayerAdded = !isMapboxLayerAdded;
    });

    async function fetchPermitData(startDate, endDate) {
        const apiUrl = `https://data.calgary.ca/resource/c2es-76ed.geojson?$where=issueddate between '${startDate}T00:00:00.000' and '${endDate}T23:59:59.999'`;
        try {
            let response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            return await response.json();
        } catch (error) {
            alert("Failed to fetch data. Please try again later.");
            console.error("Error fetching data:", error);
        }
    }

    function plotMarkers(geojsonData) {
        markersCluster.clearLayers();
        let geoLayer = L.geoJSON(geojsonData, {
            pointToLayer: function (feature, latlng) {
                let description = feature.properties.DESCRIPTION || "Unknown";
                return L.circleMarker(latlng, {
                    radius: 8,
                    fillColor: "#ff0000",
                    color: "#000",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                });
            },
            onEachFeature: function (feature, layer) {
                let props = feature.properties;
                let popupContent = `
                    <strong>Issued Date:</strong> ${props.issueddate || 'N/A'}<br>
                    <strong>Work Class:</strong> ${props.workclassgroup || 'N/A'}<br>
                    <strong>Community:</strong> ${props.communityname || 'N/A'}<br>
                    <strong>Address:</strong> ${props.originaladdress || 'N/A'}
                `;
                layer.bindPopup(popupContent);
            }
        });
        markersCluster.addLayer(geoLayer);
    }

    $('#searchBtn').click(async function () {
        let startDate = $('#fromDate').val();
        let endDate = $('#toDate').val();
        if (!moment(startDate).isBefore(endDate)) {
            alert("Please ensure the 'From' date is earlier than the 'To' date.");
            return;
        }
        let data = await fetchPermitData(startDate, endDate);
        if (data && data.features.length > 0) {
            plotMarkers(data);
        } else {
            alert("No building permits found for the selected date range.");
        }
    });
});
