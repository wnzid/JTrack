


document.addEventListener("DOMContentLoaded", function() {
  fetch("/api/current-vs-enrolled")
    .then(r => r.json())
    .then(d => {
      new Chart(document.getElementById("chart-current-enrolled"), {
        type: "line",
        data: {
          labels: d.map(x => x.term),
          datasets: [
            { label: "Current Students", data: d.map(x => x.current_students), fill: false },
            { label: "Enrolled", data: d.map(x => x.enrolled), fill: false }
          ]
        },
        options: { responsive: true }
      });
    })
    .catch(e => console.error("current-vs-enrolled", e));

  fetch("/api/enrolled-vs-offer")
    .then(r => r.json())
    .then(d => {
      new Chart(document.getElementById("chart-enrolled-offer"), {
        type: "bar",
        data: {
          labels: d.map(x => x.term),
          datasets: [
            { label: "Offers", data: d.map(x => x.offers) },
            { label: "Enrolled", data: d.map(x => x.enrolled) }
          ]
        },
        options: { responsive: true }
      });
    })
    .catch(e => console.error("enrolled-vs-offer", e));

  fetch("/api/visa-breakdown")
    .then(r => r.json())
    .then(d => {
      new Chart(document.getElementById("chart-visa-breakdown"), {
        type: "doughnut",
        data: {
          labels: d.map(x => x.visa_type),
          datasets: [{ data: d.map(x => x.total) }]
        },
        options: { responsive: true }
      });
    })
    .catch(e => console.error("visa-breakdown", e));

  fetch("/api/offer-expiry-surge")
    .then(r => r.json())
    .then(d => {
      new Chart(document.getElementById("chart-offer-expiry-surge"), {
        type: "line",
        data: {
          labels: d.map(x => x.expiry_day),
          datasets: [{ label: "Expiring Offers", data: d.map(x => x.expiring_offers), fill: false }]
        },
        options: { responsive: true }
      });
    })
    .catch(e => console.error("offer-expiry-surge", e));
});
