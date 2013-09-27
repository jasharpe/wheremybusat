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

def get_service(weekday):
  if weekday in [1, 2, 3, 4, 5]:
    return "13FALL-All-Weekday-05"
  elif weekday == 6:
    return "13FALL-All-Saturday-03"
  else:
    return "13FALL-All-Sunday-03"
