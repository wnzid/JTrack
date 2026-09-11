export async function getJSON(url) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return Array.isArray(payload)
    ? { data: payload, meta: { count: payload.length, source: "legacy" } }
    : payload;
}

export const palette = ["#152036", "#bb5a2a", "#1d6754", "#756b8c", "#b18a35", "#4f687d"];

export function labelFor(key) {
  return String(key)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function numeric(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function chartData(rows, dimension, metrics) {
  const labels = rows.map((row) => String(row[dimension] ?? "Unknown"));
  const datasets = metrics.map((metric, index) => ({
    label: labelFor(metric),
    data: rows.map((row) => numeric(row[metric])),
    backgroundColor: palette[index % palette.length],
    borderColor: palette[index % palette.length],
    borderWidth: 2,
    borderRadius: 1,
    tension: 0.28,
  }));
  return { labels, datasets };
}

export function chartOptions(type) {
  const radial = type === "doughnut" || type === "pie";
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 350 },
    plugins: {
      legend: {
        display: radial,
        position: "bottom",
        labels: { color: "#505a68", boxWidth: 10, usePointStyle: true, padding: 16 },
      },
      tooltip: { displayColors: true, padding: 11, cornerRadius: 2 },
    },
    scales: radial
      ? undefined
      : {
          x: { grid: { display: false }, ticks: { color: "#505a68", maxRotation: 0 } },
          y: { beginAtZero: true, border: { display: false }, grid: { color: "#ded9cd" }, ticks: { color: "#505a68", precision: 0 } },
        },
  };
}
