from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import polyline
import math

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
    all_routes = []

    for origin, destination in zip(origins, destinations):
        origin_coords = get_coordinates_from_onemap(origin.strip())
        destination_coords = get_coordinates_from_onemap(destination.strip())
        print(f"Origin Coordinates: {origin_coords}, Destination Coordinates: {destination_coords}")  # Log coordinates

        if origin_coords and destination_coords:
            route_geometry = get_fastest_route(origin_coords, destination_coords)
            if route_geometry:
                # Decode the route geometry for this origin-destination pair
                decoded_route = []
                for encoded_polyline in route_geometry:
                    decoded_route.extend(polyline.decode(encoded_polyline))  # Decode and combine all legs
                all_routes.append(decoded_route)  # Add the decoded route to the list

                results.append({
                    "origin": origin_coords,
                    "destination": destination_coords,
                    "route_geometry": route_geometry,  # List of encoded polylines
                })

    # Find the closest points among all routes
    closest_points, min_distance = find_closest_points_among_routes(all_routes)

    return jsonify({
        "results": results,
        "closest_points": closest_points,  # Pair of closest points
        "min_distance": min_distance  # Distance between the closest points
    })

def find_closest_points_among_routes(all_routes):
    """
    Find the closest point among multiple routes using Euclidean distance.
    :param all_routes: List of routes, where each route is a list of (latitude, longitude) points.
    :return: Closest point pair ((lat1, lon1), (lat2, lon2)) and the minimum distance.
    """
    min_distance = float('inf')
    closest_points = None

    # Flatten all points into a single list with route identifiers
    all_points = []
    for route_index, route in enumerate(all_routes):
        for point in route:
            all_points.append((route_index, point))  # Keep track of which route the point belongs to

    # Compare every point with every other point
    for i, (route1_index, point1) in enumerate(all_points):
        for j, (route2_index, point2) in enumerate(all_points):
            # Skip comparison if points are from the same route
            if route1_index == route2_index:
                continue

            # Calculate Euclidean distance
            distance = math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
            if distance < min_distance:
                min_distance = distance
                closest_points = (point1, point2)

    return closest_points, min_distance

def get_nearby_places(central_point):
    url = "https://www.onemap.gov.sg/api/common/elastic/reversegeocode"
    params = {
        "location": f"{central_point[1]},{central_point[0]}",  # Longitude,Latitude
        "buffer": 500,  # Search within 500 meters
        "addressType": "All",
        "otherFeatures": "Y"
    }
    headers = {
        "Authorization": f"Bearer {ONEMAP_API_KEY}"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        # Extract up to 5 nearby places
        return [
            {
                "name": place.get("SEARCHVAL"),
                "latitude": float(place.get("LATITUDE")),
                "longitude": float(place.get("LONGITUDE"))
            }
            for place in data.get("GeocodeInfo", [])[:5]
        ]
    return []

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    app.run(debug=True)