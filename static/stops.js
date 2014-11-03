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

function format_time(minutes) {
  hours = Math.floor(minutes / 60);
  minutes = minutes - hours * 60;
  if (hours > 0) {
    return hours + (minutes < 10 ? ":0" : ":") + minutes;
  } else {
    return minutes;
  }
};

var delay = 30000;
function update_realtime(stops_data, num_updates) {
  var wait = 0;
  var this_num_updates = 0;
  _.each(stops_data.stops_data.slice(0, 1), function(stop_data) {
    _.each(stop_data.route_ids, function(route_id) {
      setTimeout(function() {
      $.post("/realtime/ids", {
        stop_id: stop_data.stop_id,
        route: route_id,
      }).done(
        function(data) {
          var times = [];
          _.each(data["stopTimes"], function(stop_time) {
            times.push(format_time(stop_time["Minutes"]));
          });
          var el = $("#" + stop_data.stop_id + "_" + route_id);
          el.text(times.join(", "));
          el.css({backgroundColor: "#FF8"});
          el.animate({backgroundColor: "#FFF"}, delay / 10);
        }).error(function(data) {
          $(id).text("Error: " + data);
        });
      }, wait);
      if (num_updates > 0) {
        wait += Math.floor(delay / num_updates);
      }
      this_num_updates++;
    });
    return false;
  });
  return this_num_updates;
}

// Stop automatically updating after 5 minutes.
var END_OF_TIMES = 5 * 60000;
function on_stop_response(stops_data) {
  //console.log(stops_data);
  $("#response").html(STOPS_TEMPLATE({ stops_data: stops_data }));
  var num_updates = update_realtime(stops_data, 0);
  var update_interval = setInterval(function() {
    console.log("Running interval.");
    update_realtime(stops_data, num_updates);
  }, delay);
  setTimeout(function() {
    alert('Stopping automatic updates to save load. Refresh to continue them.');
    clearInterval(update_interval);
  }, END_OF_TIMES);
}
