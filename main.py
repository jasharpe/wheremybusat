from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import abort
import collections
import os
import heapq
import lib

app = Flask(__name__)

def initialize():
  global trip_map, stop_map, sorted_stops, stop_time_map, route_names
  trips = lib.read_csv_file_with_header(os.path.join(
    os.path.dirname(__file__), "GRT_GTFS/trips.txt"))
  route_names = set()
  for trip in trips:
    route_names.add(trip['route_id'])
  trip_map = {trip['trip_id'] : trip for trip in trips}
  stops = lib.read_csv_file_with_header(os.path.join(
    os.path.dirname(__file__), "GRT_GTFS/stops.txt"))
  stop_map = {}
  for stop in stops:
    stop_map[stop['stop_id']] = stop
  sorted_stops = sorted(stops, key=lambda stop: stop['stop_id'])
  stop_times = lib.read_csv_file_with_header(os.path.join(
    os.path.dirname(__file__), "GRT_GTFS/stop_times.txt"))
  stop_time_map = collections.defaultdict(list)
  for stop_time in stop_times:
    stop_time_map[stop_time['stop_id']].append(stop_time)
  for key, value in stop_time_map.items():
    value.sort(key=lambda stop_time: stop_time['arrival_time'])
  print "Ready!"

initialize()

def get_stop_data(stops, routes, time, weekday):
  service = lib.get_service(weekday)

  stop_datas = []
  for stop in stops:
    stop_name = stop["stop_name"]
    stop_id = stop["stop_id"]

    def stop_time_has_service(stop_time):
      trip = trip_map[stop_time['trip_id']]
      service_id = trip['service_id']
      return (service_id == service and
        (not routes or trip['route_id'] in routes))
    
    stop_times = filter(stop_time_has_service, stop_time_map[stop_id])
    position = 0
    for i, stop_time in enumerate(stop_times):
      if stop_time['arrival_time'] >= time:
        position = i
        break

    upcomings = []
    for stop_time in stop_times[position:position + 5]:
      upcoming = {}
      upcoming['time'] = stop_time['arrival_time']
      upcoming['route'] = trip_map[stop_time['trip_id']]['trip_headsign']
      upcomings.append(upcoming)

    stop_datas.append({
        'stop_name' : stop_name,
        'stop_id' : stop_id,
        'upcoming' : upcomings,
        'lat' : stop['stop_lat'],
        'lon' : stop['stop_lon'],
    })
  
  return { 'stops_data': stop_datas }

@app.route("/")
def closest_handler():
  return render_template("main.html", number=5, more=10)

@app.route("/<int:number>")
def closest_number_handler(number):
  more = number + 5
  if number >= 30:
    number = 30
    more = number
  return render_template("main.html", number=number, more=more)

@app.route("/stop/<stop_ids_string>")
def stop_handler(stop_ids_string):
  stop_ids = stop_ids_string.split(",")
  if not all(stop_id in stop_map for stop_id in stop_ids):
    abort(404)
  return render_template(
    "stop.html", stop_ids=stop_ids, routes=[],
    stop_ids_string=", ".join(stop_ids))

@app.route("/stop/<stop_ids_string>/<routes_string>")
def route_stop_handler(stop_ids_string, routes_string):
  stop_ids = stop_ids_string.split(",")
  if not all(stop_id in stop_map for stop_id in stop_ids):
    abort(404)
  routes = routes_string.split(",")
  if not all(route in route_names for route in routes):
    abort(404)
  return render_template(
    "stop.html", stop_ids=stop_ids, routes=routes,
    stop_ids_string=", ".join(stop_ids),
    routes_string = ", ".join(routes))

precomputed_stops = None
@app.route("/stops")
def stops_handler():
  global precomputed_stops
  if precomputed_stops is None:
    precomputed_stops = render_template("stops.html", stops=sorted_stops)
  return precomputed_stops

@app.route("/nextbus/ids", methods=["POST"])
def nextbus_stop():
  time = request.form['time']
  weekday = int(request.form['weekday'])
  stop_ids = request.form.getlist('stop_ids[]')
  routes = request.form.getlist('routes[]')
  return jsonify(**get_stop_data(
    [stop_map[stop_id] for stop_id in stop_ids], routes, time, weekday))

@app.route("/nextbus/distance", methods=["POST"])
def nextbus():
  lat = float(request.form['lat'])
  lon = float(request.form['lon'])
  time = request.form['time']
  weekday = int(request.form['weekday'])
  number = int(request.form['number'])
  closest_stops = heapq.nsmallest(number, sorted_stops, key=lib.dist_func(lat, lon))
  return jsonify(**get_stop_data(closest_stops, [], time, weekday))

if __name__ == "__main__":
  app.run(debug=True)
