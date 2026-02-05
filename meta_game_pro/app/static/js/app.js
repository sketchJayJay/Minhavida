(function(){
  // Dashboard chart
  if (window.__chart && document.getElementById("netChart")){
    const ctx = document.getElementById("netChart");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: window.__chart.labels,
        datasets: [{
          label: "Saldo do dia (R$)",
          data: window.__chart.net,
          tension: 0.25
        }]
      },
      options: {
        plugins: { legend: { display: true } },
        scales: { y: { beginAtZero: false } }
      }
    });
  }

  // Finance category chart
  if (window.__cat && document.getElementById("catChart")){
    const ctx = document.getElementById("catChart");
    const labels = window.__cat.labels || [];
    const values = window.__cat.values || [];
    new Chart(ctx, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{ label: "R$", data: values }]
      },
      options: { plugins: { legend: { position: "bottom" } } }
    });
  }
})();
