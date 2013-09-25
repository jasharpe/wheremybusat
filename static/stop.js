var STOPS_TEMPLATE = _.template(
    "<% _.each(stops_data, function(stop_data) { %>" +
    "<h2><%- stop_data.stop_name %> (<%- stop_data.stop_id %>)</h2>" +
    "<% _.each(stop_data.upcoming, function(time) { %>" +
    "<div><span><%- time.time %></span> - <b><%- time.route %></b></div>" +
    "<% }); %>" +
    "<% }); %>");

$(function() {
  var date = new Date();
  $.post("/nextbus_stop", {
    time: string_time(date),
    weekday: date.getDay(),
    stop_id: stop_id
  }).done(
    function(stop_data) {
      on_stop_response(stop_data);
    }).error(function(data) {
      alert("error: " + data);
    });
});

function on_stop_response(stops_data) {
  $("#response").html(
      STOPS_TEMPLATE({ stops_data: stops_data.stops_data }));
}
