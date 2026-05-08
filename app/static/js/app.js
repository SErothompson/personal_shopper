function toDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function mountPriceChart() {
  const canvas = document.getElementById("priceChart");
  const payload = document.getElementById("chartPoints");
  if (!canvas || !payload || typeof Chart === "undefined") {
    return;
  }

  let points;
  try {
    points = JSON.parse(payload.textContent || "[]");
  } catch (error) {
    console.error("Unable to parse chart points", error);
    return;
  }

  const normalized = points
    .map((point) => {
      const parsedDate = toDate(point.ts);
      if (!parsedDate) {
        return null;
      }
      return { ts: parsedDate, price: Number(point.price) };
    })
    .filter(Boolean)
    .sort((a, b) => a.ts - b.ts);

  if (!normalized.length) {
    return;
  }

  const ctx = canvas.getContext("2d");
  const buttonNodes = Array.from(document.querySelectorAll(".timeline-button"));

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Price",
          data: [],
          borderColor: "#045d56",
          backgroundColor: "rgba(4, 93, 86, 0.12)",
          borderWidth: 2,
          fill: true,
          tension: 0.28,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          ticks: {
            callback(value) {
              return `$${value}`;
            },
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });

  function renderRange(days) {
    const now = new Date();
    const minDate = new Date(now.getTime() - Number(days) * 24 * 60 * 60 * 1000);
    const filtered = normalized.filter((point) => point.ts >= minDate);
    const activeSeries = filtered.length ? filtered : normalized;

    chart.data.labels = activeSeries.map((point) => point.ts.toLocaleDateString());
    chart.data.datasets[0].data = activeSeries.map((point) => point.price);
    chart.update();
  }

  buttonNodes.forEach((button) => {
    button.addEventListener("click", () => {
      buttonNodes.forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      renderRange(button.dataset.range || "30");
    });
  });

  renderRange("30");
}

function focusSearchInput() {
  const searchInput = document.querySelector("[data-search-input]");
  if (!searchInput) {
    return;
  }

  if (!searchInput.value) {
    searchInput.focus();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  mountPriceChart();
  focusSearchInput();
});
