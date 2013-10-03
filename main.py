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
# Allows sorted and int to be used in templates.
app.jinja_env.globals.update(sorted=sorted, int=int)

def read_to_dict(filename):
  return lib.read_csv_file_with_header(os.path.join(os.path.dirname(__file__), "GRT_GTFS/{}".format(filename)))

def initialize():
  trips = read_to_dict("trips.txt")
  stops = read_to_dict("stops.txt")
  stop_times = read_to_dict("stop_times.txt")
  calendar = read_to_dict("calendar.txt")
  calendar_dates = read_to_dict("calendar_dates.txt")

  global weekday_to_schedules_map
  weekday_to_schedules_map = collections.defaultdict(set)
  for calendar_entry in calendar:
    service_id = calendar_entry['service_id']
    for day, key in enumerate(['sunday', 'monday', 'tuesday',
      'wednesday', 'thursday', 'friday', 'saturday']):
      if int(calendar_entry[key]):
        weekday_to_schedules_map[day].add(service_id)

  global date_to_schedules_map
  date_to_schedules_map = collections.defaultdict(lambda: collections.defaultdict(set))
  for calendar_date_entry in calendar_dates:
    date = calendar_date_entry['date']
    exception_type = calendar_date_entry['exception_type']
    service_id = calendar_date_entry['service_id']
    if exception_type == "2":
      date_to_schedules_map[date]['excluded'].add(service_id)
    elif exception_type == "1":
      date_to_schedules_map[date]['included'].add(service_id)

  global route_names_set
  route_names_set = set()
  for trip in trips:
    route_names_set.add(trip['route_id'])
  
  global trip_id_to_trip_map
  trip_id_to_trip_map = {trip['trip_id'] : trip for trip in trips}

  global stop_id_to_stop_map
  stop_id_to_stop_map = {}
  for stop in stops:
    stop_id_to_stop_map[stop['stop_id']] = stop

  global sorted_stops
  sorted_stops = sorted(stops, key=lambda stop: stop['stop_id'])
  
  global stop_id_to_stop_times_map, stop_id_to_route_ids_map
  stop_id_to_stop_times_map = collections.defaultdict(list)
  stop_id_to_route_ids_map = collections.defaultdict(set)
  for stop_time in stop_times:
    stop_id = stop_time['stop_id']
    route_id = trip_id_to_trip_map[stop_time['trip_id']]['route_id']
    stop_id_to_route_ids_map[stop_id].add(route_id)
    stop_id_to_stop_times_map[stop_id].append(stop_time)
  # Sort each list of stop times by departure time.
  for key, value in stop_id_to_stop_times_map.items():
    value.sort(key=lambda stop_time: stop_time['departure_time'])
  
  print "Finished initialization."

initialize()

def get_stop_data(stops, routes, time, weekday, date):
  service_set = lib.get_service(weekday, date, weekday_to_schedules_map,
      date_to_schedules_map)

  stop_datas = []
  for stop in stops:
    stop_name = stop["stop_name"]
    stop_id = stop["stop_id"]

    def stop_time_has_service(stop_time):
      trip = trip_id_to_trip_map[stop_time['trip_id']]
      service_id = trip['service_id']
      return (service_id in service_set and
        (not routes or trip['route_id'] in routes))
    
    stop_times = filter(stop_time_has_service, stop_id_to_stop_times_map[stop_id])
    position = 0
    for i, stop_time in enumerate(stop_times):
      if stop_time['departure_time'] >= time:
        position = i
        break

    upcomings = []
    for stop_time in stop_times[position:position + 5]:
      upcoming = {}
      upcoming['time'] = stop_time['departure_time']
      upcoming['route'] = trip_id_to_trip_map[stop_time['trip_id']]['trip_headsign']
      upcomings.append(upcoming)

    stop_datas.append({
        'stop_name' : stop_name,
        'stop_id' : stop_id,
        'route_ids' : sorted(stop_id_to_route_ids_map[stop_id]),
        'upcoming' : upcomings,
        'lat' : stop['stop_lat'],
        'lon' : stop['stop_lon'],
    })
  
  return { 'stops_data': stop_datas }

@app.route("/")
def closest_handler():
  return render_template("closest.html", number=5, more=10, routes=[])

@app.route("/closest/<int:number>")
def closest_number_handler(number):
  more = number + 5
  if number >= 30:
    number = 30
    more = number
  return render_template("closest.html", number=number, more=more, routes=[])

@app.route("/closest/<int:number>/<routes_string>")
def closest_number_routes_handler(number, routes_string):
  more = number + 5
  if number >= 30:
    number = 30
    more = number
  routes = routes_string.split(",")
  if not all(route in route_names_set for route in routes):
    abort(404)
  return render_template("closest.html", number=number, more=more, routes=routes)

@app.route("/stops/<stop_ids_string>")
def stop_handler(stop_ids_string):
  stop_ids = stop_ids_string.split(",")
  if not all(stop_id in stop_id_to_stop_map for stop_id in stop_ids):
    abort(404)
  return render_template(
    "stops.html", stop_ids=stop_ids, routes=[],
    stop_ids_string=", ".join(stop_ids))

@app.route("/stops/<stop_ids_string>/<routes_string>")
def route_stop_handler(stop_ids_string, routes_string):
  stop_ids = stop_ids_string.split(",")
  if not all(stop_id in stop_id_to_stop_map for stop_id in stop_ids):
    abort(404)
  routes = routes_string.split(",")
  if not all(route in route_names_set for route in routes):
    abort(404)
  return render_template(
    "stops.html", stop_ids=stop_ids, routes=routes,
    stop_ids_string=", ".join(stop_ids))

precomputed_stops = None
@app.route("/allstops")
def stops_handler():
  global precomputed_stops
  if precomputed_stops is None:
    precomputed_stops = render_template("all_stops.html", stops=sorted_stops,
        stop_id_to_route_ids_map=stop_id_to_route_ids_map)
  return precomputed_stops

@app.route("/about")
def about_handler():
  return render_template("about.html")

@app.route("/nextbus/ids", methods=["POST"])
def nextbus_stop():
  time = request.form['time']
  weekday = int(request.form['weekday'])
  date = request.form['date']
  stop_ids = request.form.getlist('stop_ids[]')
  routes = request.form.getlist('routes[]')
  return jsonify(**get_stop_data(
    [stop_id_to_stop_map[stop_id] for stop_id in stop_ids], routes, time, weekday, date))

@app.route("/nextbus/distance", methods=["POST"])
def nextbus():
  lat = float(request.form['lat'])
  lon = float(request.form['lon'])
  time = request.form['time']
  weekday = int(request.form['weekday'])
  date = request.form['date']
  number = int(request.form['number'])
  routes = request.form.getlist('routes[]')
  stops = sorted_stops
  if routes:
    def filter_by_routes(stop):
      return stop_id_to_route_ids_map[stop['stop_id']].intersection(routes)
    stops = filter(filter_by_routes, stops)
  closest_stops = heapq.nsmallest(number, stops, key=lib.dist_func(lat, lon))
  return jsonify(**get_stop_data(closest_stops, routes, time, weekday, date))

if __name__ == "__main__":
  app.run(debug=True)
