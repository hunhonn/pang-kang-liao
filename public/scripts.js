// This file contains JavaScript code that handles client-side logic, such as form submission and processing the response from the server.

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('route-form');
    
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        
        const origins = document.getElementById('origins').value.split(',');
        const destinations = document.getElementById('destinations').value.split(',');
        const timeThreshold = document.getElementById('time-threshold').value;


        fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                origins: origins.map(origin => origin.trim()),
                destinations: destinations.map(destination => destination.trim()),
                time_threshold: timeThreshold
            }),
        })
        .then(response => response.json())
        .then(data => {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '';

            if (data.success) {
                data.routes.forEach(route => {
                    const routeElement = document.createElement('div');
                    routeElement.textContent = `Route: ${route}`;
                    resultDiv.appendChild(routeElement);
                });
            } else {
                resultDiv.textContent = 'No routes found within the specified time threshold.';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('location-form');
    const addPairButton = document.getElementById('add-pair');
    const pairsContainer = document.getElementById('origin-destination-pairs');
    const map = L.map('map').setView([1.3521, 103.8198], 12); // Centered on Singapore

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    let pairCount = 1;
    let routeLayers = []; // Store route layers to clear them later

    // Function to fetch suggestions from OneMap API
    async function fetchSuggestions(query) {
        const url = `https://www.onemap.gov.sg/api/common/elastic/search?searchVal=${query}&returnGeom=Y&getAddrDetails=Y&pageNum=1`;
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();
            return data.results.map((result) => result.SEARCHVAL);
        }
        return [];
    }

    // Function to update datalist with suggestions
    async function updateSuggestions(input, datalistId) {
        const query = input.value.trim();
        if (query.length > 2) {
            const suggestions = await fetchSuggestions(query);
            const datalist = document.getElementById(datalistId);
            datalist.innerHTML = '';
            suggestions.forEach((suggestion) => {
                const option = document.createElement('option');
                option.value = suggestion;
                datalist.appendChild(option);
            });
        }
    }

    // Add event listeners for input fields
    pairsContainer.addEventListener('input', function (event) {
        if (event.target.tagName === 'INPUT' && event.target.list) {
            updateSuggestions(event.target, event.target.list.id);
        }
    });

    // Add a new origin-destination pair
    addPairButton.addEventListener('click', function () {
        const pairDiv = document.createElement('div');
        pairDiv.classList.add('pair');
        pairDiv.innerHTML = `
            <label for="origin-${pairCount}">Origin:</label>
            <input type="text" id="origin-${pairCount}" name="origins" list="origin-suggestions-${pairCount}" autocomplete="off" required>
            <datalist id="origin-suggestions-${pairCount}"></datalist>
            <label for="destination-${pairCount}">Destination:</label>
            <input type="text" id="destination-${pairCount}" name="destinations" list="destination-suggestions-${pairCount}" autocomplete="off" required>
            <datalist id="destination-suggestions-${pairCount}"></datalist>
            <button type="button" class="delete-pair">X</button>
        `;
        pairsContainer.appendChild(pairDiv);
        pairCount++;
    });

    // Handle deletion of a pair
    pairsContainer.addEventListener('click', function (event) {
        if (event.target.classList.contains('delete-pair')) {
            const pairDiv = event.target.closest('.pair');
            pairDiv.remove();
        }
    });

    const routeColors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'yellow'];

    // Handle form submission
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        const origins = Array.from(document.querySelectorAll('input[name="origins"]')).map((input) => input.value.trim());
        const destinations = Array.from(document.querySelectorAll('input[name="destinations"]')).map((input) => input.value.trim());
        const timeThreshold = document.getElementById('time-threshold').value;

        fetch('/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                origins,
                destinations,
                time_threshold: timeThreshold,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                // Clear previous routes
                routeLayers.forEach((layer) => map.removeLayer(layer));
                routeLayers = [];
    
                data.forEach((result, index) => {
                    const { origin, destination, route_geometry } = result;
    
                    // Add markers for origin and destination
                    const originMarker = L.marker([origin[0], origin[1]]).addTo(map).bindPopup(`Origin ${index + 1}`).openPopup();
                    const destinationMarker = L.marker([destination[0], destination[1]]).addTo(map).bindPopup(`Destination ${index + 1}`).openPopup();
    
                    // Get the color for this route
                    const routeColor = routeColors[index % routeColors.length];
    
                    // Decode and draw each leg of the route
                    if (route_geometry) {
                        route_geometry.forEach((encodedPolyline) => {
                            // Decode the encoded polyline
                            const decodedPolyline = polyline.decode(encodedPolyline);
    
                            // Add the decoded polyline to the map with the assigned color
                            const route = L.polyline(decodedPolyline, {
                                color: routeColor,
                                weight: 4,
                            }).addTo(map);
    
                            routeLayers.push(route);
                        });
                    }
    
                    routeLayers.push(originMarker, destinationMarker);
                });
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    });
});