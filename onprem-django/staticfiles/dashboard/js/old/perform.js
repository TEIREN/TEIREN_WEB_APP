Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

function getCookie(name = 'csrftoken') {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

//==================================================================================== Network usage
$(document).ready(function () {
  var ctx = document.getElementById("myNet").getContext("2d");
  var data = {
    labels: ["", "", "", "", "", "", "", "", ""],
    datasets: [{
      label: "Network Recieved",
      lineTension: 0,
      backgroundColor: "rgba(246, 194, 62, 0.05)",
      borderColor: "rgba(246, 194, 62, 1)",
      pointRadius: 0,
      pointBackgroundColor: "rgba(246, 194, 62, 1)",
      pointBorderColor: "rgba(246, 194, 62, 1)",
      pointHoverRadius: 2,
      pointHoverBackgroundColor: "rgba(246, 194, 62, 1)",
      pointHoverBorderColor: "rgba(0, 197, 143, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }, {
      label: "Network Transmitted",
      lineTension: 0,
      backgroundColor: "rgba(244, 204, 9, 0.05)",
      borderColor: "rgba(244, 204, 9, 1)",
      pointRadius: 0,
      pointBackgroundColor: "rgba(244, 204, 9, 1)",
      pointBorderColor: "rgba(244, 204, 9, 1)",
      pointHoverRadius: 2,
      pointHoverBackgroundColor: "rgba(244, 204, 9, 1)",
      pointHoverBorderColor: "rgba(0, 197, 143, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }],
  };
  var options = {
    animation: false,
    plugins: {
      datalabels: {
        formatter: function () {
          return null; // Hide datalabels for this chart
        },
      }
    },
    maintainAspectRatio: false,
    layout: {
      padding: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 10
        }
      }],
      yAxes: [{
        scaleLabel: {
          display: false,
          labelString: '네트워크 사용량'
        },
        ticks: {
          min: 0,
          max: 10000,
          maxTicksLimit: 10,
          padding: 10,
          // Include a percent sign in the ticks
          callback: function (value, index, values) {
            return number_format(value) + "KB";
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(255, 236, 244)",
          drawBorder: true,
          borderDash: [0],
          zeroLineBorderDash: [0]
        }
      }]
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#6DC58F',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function (tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ': ' + tooltipItem.yLabel + 'KB';
        }
      }
    }
  };
  var myNet = new Chart(ctx, {
    type: 'line',
    data: data,
    options: options
  });

  setInterval(function () {
    setData(data.datasets[0].data, data.datasets[1].data);
    var myNet = new Chart(ctx, {
      type: 'line',
      data: data,
      options: options
    })
  }, 1500);

  function setData(data_in, data_out) {
    $.ajax({
      url: "/dashboard/status/",
      headers: {
        'X-CSRFToken': getCookie()
      },
      type: "post",
      data: {
        "data": 'network'
      },
      success: function (response) {
        response = JSON.parse(response);
        network_in_percent = response.in
        network_out_percent = response.out
      }
    });
    setTimeout(function(){
      data_in.shift();
      data_in.push(network_in_percent);
      data_out.shift();
      data_out.push(network_out_percent);
    }, 500)
    
    //$('#NET_In').text(network_in_percent);
    //$('#NET_Out').text(network_out_percent);
  };
});


//=================================================================== DASHBOARD CPU USAGE
$(document).ready(function () {
  var ctx = document.getElementById("myCPU").getContext("2d");
  var data = {
    labels: ["", "", "", "", "", ""],
    datasets: [{
      label: "CPU Usage",
      lineTension: 0,
      backgroundColor: "rgba(78, 115, 223, 0.05)",
      borderColor: "rgba(78, 115, 223, 1)",
      pointRadius: 0,
      pointBackgroundColor: "rgba(78, 115, 223, 1)",
      pointBorderColor: "rgba(78, 115, 223, 1)",
      pointHoverRadius: 2,
      pointHoverBackgroundColor: "rgba(78, 115, 223, 1)",
      pointHoverBorderColor: "rgba(0, 115, 223, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: [0, 0, 0, 0, 0, 0, 0]
    }],
  };
  var options = {
    animation: false,
    maintainAspectRatio: false,
    plugins: {
      datalabels: {
        formatter: function () {
          return null; // Hide datalabels for this chart
        },
      }
    },
    layout: {
      padding: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 7
        }
      }],
      yAxes: [{
        scaleLabel: {
          display: false,
          labelString: 'CPU 사용량'
        },
        ticks: {
          min: 0,
          max: 100,
          maxTicksLimit: 10,
          padding: 10,
          // Include a percent sign in the ticks
          callback: function (value, index, values) {
            return number_format(value) + "%";
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(255, 236, 244)",
          drawBorder: true,
          borderDash: [0],
          zeroLineBorderDash: [0]
        }
      }]
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#6b74cf',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function (tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ': ' + number_format(tooltipItem.yLabel) + '%';
        }
      }
    }
  };
  var myCPU = new Chart(ctx, {
    type: 'line',
    data: data,
    options: options
  });

  setInterval(function () {
    setData(data.datasets[0].data);
    var myCPU = new Chart(ctx, {
      type: 'line',
      data: data,
      options: options
    })
  }, 1500);

  function setData(data) {
    $.ajax({
      url: "/dashboard/status/",
      headers: {
        'X-CSRFToken': getCookie()
      },
      data: {
        "data": "cpu"
      },
      type: "post",
      success: function (result) {
        result = JSON.parse(result);
        cpu_percent = result.cpu;
      }
    });
    setTimeout(function(){
      data.shift();
      data.push(cpu_percent);
    }, 500);
    //$('#CPU').text(cpu_percent);
  };
});

//====================================================================================mem usage
$(document).ready(function () {
  var ctx = document.getElementById("myMem").getContext("2d");
  var data = {
    labels: ["", "", "", "", "", "", "", "", ""],
    datasets: [{
      label: "Memory Usage",
      lineTension: 0,
      backgroundColor: "rgba(109, 197, 143, 0.05)",
      borderColor: "rgba(109, 197, 143, 1)",
      pointRadius: 0,
      pointBackgroundColor: "rgba(109, 197, 143, 1)",
      pointBorderColor: "rgba(109, 197, 143, 1)",
      pointHoverRadius: 2,
      pointHoverBackgroundColor: "rgba(109, 197, 143, 1)",
      pointHoverBorderColor: "rgba(0, 197, 143, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }],
  };
  var options = {
    animation: false,
    maintainAspectRatio: false,
    plugins: {
      datalabels: {
        formatter: function () {
          return null; // Hide datalabels for this chart
        },
      }
    },
    layout: {
      padding: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 10
        }
      }],
      yAxes: [{
        scaleLabel: {
          display: false,
          labelString: '메모리 사용량'
        },
        ticks: {
          min: 0,
          max: 100,
          maxTicksLimit: 10,
          padding: 10,
          // Include a percent sign in the ticks
          callback: function (value, index, values) {
            return number_format(value) + "%";
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(255, 236, 244)",
          drawBorder: true,
          borderDash: [0],
          zeroLineBorderDash: [0]
        }
      }]
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#6DC58F',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function (tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ': ' + tooltipItem.yLabel + '%';
        }
      }
    }
  };

  setInterval(function () {
    setData(data.datasets[0].data);
    var myMem = new Chart(ctx, {
      type: 'line',
      data: data,
      options: options
    })
  }, 1500);

  function setData(data) {
    $.ajax({
      url: "/dashboard/status/",
      headers: {
        'X-CSRFToken': getCookie()
      },
      type: "post",
      data: {
        "data": 'memory'
      },
      success: function (result) {
        result = JSON.parse(result);
        mem_percent = result.memory
        mem = Math.round(result.memory * 1000) / 1000;
      }
    });
    setTimeout(function(){
      data.shift();
      data.push(mem_percent);
    }, 500);
    //$('#mem').text(mem);
  };
});

//==================================================================================== disk usage
$(document).ready(function () {
  var ctx = document.getElementById("myDISK").getContext("2d");
  var data = {
    labels: ["", "", "", "", "", "", "", "", ""],
    datasets: [{
      label: "Disk Usage",
      lineTension: 0,
      backgroundColor: "rgba(112, 183, 201, 0.05)",
      borderColor: "rgba(112, 183, 201, 1)",
      pointRadius: 0,
      pointBackgroundColor: "rgba(112, 183, 201, 1)",
      pointBorderColor: "rgba(112, 183, 201, 1)",
      pointHoverRadius: 2,
      pointHoverBackgroundColor: "rgba(112, 183, 201, 1)",
      pointHoverBorderColor: "rgba(0, 183, 201, 1)",
      pointHitRadius: 10,
      pointBorderWidth: 2,
      data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }],
  };
  var options = {
    animation: false,
    maintainAspectRatio: false,
    plugins: {
      datalabels: {
        formatter: function () {
          return null; // Hide datalabels for this chart
        },
      }
    },
    layout: {
      padding: {
        left: 0,
        right: 0,
        top: 0,
        bottom: 0
      }
    },
    scales: {
      xAxes: [{
        time: {
          unit: 'date'
        },
        gridLines: {
          display: false,
          drawBorder: false
        },
        ticks: {
          maxTicksLimit: 10
        }
      }],
      yAxes: [{
        scaleLabel: {
          display: false,
          labelString: 'DISK 사용량'
        },
        ticks: {
          min: 0,
          max: 100,
          maxTicksLimit: 10,
          padding: 10,
          // Include a percent sign in the ticks
          callback: function (value, index, values) {
            return number_format(value) + "%";
          }
        },
        gridLines: {
          color: "rgb(234, 236, 244)",
          zeroLineColor: "rgb(255, 236, 244)",
          drawBorder: true,
          borderDash: [0],
          zeroLineBorderDash: [0]
        }
      }]
    },
    legend: {
      display: false
    },
    tooltips: {
      backgroundColor: "rgb(255,255,255)",
      bodyFontColor: "#858796",
      titleMarginBottom: 10,
      titleFontColor: '#6e707e',
      titleFontSize: 14,
      borderColor: '#70B7C9',
      borderWidth: 1,
      xPadding: 15,
      yPadding: 15,
      displayColors: false,
      intersect: false,
      mode: 'index',
      caretPadding: 10,
      callbacks: {
        label: function (tooltipItem, chart) {
          var datasetLabel = chart.datasets[tooltipItem.datasetIndex].label || '';
          return datasetLabel + ': ' + tooltipItem.yLabel + '%';
        }
      }
    }
  };
  var myDISK = new Chart(ctx, {
    type: 'line',
    data: data,
    options: options
  });

  setInterval(function () {
    setData(data.datasets[0].data);
    var myDISK = new Chart(ctx, {
      type: 'line',
      data: data,
      options: options
    })
  }, 1500);

  function setData(data) {
    $.ajax({
      url: "/dashboard/status/",
      headers: {
        'X-CSRFToken': getCookie()
      },
      type: "post",
      data: {
        "data": 'disk'
      },
      success: function (result) {
        result = JSON.parse(result);
        disk_percent = Math.round(result.disk);
        disk = Math.round(result.disk * 1000) / 1000
      }
    });
    setTimeout(function(){
      data.shift();
      data.push(disk_percent);
    }, 500);
    //$('#DISK').text(disk);
  };
});

