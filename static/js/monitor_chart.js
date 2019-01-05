google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);

function drawChart() {
  var data = google.visualization.arrayToDataTable([
    ['Week', 'Hosts'],
    ['12-30',  3],
    ['1-6',  2],
    ['1-13',  4],
    ['1-20',  1],
    ['1-27',  2],
    ['2-3',  1],
    ['2-10',  3],
    ['2-17',  1]
  ]);

  var options = {
    title: 'Hosts Status',
    curveType: 'function',
    legend: { position: 'bottom' }
  };

  var chart = new google.visualization.LineChart(document.getElementById('curve_chart'));

  chart.draw(data, options);
}