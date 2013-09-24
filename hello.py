from flask import Flask
from flask import render_template
from flask import request
import json
import csv
import itertools
import collections
import os
import heapq
import math

app = Flask(__name__)

def read_csv_file_with_header(name):
  reader = csv.reader(open(name))
  labels = reader.next()
  output = []
  for row in reader:
    labelled_row = {}
    for label, data in itertools.izip(labels, row):
      labelled_row[label] = data
    output.append(labelled_row)
  return output

trips = read_csv_file_with_header(os.path.join(os.path.dirname(__file__), "GRT_GTFS/trips.txt"))
trip_map = {trip['trip_id'] : trip for trip in trips}
stops = read_csv_file_with_header(os.path.join(os.path.dirname(__file__), "GRT_GTFS/stops.txt"))
stop_map = {}
for stop in stops:
  stop_map[stop['stop_id']] = stop
sorted_stops = sorted(stops, key=lambda stop: stop['stop_id'])
stop_times = read_csv_file_with_header(os.path.join(os.path.dirname(__file__), "GRT_GTFS/stop_times.txt"))
stop_time_map = collections.defaultdict(list)
for stop_time in stop_times:
  stop_time_map[stop_time['stop_id']].append(stop_time)
for key, value in stop_time_map.items():
  value.sort(key=lambda stop_time: stop_time['arrival_time'])
print "Ready!"

@app.route("/")
def main():
  return render_template("foo.html")

@app.route("/stop/<int:stop_id>")
def stop_handler(stop_id):
  return render_template("foo.html", stop_id=stop_id)

precomputed_stops = None

@app.route("/stops")
def stops_handler():
  global precomputed_stops
  if precomputed_stops is None:
    precomputed_stops = render_template("stops.html", stops=sorted_stops)
  return precomputed_stops

@app.route("/nextbus_stop", methods=["POST"])
def nextbus_stop():
  time = request.form['time']
  weekday = int(request.form['weekday'])
  stop_id = request.form['stop_id']
  return json.dumps(get_stop_data([stop_map[stop_id]], time, weekday))

# Returns distance between points on the earth in km.
# From http://www.johndcook.com/python_longitude_latitude.html
def distance_on_unit_sphere(lat1, long1, lat2, long2):
    degrees_to_radians = math.pi / 180.0
    phi1 = (90.0 - lat1) * degrees_to_radians
    phi2 = (90.0 - lat2) * degrees_to_radians
    theta1 = long1 * degrees_to_radians
    theta2 = long2 * degrees_to_radians
    cos = (math.sin(phi1) * math.sin(phi2) * math.cos(theta1 - theta2) + 
           math.cos(phi1) * math.cos(phi2))
    arc = math.acos(cos)
    return arc * 6373

def dist_func(lat, lon):
  def func(stop):
    return distance_on_unit_sphere(float(stop["stop_lat"]), float(stop["stop_lon"]), lat, lon)
  return func

@app.route("/nextbus", methods=["POST"])
def nextbus():
  lat = float(request.form['lat'])
  lon = float(request.form['lon'])
  time = request.form['time']
  weekday = int(request.form['weekday'])
  closest_stops = heapq.nsmallest(5, stops, key=dist_func(lat, lon))

  return json.dumps(get_stop_data(closest_stops, time, weekday))

def get_stop_data(stops, time, weekday):
  if weekday in [1, 2, 3, 4, 5]:
    schedule = "13FALL-All-Weekday-05"
  elif weekday == 6:
    schedule = "13FALL-All-Saturday-03"
  else:
    schedule = "13FALL-All-Sunday-03"

  stop_datas = []
  for stop in stops:
    stop_name = stop["stop_name"]
    stop_id = stop["stop_id"]

    stop_times = filter(lambda stop_time: trip_map[stop_time['trip_id']]['service_id'] == schedule, stop_time_map[stop_id])
    position = 0
    for i, stop_time in enumerate(stop_times):
      if stop_time['arrival_time'] >= time:
        position = i
        break

    upcomings = []
    for stop_time in stop_times[position:position+5]:
      upcoming = {}
      upcoming['time'] = stop_time['arrival_time']
      upcoming['route'] = trip_map[stop_time['trip_id']]['trip_headsign']
      upcomings.append(upcoming)

    stop_data = {'stop_name' : stop_name, 'stop_id' : stop_id, 'upcoming' : upcomings, 'lat' : stop['stop_lat'], 'lon' : stop['stop_lon']}
    stop_datas.append(stop_data)
  
  return stop_datas

if __name__ == "__main__":
  print "Running app!"
  #app.run(debug=True, host="0.0.0.0")
  app.run(debug=True)
