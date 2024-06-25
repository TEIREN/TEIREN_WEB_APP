Chart.defaults.global.defaultFontFamily = 'Cairo';
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

function number_format(number, decimals, dec_point, thousands_sep) {
  number = (number + '').replace(/[^0-9+\-Ee.]/g, '');
  var n = !isFinite(+number) ? 0 : +number,
    prec = !isFinite(+decimals) ? 0 : Math.abs(decimals),
    sep = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
    dec = (typeof dec_point === 'undefined') ? '.' : dec_point,
    s = '',
    toFixedFix = function (n, prec) {
      var k = Math.pow(10, prec);
      return '' + Math.round(n * k) / k;
    };
  // Fix for IE parseFloat(0.55).toFixed(0) = 0;
  s = (prec ? toFixedFix(n, prec) : '' + Math.round(n)).split('.');
  if (s[0].length > 3) {
    s[0] = s[0].replace(/\B(?=(?:\d{3})+(?!\d))/g, sep);
  }
  if ((s[1] || '').length < prec) {
    s[1] = s[1] || '';
    s[1] += new Array(prec - s[1].length + 1).join('0');
  }
  return s.join(dec);
}





var ctxmemory = document.getElementById("myMem").getContext("2d");
var datamemory = {
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
var optionsmemory = {
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

var myMem = new Chart(ctxmemory, {
  type: 'line',
  data: datamemory,
  options: optionsmemory
})

setInterval(function () {
  setDatamemory(datamemory.datasets[0].data);
  var myMem = new Chart(ctxmemory, {
    type: 'line',
    data: datamemory,
    options: optionsmemory
  })
}, 1500);

function setDatamemory(data) {
  $.ajax({
    url: "/status/",
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
  setTimeout(function () {
    data.shift();
    data.push(mem_percent);
  }, 500);
  //$('#mem').text(mem);
};
