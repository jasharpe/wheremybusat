from flask import Flask
from flask import render_template
from flask import request
import json
import csv
import itertools
import collections

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

trips = read_csv_file_with_header("GRT_GTFS/trips.txt")
trip_map = {trip['trip_id'] : trip for trip in trips}
stops = read_csv_file_with_header("GRT_GTFS/stops.txt")
stop_times = read_csv_file_with_header("GRT_GTFS/stop_times.txt")
stop_time_map = collections.defaultdict(list)
for stop_time in stop_times:
  stop_time_map[stop_time['stop_id']].append(stop_time)
for key, value in stop_time_map.items():
  value.sort(key=lambda stop_time: stop_time['arrival_time'])
print "Ready!"

@app.route("/")
def main():
  return render_template("foo.html")

@app.route("/nextbus", methods=["POST"])
def stop():
  lat = float(request.form['lat'])
  lon = float(request.form['lon'])
  time = request.form['time']
  weekday = int(request.form['weekday'])
  if weekday in [1, 2, 3, 4, 5]:
    schedule = "13FALL-All-Weekday-05"
  elif weekday == 6:
    schedule = "13FALL-All-Saturday-03"
  else:
    schedule = "13FALL-All-Sunday-03"
  min_dist = -1
  min_stop = "UNKNOWN"
  min_stop_id = 0
  sorted_stops = sorted(stops, key=lambda stop: (float(stop["stop_lat"]) - lat) ** 2 + (float(stop["stop_lon"]) - lon) ** 2)
  closest_stop_data = []
  for stop in sorted_stops[:5]:
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
    closest_stop_data.append(stop_data)

  return json.dumps(closest_stop_data)

if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0")
