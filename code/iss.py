from flask import Flask, render_template, jsonify, request
import requests
import time

app = Flask(__name__)

trajectory = []

def fetch_iss_location():
    api_url = "https://api.wheretheiss.at/v1/satellites/25544"
    try:
        response = requests.get(api_url)
        if  response.status_code == 200:
            data = response.json()
            latitude = data['latitude']
            longitude = data['longitude']
            altitude = data['altitude']
            visibility = data['visibility']
            return latitude, longitude, altitude, visibility
        return None, None, None, None
    except Exception:
        return None, None, None, None

@app.route("/iss_data")
def iss_data():
    latitude, longitude, altitude, visibility = fetch_iss_location()
    if latitude is not None and longitude is not None:
        trajectory.append([latitude, longitude])
        return jsonify(
            {
                "latitude": latitude,
                "longitude": longitude,
                "altitude": altitude,
                "visibility": visibility,
                "trajectory": trajectory
            }
        )
    return jsonify({"error": "No data available"})

@app.route("/iss_trajectory")
def iss_trajectory():
    future_path = fetch_iss_future_path()
    return jsonify({"trajectory": future_path})

def fetch_iss_future_path():
    api_url = "https://api.wheretheiss.at/v1/satellites/25544/positions?timestamps="
    timestamps = ",".join([str(int(time.time()) + (i * 90)) for i in range(1, 21)])
    try:
        response = requests.get(api_url + timestamps)
        if response.status_code == 200:
            data = response.json()
            return [{"lat": d["latitude"], "lon": d["longitude"]} for d in data if "latitude" in d and "longitude" in d]
        return []
    except Exception:
        return []
    
@app.route("/iss_alerts")
def iss_alerts():
    user_lat = request.args.get("lat", type=float)
    user_lon = request.args.get("lon", type=float)

    if user_lat is None or user_lon is None:
        return jsonify({"error": "Invalid coordinates"}), 400
    
    latitude, longitude, altitude, visibility = fetch_iss_location()

    if latitude is not None and longitude is not None:
        if abs(latitude - user_lat) < 5 and abs(longitude - user_lon) < 5 and visibility == "daylight":
            return jsonify({"alert": True, "message": "🚀 The ISS is currently visible overhead!"})
        else:
            return jsonify({"alert": False, "message": "The ISS is not currently visible from your location."})
    return jsonify({"error": "Could not fetch ISS data"})

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")