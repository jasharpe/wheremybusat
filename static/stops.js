var STOPS_TEMPLATE = _.template(
    "<% _.each(stops_data, function(stop_data) { %>" +
    "<h2><%- stop_data.stop_name %> (<%- stop_data.stop_id %>)</h2>" +
    "<% _.each(stop_data.upcoming, function(time) { %>" +
    "<div><span><%- time.time %></span> - <b><%- time.route %></b></div>" +
    "<% }); %>" +
    "<% }); %>");

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

  route_filter_form(function(routes) {
    return "/stops/" + stop_ids.join() + "/" + routes.join();
  });
});

function on_stop_response(stops_data) {
  $("#response").html(
      STOPS_TEMPLATE({ stops_data: stops_data.stops_data }));
}
