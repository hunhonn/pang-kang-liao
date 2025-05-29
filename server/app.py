from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
ONEMAP_API_KEY = os.getenv("ONEMAP_API_KEY")

app = Flask(__name__, static_folder='../public', template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

def get_coordinates_from_onemap(address):
    url = "https://www.onemap.gov.sg/api/common/elastic/search"
    headers = {
        "Authorization": f"Bearer {ONEMAP_API_KEY}"  # Use the API key as a Bearer token
    }
    params = {
        'searchVal': address,
        'returnGeom': 'Y',
        'getAddrDetails': 'Y',
        'pageNum': 1
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['found'] > 0:
            location = data['results'][0]
            return float(location['LATITUDE']), float(location['LONGITUDE'])
    return None, None


def get_fastest_route(origin_coords, destination_coords):
    url = "https://www.onemap.gov.sg/api/public/routingsvc/route"
    params = {
        "start": f"{origin_coords[0]},{origin_coords[1]}",  # Latitude,Longitude
        "end": f"{destination_coords[0]},{destination_coords[1]}",  # Latitude,Longitude
        "routeType": "pt",  # Public transport
        "date": datetime.now().strftime("%m-%d-%Y"),  # Current date in MM-DD-YYYY format
        "time": datetime.now().strftime("%H:%M:%S"),  # Current time in HH:MM:SS format
        "mode": "TRANSIT",  # Transit mode
        "maxWalkDistance": 800,  # Maximum walking distance in meters
        "numItineraries": 3  # Number of route options to return
    }
    headers = {
        "Authorization": f"Bearer {ONEMAP_API_KEY}"  # Send the token as a Bearer token in the header
    }
    response = requests.get(url, params=params, headers=headers)
    # print("Request URL:", response.url)  # Log the full request URL
    # print("Response Status Code:", response.status_code)  # Log the status code

    if response.status_code == 200:
        data = response.json()
        # print("Response Data:", data)  # Log the full response data

        if "plan" in data and "itineraries" in data["plan"]:
            # Extract the first itinerary
            itinerary = data["plan"]["itineraries"][0]
            route_geometry = []
            for leg in itinerary["legs"]:
                if "legGeometry" in leg and "points" in leg["legGeometry"]:
                    route_geometry.append(leg["legGeometry"]["points"])
            print("Extracted Route Geometry:", route_geometry)  # Log the extracted route geometry
            return route_geometry  # List of encoded polylines for each leg
        else:
            print("No itineraries found in the response.")
    else:
        print("Error Response:", response.text)  # Log the error response if status code is not 200

    return None

@app.route('/calculate', methods=['POST'])
def calculate():
    print("Headers:", request.headers)
    print("Content-Type:", request.content_type)
    print("Data:", request.data)

    if request.content_type.startswith('application/x-www-form-urlencoded'):
        data = request.form.to_dict()
    elif request.is_json:
        data = request.json
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    # Extract origins and destinations as lists
    origins = data.get('origins', [])
    destinations = data.get('destinations', [])
    time_threshold = int(data.get('time_threshold', 40))

    # Validate that origins and destinations are lists and have the same length
    if not isinstance(origins, list) or not isinstance(destinations, list):
        return jsonify({"error": "Origins and destinations must be lists"}), 400
    if len(origins) != len(destinations):
        return jsonify({"error": "Origins and destinations must have the same number of entries"}), 400

    results = []
    for origin, destination in zip(origins, destinations):
        origin_coords = get_coordinates_from_onemap(origin.strip())
        destination_coords = get_coordinates_from_onemap(destination.strip())
        print(f"Origin Coordinates: {origin_coords}, Destination Coordinates: {destination_coords}")  # Log coordinates

        if origin_coords and destination_coords:
            route_geometry = get_fastest_route(origin_coords, destination_coords)
            print(f"Route Geometry for {origin} to {destination}: {route_geometry}")  # Log route geometry

            results.append({
                "origin": origin_coords,
                "destination": destination_coords,
                "route_geometry": route_geometry  # List of encoded polylines
            })

    print("Final Results:", results)  # Log the final results
    return jsonify(results)

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)