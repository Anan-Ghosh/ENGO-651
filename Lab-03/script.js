$(document).ready(function () {
    let today = moment().format('YYYY-MM-DD');
    let lastMonth = moment().subtract(30, 'days').format('YYYY-MM-DD');

    $('#fromDate').val(lastMonth);
    $('#toDate').val(today);

    // Initialize "From" Date Picker
    $('#fromDate').daterangepicker({
        singleDatePicker: true,
        autoUpdateInput: true,
        locale: { format: 'YYYY-MM-DD' }
    }, function(start) {
        $('#fromDate').val(start.format('YYYY-MM-DD'));

        // Ensure "To" date is not earlier than "From" date
        if (moment($('#toDate').val()).isBefore(start)) {
            $('#toDate').val(start.format('YYYY-MM-DD'));
        }
    });

    // Initialize "To" Date Picker
    $('#toDate').daterangepicker({
        singleDatePicker: true,
        autoUpdateInput: true,
        locale: { format: 'YYYY-MM-DD' }
    }, function(start) {
        $('#toDate').val(start.format('YYYY-MM-DD'));

        // Ensure "From" date is not later than "To" date
        if (moment($('#fromDate').val()).isAfter(start)) {
            $('#fromDate').val(start.format('YYYY-MM-DD'));
        }
    });

    // 🗺 Initialize the Leaflet map inside the ready function
    let map = L.map('map').setView([51.0447, -114.0719], 12);

    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Marker Cluster Group
    let markersCluster = L.markerClusterGroup();
    map.addLayer(markersCluster);

    // Function to fetch permit data
    async function fetchPermitData(startDate, endDate) {
        const apiUrl = `https://data.calgary.ca/resource/c2es-76ed.geojson?$where=issueddate between '${startDate}T00:00:00.000' and '${endDate}T23:59:59.999'`;

        try {
            let response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            let data = await response.json();
            return data;
        } catch (error) {
            alert("Failed to fetch data. Please check your internet connection or try again later.");
            console.error("Error fetching data:", error);
        }
    }

    // Function to plot markers
    function plotMarkers(geojsonData) {
        markersCluster.clearLayers(); // Clear existing markers

        let geoLayer = L.geoJSON(geojsonData, {
            onEachFeature: function (feature, layer) {
                let props = feature.properties;
                let popupContent = `
                    <strong>Issued Date:</strong> ${props.issueddate}<br>
                    <strong>Work Class:</strong> ${props.workclassgroup || 'N/A'}<br>
                    <strong>Contractor:</strong> ${props.contractorname || 'N/A'}<br>
                    <strong>Community:</strong> ${props.communityname || 'N/A'}<br>
                    <strong>Address:</strong> ${props.originaladdress || 'N/A'}
                `;
                layer.bindPopup(popupContent);
            }
        });

        markersCluster.addLayer(geoLayer);
    }

    // Search Button Event
    document.getElementById('searchBtn').addEventListener('click', async function () {
        let startDate = document.getElementById('fromDate').value;
        let endDate = document.getElementById('toDate').value;

        if (startDate && endDate && moment(startDate).isBefore(endDate)) {
            console.log(`Fetching data from ${startDate} to ${endDate}...`);
            let data = await fetchPermitData(startDate, endDate);
            if (data && data.features.length > 0) {
                plotMarkers(data);
            } else {
                alert("No building permits found for the selected date range.");
            }
        } else {
            alert("Please ensure the 'From' date is not later than the 'To' date.");
        }
    });

});
