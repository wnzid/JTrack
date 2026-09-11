import { chartData, chartOptions, getJSON, numeric, palette } from "./api-client.js";

const app = document.querySelector("#report-app");
const dimension = app.dataset.dimension;
const metrics = JSON.parse(app.dataset.metrics || "[]");
const columns = JSON.parse(app.dataset.columns || "{}");
const canvas = app.querySelector("canvas");
const status = app.querySelector("[data-report-status]");
const source = app.querySelector("[data-report-source]");
const empty = app.querySelector("[data-empty]");
const tableBody = app.querySelector("tbody");
let rows = [];
let visibleRows = [];
let chart;

function renderChart() {
  const type = app.querySelector("[data-chart-type]").value;
  const data = chartData(visibleRows, dimension, metrics);
  if (type === "doughnut" && data.datasets.length === 1) {
    data.datasets[0].backgroundColor = visibleRows.map((_, index) => palette[index % palette.length]);
    data.datasets[0].borderColor = "#fbfaf5";
  }
  chart?.destroy();
  chart = new Chart(canvas, { type, data, options: chartOptions(type) });
}

function renderTable() {
  tableBody.replaceChildren(
    ...visibleRows.map((row) => {
      const tr = document.createElement("tr");
      Object.keys(columns).forEach((key) => {
        const td = document.createElement("td");
        td.textContent = row[key] ?? "—";
        tr.append(td);
      });
      return tr;
    }),
  );
}

function applyControls() {
  const query = app.querySelector("[data-search]").value.trim().toLowerCase();
  const sort = app.querySelector("[data-sort]").value;
  visibleRows = rows.filter((row) =>
    Object.values(row).some((value) => String(value ?? "").toLowerCase().includes(query)),
  );
  const primaryMetric = metrics.at(-1);
  if (sort === "value-desc") visibleRows.sort((a, b) => numeric(b[primaryMetric]) - numeric(a[primaryMetric]));
  if (sort === "value-asc") visibleRows.sort((a, b) => numeric(a[primaryMetric]) - numeric(b[primaryMetric]));
  if (sort === "label-asc") visibleRows.sort((a, b) => String(a[dimension] ?? "").localeCompare(String(b[dimension] ?? "")));
  status.textContent = `${visibleRows.length.toLocaleString()} of ${rows.length.toLocaleString()} rows`;
  empty.hidden = visibleRows.length > 0;
  app.querySelector("[data-chart-view]").hidden = visibleRows.length === 0 || app.querySelector('[name="display"]:checked').value !== "chart";
  app.querySelector("[data-table-view]").hidden = visibleRows.length === 0 || app.querySelector('[name="display"]:checked').value !== "table";
  renderTable();
  renderChart();
}

function exportCSV() {
  const keys = Object.keys(columns);
  const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const csv = [keys.map((key) => quote(columns[key])).join(","), ...visibleRows.map((row) => keys.map((key) => quote(row[key])).join(","))].join("\n");
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  link.download = `${location.pathname.split("/").filter(Boolean).at(-1) || "jtrack-report"}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

async function initialize() {
  app.querySelector("[data-chart-type]").value = app.dataset.chartType || "bar";
  try {
    const payload = await getJSON(app.dataset.endpoint);
    rows = payload.data;
    source.textContent = `${payload.meta?.source || "source"} / ${new Date(payload.meta?.generated_at || Date.now()).toLocaleString()}`;
    applyControls();
  } catch (error) {
    status.textContent = error.message;
    empty.hidden = false;
    empty.querySelector("strong").textContent = "Report unavailable";
    empty.querySelector("p").textContent = "Check the data source, then try again.";
  }
}

app.querySelector("[data-search]").addEventListener("input", applyControls);
app.querySelector("[data-sort]").addEventListener("change", applyControls);
app.querySelector("[data-chart-type]").addEventListener("change", renderChart);
app.querySelectorAll('[name="display"]').forEach((control) => control.addEventListener("change", applyControls));
app.querySelector("[data-export]").addEventListener("click", exportCSV);
initialize();
