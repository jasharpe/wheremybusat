import csv
import math
import itertools

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
