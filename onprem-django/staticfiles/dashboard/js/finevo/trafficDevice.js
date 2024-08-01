// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Cairo';
Chart.defaults.global.defaultFontColor = '#858796';

var ctxtrafficDevice = document.getElementById("trafficDevice");
var trafficDevice = new Chart(ctxtrafficDevice, {
  type: 'doughnut',
  data: {
    labels: device['name'],
    datasets: [{
      data: device['data'],
      backgroundColor: device['color'],
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
    },
    legend: {
      display: false
    },
    cutoutPercentage: 50
  },
});
