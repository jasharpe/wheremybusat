$(function() {
  //var date = new Date(2013, 9, 12, 2, 10, 0);
  var date = new Date();
  var tomorrow = new Date(date);
  tomorrow.setDate(tomorrow.getDate() + 1);
  $.post("/nextbus/ids", {
    time: string_time(date),
    weekday: get_weekday(date),
    date: string_date(date),
    tomorrow_weekday: get_weekday(tomorrow),
    tomorrow_date: string_date(tomorrow),
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
