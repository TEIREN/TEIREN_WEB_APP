// Set new default font family and font color to mimic Bootstrap's default styling
Chart.defaults.global.defaultFontFamily = 'Nunito', '-apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif';
Chart.defaults.global.defaultFontColor = '#858796';

var ctx = document.getElementById("senarioThreat");

(function (Chart) {
    Chart.pluginService.register({ 
        beforeDraw: function (chart) {
            if (chart.config.options.needle) {
                var needleRadius = chart.config.options.needle.radius || 7;
                var centerPoint = {
                    x: chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2,
                    y: chart.chartArea.bottom - (chart.chartArea.bottom - chart.chartArea.top) / 8 //.top + (chart.chartArea.bottom - chart.chartArea.top) / 2
                };
                var meta = chart.getDatasetMeta(0);
                var currentValue = chart.config.options.needle.currentValue || 0;
                var totalDatasetValues = chart.data.datasets[0].data.reduce((a, b) => a + b);
                var angle = ((currentValue / totalDatasetValues) * Math.PI * 2) - (Math.PI / 2);
                var needleX = centerPoint.x + Math.cos(angle) * meta.controller.outerRadius * 0.8; // needle length
                var needleY = centerPoint.y + Math.sin(angle) * meta.controller.outerRadius * 0.8; // needle length

                // Needle Animation
                const needleOptions = chart.config.options.needle;
                const targetValue = senario_threat["degree"];
                const step = (targetValue - currentValue)/20; // Adjust the divisor to control the speed of animation

                if (Math.abs(step) > 0.00000001) {
                    needleOptions.currentValue = currentValue + step;
                    chart.update();
                }

                // Draw round base
                chart.chart.ctx.beginPath();
                chart.chart.ctx.arc(centerPoint.x, centerPoint.y, needleRadius, 0, Math.PI * 2);
                chart.chart.ctx.closePath();
                chart.chart.ctx.fillStyle = senario_threat['color']; // centerpointer color
                chart.chart.ctx.fill();

                // Calculate additional points for the triangular needle
                var theta = Math.PI / 5; // needle thinkness
                var needleStartLeftX = centerPoint.x + Math.cos(angle + theta) * (needleRadius * 0.6);
                var needleStartLeftY = centerPoint.y + Math.sin(angle + theta) * (needleRadius * 0.6);
                var needleStartRightX = centerPoint.x + Math.cos(angle - theta) * (needleRadius * 0.6);
                var needleStartRightY = centerPoint.y + Math.sin(angle - theta) * (needleRadius * 0.6);

                // Draw triangular needle
                chart.chart.ctx.beginPath();
                chart.chart.ctx.moveTo(needleStartLeftX, needleStartLeftY);
                chart.chart.ctx.lineTo(needleX, needleY);
                chart.chart.ctx.lineTo(needleStartRightX, needleStartRightY);
                chart.chart.ctx.closePath();
                chart.chart.ctx.fillStyle = senario_threat['color']; // needle color
                chart.chart.ctx.fill();

            }
        }
    });
})(Chart);

var myPieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['정상', '주의', '경계', '심각'],
        datasets: [{
            data: [1, 1, 1, 1],
            backgroundColor: ['#1cc88a', '#f6c23e', '#fd7e14', '#e74a3b'],
            //hoverBackgroundColor: ['#2e59d9', '#17a673', '#2c9faf'],
            //hoverBorderColor: "rgba(234, 236, 244, 1)",
        }],
    },
    options: {
        maintainAspectRatio: false,
        needle: {
            // currentValue: senario_threat['degree'],
            currentValue: 3,
        },
        tooltips: {
            enabled: false
        },
        legend: {
            display: false
        },
        cutoutPercentage: 80,
        circumference: Math.PI,
        rotation: - Math.PI,
        plugins: {
            datalabels: {
                anchor: 'center',
                align: 'center',
                color: '#fff',
                formatter: function (value, context) {
                    return context.chart.data.labels[context.dataIndex];
                },
                rotation: function (context) {
                    const index = context.dataIndex;
                    const chart = context.chart;
                    const meta = chart.getDatasetMeta(0);
                    const angle = (meta.data[index]._model.endAngle + meta.data[index]._model.startAngle) / 2;
                    return (angle * (180 / Math.PI)) - 270; // label rotation
                }
            }
        },
    },
});