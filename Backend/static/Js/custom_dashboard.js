// Fetch dataset and allow users to build custom charts with filters
let dataset = [];
let columns = [];

async function init() {
  try {
    const res = await fetch('/api/data');
    dataset = await res.json();
    if (dataset.length) {
      columns = Object.keys(dataset[0]);
    }
    document.getElementById('addChart').addEventListener('click', addChartCard);
    document.getElementById('resetDashboard').addEventListener('click', resetDashboard);
    document.getElementById('saveDashboard').addEventListener('click', saveDashboard);
    // create first chart by default
    addChartCard();
  } catch (err) {
    console.error('Failed to load data', err);
  }
}

function createSelect(options, className) {
  const sel = document.createElement('select');
  sel.className = `form-select ${className}`;
  options.forEach(opt => {
    const o = document.createElement('option');
    o.value = opt;
    o.textContent = opt;
    sel.appendChild(o);
  });
  return sel;
}

function populateFieldSelect(select) {
  select.innerHTML = '';
  columns.forEach(col => {
    const opt = document.createElement('option');
    opt.value = col;
    opt.textContent = col;
    select.appendChild(opt);
  });
}

function uniqueValues(field) {
  return Array.from(new Set(dataset.map(row => row[field]))).sort();
}

function addFilterRow(filtersContainer) {
  const row = document.createElement('div');
  row.className = 'row g-2 align-items-center filter-row mt-1';

  const fieldCol = document.createElement('div');
  fieldCol.className = 'col';
  const fieldSelect = createSelect(columns, 'filter-field form-select-sm');
  fieldCol.appendChild(fieldSelect);

  const valueCol = document.createElement('div');
  valueCol.className = 'col';
  const valueSelect = document.createElement('select');
  valueSelect.className = 'form-select form-select-sm filter-value';
  valueCol.appendChild(valueSelect);

  const removeCol = document.createElement('div');
  removeCol.className = 'col-auto';
  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-outline-danger btn-sm remove-filter';
  removeBtn.textContent = '\u00d7';
  removeCol.appendChild(removeBtn);

  row.appendChild(fieldCol);
  row.appendChild(valueCol);
  row.appendChild(removeCol);
  filtersContainer.appendChild(row);

  const updateValues = () => {
    const vals = uniqueValues(fieldSelect.value);
    valueSelect.innerHTML = '';
    vals.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      opt.textContent = v;
      valueSelect.appendChild(opt);
    });
  };
  fieldSelect.addEventListener('change', updateValues);
  updateValues();

  removeBtn.addEventListener('click', () => row.remove());
}

function addChartCard() {
  const container = document.getElementById('charts');
  const card = document.createElement('div');
  card.className = 'card mb-3 chart-card';
  const body = document.createElement('div');
  body.className = 'card-body';

  const row = document.createElement('div');
  row.className = 'row g-2';

  const typeCol = document.createElement('div');
  typeCol.className = 'col';
  const typeLabel = document.createElement('label');
  typeLabel.textContent = 'Chart Type';
  const typeSelect = createSelect(['bar', 'line', 'pie'], 'chart-type');
  typeCol.appendChild(typeLabel);
  typeCol.appendChild(typeSelect);

  const xCol = document.createElement('div');
  xCol.className = 'col';
  const xLabel = document.createElement('label');
  xLabel.textContent = 'X-Axis';
  const xSelect = document.createElement('select');
  xSelect.className = 'form-select x-field';
  populateFieldSelect(xSelect);
  xCol.appendChild(xLabel);
  xCol.appendChild(xSelect);

  const yCol = document.createElement('div');
  yCol.className = 'col';
  const yLabel = document.createElement('label');
  yLabel.textContent = 'Y-Axis';
  const ySelect = document.createElement('select');
  ySelect.className = 'form-select y-field';
  populateFieldSelect(ySelect);
  yCol.appendChild(yLabel);
  yCol.appendChild(ySelect);

  row.appendChild(typeCol);
  row.appendChild(xCol);
  row.appendChild(yCol);
  body.appendChild(row);

  const filtersContainer = document.createElement('div');
  filtersContainer.className = 'filters mt-2';
  body.appendChild(filtersContainer);

  const addFilterBtn = document.createElement('button');
  addFilterBtn.type = 'button';
  addFilterBtn.className = 'btn btn-secondary btn-sm mt-2 add-filter';
  addFilterBtn.textContent = 'Add Filter';
  body.appendChild(addFilterBtn);

  const generateBtn = document.createElement('button');
  generateBtn.type = 'button';
  generateBtn.className = 'btn btn-success btn-sm mt-2 ms-2 generate-chart';
  generateBtn.textContent = 'Generate';
  body.appendChild(generateBtn);

  const downloadBtn = document.createElement('button');
  downloadBtn.type = 'button';
  downloadBtn.className = 'btn btn-outline-primary btn-sm mt-2 ms-2 download-chart';
  downloadBtn.textContent = 'Download';
  body.appendChild(downloadBtn);

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-outline-danger btn-sm mt-2 ms-2 remove-chart-card';
  removeBtn.textContent = 'Remove';
  body.appendChild(removeBtn);

  const canvas = document.createElement('canvas');
  canvas.className = 'mt-3 chart';
  body.appendChild(canvas);

  card.appendChild(body);
  container.appendChild(card);

  addFilterBtn.addEventListener('click', () => addFilterRow(filtersContainer));
  generateBtn.addEventListener('click', () => buildChart(card, canvas));
  downloadBtn.addEventListener('click', () => {
    const link = document.createElement('a');
    link.href = canvas.toDataURL('image/png');
    link.download = 'chart.png';
    link.click();
  });
  removeBtn.addEventListener('click', () => card.remove());
}

function applyFilters(data, card) {
  const filters = Array.from(card.querySelectorAll('.filter-row')).map(row => ({
    field: row.querySelector('.filter-field').value,
    value: row.querySelector('.filter-value').value
  }));
  return data.filter(row => filters.every(f => String(row[f.field]) === f.value));
}

function buildChart(card, canvas) {
  const ctx = canvas.getContext('2d');
  const type = card.querySelector('.chart-type').value;
  const xField = card.querySelector('.x-field').value;
  const yField = card.querySelector('.y-field').value;
  const data = applyFilters(dataset, card);
  const grouped = {};
  data.forEach(row => {
    const key = row[xField];
    if (!grouped[key]) grouped[key] = [];
    grouped[key].push(row[yField]);
  });
  const labels = Object.keys(grouped);
  let values;
  if (data.length && !isNaN(parseFloat(data[0][yField]))) {
    values = labels.map(l => grouped[l].reduce((sum, v) => sum + Number(v), 0));
  } else {
    values = labels.map(l => grouped[l].length);
  }

  if (canvas._chart) {
    canvas._chart.destroy();
  }
  canvas._chart = new Chart(ctx, {
    type,
    data: {
      labels,
      datasets: [{
        label: `${yField} by ${xField}`,
        data: values,
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      scales: type !== 'pie' ? { y: { beginAtZero: true } } : {}
    }
  });
}

function resetDashboard() {
  document.getElementById('charts').innerHTML = '';
}

function saveDashboard() {
  const configs = Array.from(document.querySelectorAll('.chart-card')).map(card => ({
    type: card.querySelector('.chart-type').value,
    xField: card.querySelector('.x-field').value,
    yField: card.querySelector('.y-field').value,
    filters: Array.from(card.querySelectorAll('.filter-row')).map(row => ({
      field: row.querySelector('.filter-field').value,
      value: row.querySelector('.filter-value').value
    }))
  }));
  console.log('Dashboard configuration', configs);
  alert('Dashboard configuration saved to console.');
}

document.addEventListener('DOMContentLoaded', init);
