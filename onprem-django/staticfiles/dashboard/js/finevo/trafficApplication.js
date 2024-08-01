// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Cairo';
Chart.defaults.global.defaultFontColor = '#858796';

var ctxtrafficApplication = document.getElementById("trafficApplication");
var trafficApplication = new Chart(ctxtrafficApplication, {
  type: 'doughnut',
  data: {
    labels: application['name'],
    datasets: [{
      data: application['data'],
      backgroundColor: application['color'],
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
