"""
Routes and views for the flask application.
"""

from datetime import datetime # import datetime to get the current data and time
from flask import render_template # render template is used to serve the HTML templates; jsonify returns the JSON responses
from Project5 import app #import Flask app instance from the Project package
# home
@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )
# contact
@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

import random # used for random weather and aircraft behaviour
from flask import jsonify # a placeholder for API use


import requests
# hardcoded aircraft data, contains starting positions, states, altitudes etc
sim_aircraft = [
    {
        "call_sign": "HZ123",
        "lat": 51.790,
        "lon": -1.180,
        "altitude": 0,
        "type": "Boeing 737",
        "status": "stationary",
        "route": [(51.792, -1.182), (51.795, -1.185), (51.798, -1.188)]
    },
    {
        "call_sign": "HZ899",
        "lat": 51.800,
        "lon": -1.200,
        "altitude": 0,
        "type": "Airbus A320",
        "status": "stationary",
        "route": [(51.802, -1.202), (51.805, -1.205), (51.808, -1.208)]
    },
    {
        "call_sign": "HZ456",
        "lat": 51.850,
        "lon": -1.100,
        "altitude": 6000,
        "type": "DRONE1",
        "status": "flying",
        "route": []
    },
    {
        "call_sign": "HZ789",
        "lat": 51.750,
        "lon": -1.300,
        "altitude": 4000,
        "type": "MILJET",
        "status": "flying",
        "route": []
    },
    {
        "call_sign": "HZRANDOM", # dummy plane for testing
        "lat": 51.808,
        "lon": -1.250,
        "altitude": 3500,
        "type": "TESTERJET",
        "status": "flying",
        "route": []
    }
]

# helper function to simulate aircraft movement towards a waypoint
def move_toward(plane, target, speed=0.0005):
    if abs(plane["lat"] - target[0]) > speed: #adjusts latitude and longitude incrementally based on the direction
        plane["lat"] += speed if plane["lat"] < target[0] else -speed
    if abs(plane["lon"] - target[1]) > speed:
        plane["lon"] += speed if plane["lon"] < target[1] else -speed # "speed" is a float value that determines how far to move per update

        # determines if an aircraft has reached its target, true is returned if lat and lon are within a small threshold
def reached(plane, target, threshold=0.0003):
    return abs(plane["lat"] - target[0]) < threshold and abs(plane["lon"] - target[1]) < threshold

import random
# hardcoded weather data, updated per request
current_weather = {
    "condition": "clear",  # could be: clear, wind, snow, fog
    "caution_level": "low"  # low, moderate, high
}
# randomly update the weather conditions, with a changing caution level
from time import time

last_weather_update = 0 # global variable to trach the weather update time
def update_weather():
    global last_weather_update #access to global variable
    if time() - last_weather_update < 30: # if the last update was less than 30 seconds ago
        return # DONT update weather
    last_weather_update = time()
    condition = random.choice(["clear", "wind", "snow", "fog"]) # selects through these random weather conditions
    if condition == "clear":
        caution = "low"
    elif condition == "wind":
        caution = random.choice(["moderate", "high"])
    elif condition == "snow":
        caution = random.choice(["moderate", "high"])
    elif condition == "fog":
        caution = random.choice(["moderate", "high"])
    current_weather["condition"] = condition
    current_weather["caution_level"] = caution

#main endpoint that updates the weather and aircraft positions, (also routing, conflict detection)
@app.route("/hzia")
def custom_airport():
    update_weather() #update the weather conditions
    for plane in sim_aircraft:
        if plane["status"] == "stationary": # if the plane is seen as stationary
            continue # the plane stays on the ground

        elif plane["status"] == "taxi":
            if plane["route"]:
                target = plane["route"][0] # get the next waypoint
                move_toward(plane, target, speed=0.0002)
                if reached(plane, target):
                    plane["route"].pop(0) #remove the target from the route
                    if not plane["route"]:
                        plane["status"] = "takeoff" #change the status to takeoff if the plane is not on route yet
            plane["altitude"] = 0 #the plane is still on the ground

        elif plane["status"] == "takeoff":
            plane["altitude"] += 300
            if plane["altitude"] >= 1000:
                plane["status"] = "flying"

        elif plane["status"] == "flying":
            plane["lat"] += random.uniform(-0.001, 0.001) #latitude changes
            plane["lon"] += random.uniform(-0.001, 0.001) #the plane is now flying
            plane["altitude"] += random.choice([-100, 0, 100]) #simulate small altitude fluctuations


    # Conflict detection using the Haversine formula
    def distance_km(lat1, lon1, lat2, lon2):
        from math import radians, cos, sin, sqrt, atan2

        R = 6371  # location radius (km)
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    conflicts = [] # list of conflicting pairs
    for i, a1 in enumerate(sim_aircraft):
        for j, a2 in enumerate(sim_aircraft):
            if i >= j:
                continue # do not compare the same or already compared pairs
            dist = distance_km(a1["lat"], a1["lon"], a2["lat"], a2["lon"])
            alt_diff = abs(a1["altitude"] - a2["altitude"])
            if dist < 3 and alt_diff < 1000:
                conflicts.append((a1["call_sign"], a2["call_sign"]))
# add conflict to each aircraft for front-end display
    for plane in sim_aircraft:
        plane["conflict"] = any(plane["call_sign"] in pair for pair in conflicts)
# track nearest aircraft distance (UI log display)
    for plane in sim_aircraft:
        nearest_dist = float('inf')
        for other in sim_aircraft:
            if plane == other: #skip the same aircraft
                continue
            dist = distance_km(plane["lat"], plane["lon"], other["lat"], other["lon"]) # calculate distance 
            if dist < nearest_dist: # if the distance is smaller than the currrent nearest distance
                nearest_dist = dist # update nearest distance as new minimum value
        plane["nearest_distance_km"] = round(nearest_dist, 2) # calculated distance is stored in "nearest_distance_km" key

    # updates the weather
    return jsonify({
        "aircraft": sim_aircraft,
        "weather": current_weather
        })


#route for issuing commands to aircraft via dropdown (taxi, take off, land)
@app.route("/command/<call_sign>/<cmd>")
def issue_command(call_sign, cmd):
    for plane in sim_aircraft:
        if plane["call_sign"] == call_sign:
            if cmd == "taxi":
                plane["status"] = "taxi"
            elif cmd == "takeoff":
                plane["status"] = "takeoff"
            elif cmd == "land":
                plane["status"] = "stationary"
                plane["altitude"] = 0
                plane["route"] = []
            break
    return jsonify({"status": "ok"})


            