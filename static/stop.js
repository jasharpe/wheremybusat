var STOPS_TEMPLATE = _.template(
    "<% _.each(stops_data, function(stop_data) { %>" +
    "<h2><%- stop_data.stop_name %> (<%- stop_data.stop_id %>)</h2>" +
    "<% _.each(stop_data.upcoming, function(time) { %>" +
    "<div><span><%- time.time %></span> - <b><%- time.route %></b></div>" +
    "<% }); %>" +
    "<% }); %>");

function is_positive_int(str) {
  var n = ~~Number(str);
  return String(n) === str && n > 0;
}

$(function() {
  var date = new Date();
  $.post("/nextbus/ids", {
    time: string_time(date),
    weekday: date.getDay(),
    stop_ids: stop_ids,
    routes: routes
  }).done(
    function(stop_data) {
      on_stop_response(stop_data);
    }).error(function(data) {
      alert("error: " + data);
    });

  $("#route_filter_form").submit(function(event) {
    event.preventDefault();
    var route_filter = $("#route_filter").val();
    var routes = route_filter.split(/\s*,\s*/);
    var valid = true;
    _.each(routes, function (route) {
      if (!is_positive_int(route)) {
        valid = false;
      }
    });
    if (!valid) {
      $("#error").text("Invalid route filter.");
      return;
    }
    window.location = "/stop/" + stop_ids.join() + "/" + routes.join();
  });
});

function on_stop_response(stops_data) {
  $("#response").html(
      STOPS_TEMPLATE({ stops_data: stops_data.stops_data }));
}
