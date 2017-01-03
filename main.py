from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import abort
from flask import url_for
import collections
import os
import heapq
import lib
import sys
from memory_profiler import profile


app = Flask(__name__)
# Allows sorted and int to be used in templates.
app.jinja_env.globals.update(sorted=sorted, int=int)

@profile
def read_to_dict(filename):
  return lib.read_csv_file_with_header(os.path.join(os.path.dirname(__file__), "GRT_GTFS/{}".format(filename)))

def initialize():
  trips = read_to_dict("trips.txt")
  stops = read_to_dict("stops.txt")
  stop_times = read_to_dict("stop_times.txt")

  global latest
  latest = max(stop_time['departure_time'] for stop_time in stop_times)

  calendar = read_to_dict("calendar.txt")
  calendar_dates = read_to_dict("calendar_dates.txt")

  global weekday_names
  weekday_names = {day: key for day, key in enumerate([
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
    'Saturday'])}

  global weekday_to_schedules_map
  weekday_to_schedules_map = collections.defaultdict(set)
  global service_id_to_days_map
  service_id_to_days_map = collections.defaultdict(list)
  for calendar_entry in calendar:
    service_id = calendar_entry['service_id']
    for day, key in enumerate(['Sunday', 'Monday', 'Tuesday',
      'Wednesday', 'Thursday', 'Friday', 'Saturday']):
      if int(calendar_entry[key.lower()]):
        service_id_to_days_map[service_id].append(key)
        weekday_to_schedules_map[day].add(service_id)

  global special_service_id_to_days_map
  special_service_id_to_days_map = {}
  for (service_id, days) in service_id_to_days_map.items():
    if set(days) not in [
      set(['Saturday']),
      set(['Sunday']),
      set(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]:
      #set(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])]:
      special_service_id_to_days_map[service_id] = days

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

  lib.compile_templates(
      os.path.join(os.path.dirname(__file__), "templates/js"),
      os.path.join(os.path.dirname(__file__), "static/compiled_templates.js"))
  
  print "Finished initialization."

initialize()

def get_upcomings(stop, routes, time, service_set, num_stop_times,
    service_id_to_asterisks_map, annotations, is_tomorrow):
  stop_name = stop["stop_name"]
  stop_id = stop["stop_id"]

  def stop_time_has_service(stop_time):
    trip = trip_id_to_trip_map[stop_time['trip_id']]
    service_id = trip['service_id']
    return (service_id in service_set and
      (not routes or trip['route_id'] in routes))

  stop_times = filter(stop_time_has_service, stop_id_to_stop_times_map[stop_id])
  position = -1
  for i, stop_time in enumerate(stop_times):
    if stop_time['departure_time'] >= time:
      position = i
      break

  if position == -1:
    return []

  upcomings = []
  for stop_time in stop_times[position:position + num_stop_times]:
    service_id = trip_id_to_trip_map[stop_time['trip_id']]['service_id']
    upcoming = {}
    upcoming['time'] = stop_time['departure_time']
    upcoming['route'] = trip_id_to_trip_map[stop_time['trip_id']]['trip_headsign']
    if service_id in special_service_id_to_days_map:
      days = special_service_id_to_days_map[service_id]
      if not service_id in service_id_to_asterisks_map:
        asterisk = '*' * (len(service_id_to_asterisks_map) + 1)
        service_id_to_asterisks_map[service_id] = asterisk
        annotations.append(asterisk + ' ' + ', '.join(days) + " only")
      upcoming['asterisk'] = service_id_to_asterisks_map[service_id]
    else:
      upcoming['asterisk'] = ''
    upcoming['is_tomorrow'] = is_tomorrow
    upcomings.append(upcoming)

  return upcomings

def get_stop_data(stops, routes, time, weekday, date, tomorrow_weekday,
    tomorrow_date):
  service_set = lib.get_service(weekday, date, weekday_to_schedules_map,
      date_to_schedules_map)
  tomorrow_service_set = lib.get_service(tomorrow_weekday, tomorrow_date,
      weekday_to_schedules_map, date_to_schedules_map)

  service_name = lib.get_service_name(weekday, date, weekday_to_schedules_map,
      date_to_schedules_map)
  tomorrow_service_name = lib.get_service_name(tomorrow_weekday, tomorrow_date, 
      weekday_to_schedules_map, date_to_schedules_map)

  stop_datas = []
  tomorrow_used = False
  for stop in stops:
    stop_name = stop["stop_name"]
    stop_id = stop["stop_id"]
    service_id_to_asterisks_map = {}
    annotations = []
    upcomings = get_upcomings(stop, routes, time, service_set, 5,
        service_id_to_asterisks_map, annotations, False)
    if len(upcomings) < 5:
      extra_upcomings = get_upcomings(stop, routes, "00:00:00",
        tomorrow_service_set, 5 - len(upcomings), service_id_to_asterisks_map,
        annotations, True)
      tomorrow_used = tomorrow_used or extra_upcomings
      upcomings.extend(extra_upcomings)
    
    stop_datas.append({
        'stop_name' : stop_name,
        'stop_id' : stop_id,
        'route_ids' : sorted(stop_id_to_route_ids_map[stop_id]),
        'upcoming' : upcomings,
        'annotations' : annotations,
        'lat' : stop['stop_lat'],
        'lon' : stop['stop_lon'],
    })
  
  return { 'stops_data': stop_datas, 'service' : service_name,
      'weekday_name' : weekday_names[weekday],
      'tomorrow_weekday_name' : weekday_names[tomorrow_weekday],
      'tomorrow_used' : tomorrow_used,
      'tomorrow_service' : tomorrow_service_name }

@app.route("/")
def closest_handler():
  return render_template("closest.html", number=5, more=10, routes=[],
      latest=latest)

@app.route("/closest/<int:number>")
def closest_number_handler(number):
  more = number + 5
  if number >= 30:
    number = 30
    more = number
  return render_template("closest.html", number=number, more=more, routes=[],
      latest=latest)

@app.route("/closest/<int:number>/<routes_string>")
def closest_number_routes_handler(number, routes_string):
  more = number + 5
  if number >= 30:
    number = 30
    more = number
  routes = routes_string.split(",")
  if not all(route in route_names_set for route in routes):
    abort(404)
  return render_template("closest.html", number=number, more=more,
      routes=routes, latest=latest)

@app.route("/stops/<stop_ids_string>")
def stop_handler(stop_ids_string):
  stop_ids = stop_ids_string.split(",")
  if not all(stop_id in stop_id_to_stop_map for stop_id in stop_ids):
    abort(404)
  return render_template(
    "stops.html", stop_ids=stop_ids, routes=[], latest=latest)

@app.route("/stops/<stop_ids_string>/<routes_string>")
def route_stop_handler(stop_ids_string, routes_string):
  stop_ids = stop_ids_string.split(",")
  if not all(stop_id in stop_id_to_stop_map for stop_id in stop_ids):
    abort(404)
  routes = routes_string.split(",")
  if not all(route in route_names_set for route in routes):
    abort(404)
  return render_template(
    "stops.html", stop_ids=stop_ids, routes=routes, latest=latest)

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
  tomorrow_weekday = int(request.form['tomorrow_weekday'])
  tomorrow_date = request.form['tomorrow_date']
  stop_ids = request.form.getlist('stop_ids[]')
  routes = request.form.getlist('routes[]')
  return jsonify(**get_stop_data(
    [stop_id_to_stop_map[stop_id] for stop_id in stop_ids], routes, time, weekday, date, tomorrow_weekday, tomorrow_date))

@app.route("/nextbus/distance", methods=["POST"])
def nextbus():
  lat = float(request.form['lat'])
  lon = float(request.form['lon'])
  time = request.form['time']
  weekday = int(request.form['weekday'])
  date = request.form['date']
  tomorrow_weekday = int(request.form['tomorrow_weekday'])
  tomorrow_date = request.form['tomorrow_date']
  number = int(request.form['number'])
  routes = request.form.getlist('routes[]')
  stops = sorted_stops
  if routes:
    def filter_by_routes(stop):
      return stop_id_to_route_ids_map[stop['stop_id']].intersection(routes)
    stops = filter(filter_by_routes, stops)
  closest_stops = heapq.nsmallest(number, stops, key=lib.dist_func(lat, lon))
  return jsonify(**get_stop_data(closest_stops, routes, time, weekday, date,
    tomorrow_weekday, tomorrow_date))

@app.route("/realtime/ids", methods=["POST", "GET"])
def realtime_ids():
  stop_id = None
  route = None
  if request.method == "POST":
    stop_id = int(request.form['stop_id'])
    route = int(request.form['route'])
  else:
    stop_id = int(request.args.get('stop_id'))
    route = int(request.args.get('route'))
  times = lib.get_real_bus_times(stop_id, route)
  if times is not None:
    return jsonify(times)
  # TODO: Handle errors better!

if __name__ == "__main__":
  app.run(debug=True)
