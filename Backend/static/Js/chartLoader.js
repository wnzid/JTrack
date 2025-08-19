import { apiFetch, $, hide, show, setText } from "./dataApi.js";

// Fetch data and render a chart in the given canvas
export async function renderChart({ endpoint, canvas, type, map, options={} }) {
  const state = $("#loading-state", canvas.parentElement) || $("#loading-state");
  const err = $("#error-state", canvas.parentElement) || $("#error-state");
  try {
    if (state) show(state);
    const rows = await apiFetch(endpoint);
    if (state) hide(state);

    const { labels, datasets } = map(rows);

    if (canvas.__chart) { canvas.__chart.destroy(); }

    canvas.__chart = new Chart(canvas, { type, data: { labels, datasets }, options });
    return { rows, labels, datasets, chart: canvas.__chart };
  } catch (e) {
    if (state) hide(state);
    if (err) { setText(err, e.message); show(err); }
    console.error(e);
    return null;
  }
}

