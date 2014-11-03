import csv
import math
import itertools
import os
import requests
import datetime

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
    return distance_on_unit_sphere(
        float(stop["stop_lat"]), float(stop["stop_lon"]), lat, lon)
  return func

def get_service(weekday, date, weekday_to_schedules_map, date_to_schedules_map):
  return (weekday_to_schedules_map[weekday] - date_to_schedules_map[date]['excluded']) | date_to_schedules_map[date]['included']

def get_service_name(weekday, date, weekday_to_schedules_map,
    date_to_schedules_map):
  services = get_service(weekday, date, weekday_to_schedules_map, date_to_schedules_map)
  for service in services:
    if "Weekday" in service:
      return "Weekday"
    elif "Sunday" in service and weekday != 0:
      return "Holiday (Sunday)"
    elif "Saturday" in service and weekday != 6:
      return "Holiday (Saturday)"
    elif "Saturday" in service:
      return "Saturday"
    elif "Sunday" in service:
      return "Sunday"
  return "Unknown"

def compile_templates(template_dir, output_file):
  template_files = [f for f in os.listdir(template_dir)
                    if os.path.isfile(os.path.join(template_dir, f))]
  with open(output_file, 'w') as output_file:
    for template_file in template_files:
      if not template_file.endswith(".html"):
        raise Exception('Unexpected non-html template file: ' + template_file)
      template_name = "{}_TEMPLATE".format(template_file[0:-5].upper())
      output_file.write("var {} = _.template(\n".format(template_name))
      with open(os.path.join(template_dir, template_file)) as template:
        for line in template.readlines():
          output_file.write("\"{}\" + \n".format(
            line.rstrip().replace('"', '\\"')))
      output_file.write("\"\");\n")

# TODO: periodically clear this cache.
real_bus_time_cache = {}
last_request = 0
cache_seconds = 28
def get_real_bus_times(stop_id, route):
  url = "http://realtimemap.grt.ca/Stop/GetStopInfo?stopId=%d&routeId=%d" % (stop_id, route)
  res = None
  if url in real_bus_time_cache and real_bus_time_cache[url][0] > datetime.datetime.now() - datetime.timedelta(seconds=28):
    print "Returning cached result for url %s" % (url,)
    res = real_bus_time_cache[url][1]
  else:
    print "Fetching new result from url %s" % (url,)
    res = requests.get(url)
    real_bus_time_cache[url] = (datetime.datetime.now(), res)

  if res.status_code != 200:
    print res
    return None
  elif res.json()['status'] != "success":
    print res.json()
    return None
  return res.json()
