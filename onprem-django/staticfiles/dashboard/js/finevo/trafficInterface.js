// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Cairo';
Chart.defaults.global.defaultFontColor = '#858796';

var ctxtrafficInterface = document.getElementById("trafficInterface");
var trafficInterface = new Chart(ctxtrafficInterface, {
  type: 'doughnut',
  data: {
    labels: interface['name'],
    datasets: [{
      data: interface['data'],
      backgroundColor: interface['color'],
      //hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf'],
      hoverBorderColor: "rgba(234, 236, 244, 1)",
    }],
  },
  options: {
    maintainAspectRatio: false,
    plugins: {
      datalabels: {
          display: false, // This will disable the plugin for this chart
      }
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      borderColor: '#dddfeb',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      caretPadding: 10,
      callbacks: {
        label: function(tooltipItem, chart) {
          var dataset = chart.datasets[tooltipItem.datasetIndex];
          var value = dataset.data[tooltipItem.index];
          return chart.labels[tooltipItem.index] + ': ' + number_format(value) + ' MB';
        }
      }
    },
    legend: {
      display: false
    },
    cutoutPercentage: 50
  },
});
