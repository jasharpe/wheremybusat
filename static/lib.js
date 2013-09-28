// Returns the number n, padded to length width with character z (or '0' if
// z is not given).
function pad(n, width, z) {
  z = z || '0';
  n = n + '';
  return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
}

// Add a toRad method to Numbers that does a degrees to radians conversion.
if (typeof(Number.prototype.toRad) === "undefined") {
  Number.prototype.toRad = function() {
    return this * Math.PI / 180;
  }
}

// Returns the great circle distance between (lat1, lon1) and (lat2, lon2).
function dist(lat1, lon1, lat2, lon2) {
  var R = 6371; // km
  var dLat = (lat2 - lat1).toRad();
  var dLon = (lon2 - lon1).toRad();
  var lat1 = parseFloat(lat1).toRad();
  var lat2 = parseFloat(lat2).toRad();

  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2); 
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)); 
  var d = R * c;
  return d;
}

// Returns the time in format HH:MM:SS, where each section is padded to 2
// digits if necessary.
function string_time(date) {
  return (pad(date.getHours(), 2) + ":" +
          pad(date.getMinutes(), 2) + ":" +
          pad(date.getSeconds(), 2));
}

// Returns the distance between position (a return value from
// navigator.geolocation.getCurrentPosition) and (lat, lon) as a string. If the
// distance is less than a kilometre, returns the distance in metres followed
// by "m". If the distance is more than a kilometre, returns the distance in
// kilometres followed by "km".
function dist_string(position, lat, lon) {
  var d = dist(position.coords.latitude, position.coords.longitude, lat, lon);
  if (d < 1) {
    return (d * 1000).toFixed(0) + "m";
  } else {
    return d.toFixed(2) + "km";
  }
}

// Returns true if str contains a positive integer.
function is_positive_int(str) {
  var n = ~~Number(str);
  return String(n) === str && n > 0;
}
