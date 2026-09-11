import { chartData, chartOptions, getJSON, labelFor, numeric, palette } from "./api-client.js";

const panels = [...document.querySelectorAll("[data-chart-panel]")];
const status = document.querySelector("[data-dashboard-status]");
const insightList = document.querySelector("[data-insight-list]");

function buildChart(panel, rows) {
  const dimension = panel.dataset.dimension;
  const metrics = JSON.parse(panel.dataset.metrics || "[]");
  const type = panel.dataset.chartType || "bar";
  const data = chartData(rows, dimension, metrics);

  if (type === "doughnut" && data.datasets.length === 1) {
    data.datasets[0].backgroundColor = rows.map((_, index) => palette[index % palette.length]);
    data.datasets[0].borderColor = "#fbfaf5";
  }

  const canvas = panel.querySelector("canvas");
  new Chart(canvas, { type, data, options: chartOptions(type) });
  const primaryMetric = metrics.at(-1);
  const total = rows.reduce((sum, row) => sum + numeric(row[primaryMetric]), 0);
  panel.querySelector("[data-chart-total]").textContent = `${total.toLocaleString()} ${labelFor(primaryMetric).toLowerCase()}`;
  panel.classList.add("is-ready");

  if (!rows.length) return null;
  const top = [...rows].sort((a, b) => numeric(b[primaryMetric]) - numeric(a[primaryMetric]))[0];
  return `${top[dimension] ?? "Unknown"} leads ${panel.querySelector("h2").textContent.toLowerCase()} at ${numeric(top[primaryMetric]).toLocaleString()}.`;
}

async function loadPanel(panel) {
  try {
    const payload = await getJSON(panel.dataset.endpoint);
    return { insight: buildChart(panel, payload.data), source: payload.meta?.source };
  } catch (error) {
    panel.classList.add("is-error");
    panel.querySelector("[data-chart-state]").textContent = error.message;
    return { insight: null, error };
  }
}

async function initialize() {
  const results = await Promise.all(panels.map(loadPanel));
  const failures = results.filter((result) => result.error).length;
  const source = results.find((result) => result.source)?.source;
  status.textContent = failures
    ? `${panels.length - failures} of ${panels.length} reports available`
    : `${panels.length} reports loaded${source ? ` from ${source}` : ""}`;
  const insights = results.map((result) => result.insight).filter(Boolean);
  insightList.replaceChildren(
    ...insights.map((text) => {
      const item = document.createElement("li");
      item.textContent = text;
      return item;
    }),
  );
}

initialize();
