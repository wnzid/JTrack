import { chartOptions, getJSON, labelFor, numeric, palette } from "./api-client.js";

const root = document.querySelector("#builder");
const container = root.querySelector("[data-views]");
const template = root.querySelector("#view-template");
const status = root.querySelector("[data-builder-status]");
const storageKey = "jtrack.saved-views.v2";
let rows = [];
let columns = [];

function isNumericColumn(key) {
  const values = rows.map((row) => row[key]).filter((value) => value !== null && value !== "").slice(0, 50);
  return values.length > 0 && values.every((value) => Number.isFinite(Number(value)));
}

function fillSelect(select, options) {
  select.replaceChildren(...options.map(({ value, label }) => new Option(label, value)));
}

function aggregate(dimension, measure) {
  const groups = new Map();
  rows.forEach((row) => {
    const key = String(row[dimension] ?? "Unknown").trim() || "Unknown";
    groups.set(key, (groups.get(key) || 0) + (measure === "count" ? 1 : numeric(row[measure])));
  });
  return [...groups.entries()].sort((a, b) => b[1] - a[1]).slice(0, 18);
}

function serialize() {
  return [...container.querySelectorAll(".builder-card")].map((card) => ({
    title: card.querySelector(".title-input").value,
    dimension: card.querySelector("[data-dimension]").value,
    measure: card.querySelector("[data-measure]").value,
    type: card.querySelector("[data-type]").value,
  }));
}

function save() {
  localStorage.setItem(storageKey, JSON.stringify(serialize()));
}

function render(card) {
  const dimension = card.querySelector("[data-dimension]").value;
  const measure = card.querySelector("[data-measure]").value;
  const type = card.querySelector("[data-type]").value;
  const values = aggregate(dimension, measure);
  const canvas = card.querySelector("canvas");
  card._chart?.destroy();
  card._chart = new Chart(canvas, {
    type,
    data: {
      labels: values.map(([label]) => label),
      datasets: [{
        label: measure === "count" ? "Records" : labelFor(measure),
        data: values.map(([, value]) => value),
        backgroundColor: type === "doughnut" ? values.map((_, index) => palette[index % palette.length]) : palette[0],
        borderColor: type === "doughnut" ? "#ffffff" : palette[0],
        borderWidth: 2,
        tension: .28,
      }],
    },
    options: chartOptions(type),
  });
  card.classList.add("is-ready");
  save();
}

function addView(config = {}) {
  const card = template.content.firstElementChild.cloneNode(true);
  const dimensionSelect = card.querySelector("[data-dimension]");
  const measureSelect = card.querySelector("[data-measure]");
  fillSelect(dimensionSelect, columns.map((key) => ({ value: key, label: labelFor(key) })));
  fillSelect(measureSelect, [
    { value: "count", label: "Record count" },
    ...columns.filter(isNumericColumn).map((key) => ({ value: key, label: `Sum of ${labelFor(key)}` })),
  ]);
  card.querySelector(".title-input").value = config.title || "Untitled view";
  if (columns.includes(config.dimension)) dimensionSelect.value = config.dimension;
  if ([...measureSelect.options].some((option) => option.value === config.measure)) measureSelect.value = config.measure;
  card.querySelector("[data-type]").value = config.type || "bar";
  card.querySelector("[data-render]").addEventListener("click", () => render(card));
  card.querySelector("[data-remove]").addEventListener("click", () => { card.remove(); save(); });
  card.querySelector(".title-input").addEventListener("change", save);
  card.querySelector("[data-download]").addEventListener("click", () => {
    if (!card._chart) return;
    const link = document.createElement("a");
    link.href = card._chart.toBase64Image("image/png", 1);
    link.download = `${card.querySelector(".title-input").value.trim().replace(/[^a-z0-9]+/gi, "-").toLowerCase() || "jtrack-view"}.png`;
    link.click();
  });
  container.append(card);
  if (config.dimension) render(card);
  save();
}

async function initialize() {
  try {
    const payload = await getJSON(root.dataset.endpoint);
    rows = payload.data;
    columns = payload.meta?.columns || Object.keys(rows[0] || {});
    const total = payload.meta?.total ?? rows.length;
    status.textContent = `${rows.length.toLocaleString()} of ${total.toLocaleString()} records available from ${payload.meta?.source || "the connected source"}.`;
    const saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
    if (saved.length) saved.forEach(addView);
    else addView({ dimension: columns[0], measure: "count", type: "bar", title: "Records by category" });
  } catch (error) {
    status.textContent = error.message;
  }
}

root.querySelector("[data-add-view]").addEventListener("click", () => addView());
root.querySelector("[data-reset]").addEventListener("click", () => {
  container.replaceChildren();
  localStorage.removeItem(storageKey);
  addView({ dimension: columns[0], measure: "count", type: "bar", title: "Records by category" });
});
initialize();
