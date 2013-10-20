var GET_CURRENT_POSITION_ERRORS = { 
  1: 'Permission denied',
  2: 'Position unavailable',
  3: 'Request timeout'
};

$(function() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      on_position_response, 
      function(error) {
        $("#response").text(
            "Error: " + GET_CURRENT_POSITION_ERRORS[error.code]);
      },
      {
        enableHighAccuracy: true,
        timeout: 10 * 1000 * 1000,
        maximumAge: 0
      });
  } else {
    $("#response").text("Geolocation is not supported by this browser");
  }

  route_filter_form(function(routes) {
    return "/closest/" + number + "/" + routes.join(",");
  });

  stop_filter_form();
});

function on_position_response(position) {
  //var date = new Date(2013, 9, 15, 0, 3, 0);
  var date = new Date();
  var tomorrow = new Date(date);
  tomorrow.setDate(tomorrow.getDate() + 1);
  $.post("/nextbus/distance", {
    lat: position.coords.latitude,
    lon: position.coords.longitude,
    time: string_time(date),
    weekday: get_weekday(date),
    date: string_date(date),
    tomorrow_weekday: get_weekday(tomorrow),
    tomorrow_date: string_date(tomorrow),
    number: number,
    routes: routes,
  }).done(function(stops_data_json) {
    on_stop_response(stops_data_json, position);
  }).error(function(data) {
    alert("error: " + data);
  });
}

function on_stop_response(stops_data, position) {
  $("#response").html(
      CLOSEST_TEMPLATE({ stops_data: stops_data, position: position }));
}
