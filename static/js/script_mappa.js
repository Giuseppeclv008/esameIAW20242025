document.addEventListener('DOMContentLoaded', function () {
    console.log("Attempting to initialize Leaflet map...");

    if (typeof L === 'undefined') {
        console.error('Leaflet (L) is not loaded! Check the script tag in base_festival.html.');
        return;
    }

    const mapElement = document.getElementById('festivalMap');
    if (!mapElement) {
        console.error('Map container #festivalMap not found in the HTML!');
        return;
    }


    const mapHeight = window.getComputedStyle(mapElement).getPropertyValue('height');
    console.log("Computed map container height:", mapHeight);
    if (mapHeight === "0px") {
        console.warn("ATTENZIONE: L'altezza del contenitore della mappa è 0px. La mappa non sarà visibile. Controlla il CSS (.festival-map-container)!");
    }

    try {

        const festivalLocation = [40.40430332101493, 18.20090042806457]; // Coordinate del Festival Del Tacco
        const map = L.map('festivalMap').setView(festivalLocation, 14); // Il secondo numero è il livello di zoom

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        L.marker(festivalLocation).addTo(map)
            .bindPopup('<b>Festival Del Tacco</b><br>Ti aspettiamo qui!')
            .openPopup();
        console.log('Leaflet map initialized successfully.');
    } catch (e) {
        console.error('Error initializing Leaflet map:', e);
    }
});