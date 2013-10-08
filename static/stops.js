$(function() {
  //var date = new Date(2013, 9, 14, 19, 24, 0);
  var date = new Date();
  $.post("/nextbus/ids", {
    time: string_time(date),
    weekday: date.getDay(),
    date: string_date(date),
    stop_ids: stop_ids,
    routes: routes
  }).done(
    function(stop_data) {
      on_stop_response(stop_data);
    }).error(function(data) {
      alert("error: " + data);
    });

  route_filter_form(function(routes) {
    return "/stops/" + stop_ids.join(",") + "/" + routes.join(",");
  });

  stop_filter_form();
});

function on_stop_response(stops_data) {
  $("#response").html(STOPS_TEMPLATE({ stops_data: stops_data }));
}
