(function(){
  // Manage report interactions, filtering and chart rendering
  let rawData = [];
  let currentSort = '';
  let chart;
  let rangeFrom = null;
  let rangeTo = null;
  let currentType = 'bar';
  const config = window.reportConfig || {};

  function parseDate(d){
    // Convert dd/mm/yyyy strings into Date objects
    if(!d) return null;
    const p = d.split('/');
    if(p.length !== 3) return null;
    return new Date(p[2], p[1]-1, p[0]);
  }

  document.addEventListener('DOMContentLoaded', () => {
    // Fetch dataset and wire UI events when page loads
    fetch(config.endpoint || '/api/data')
      .then(r => r.json())
      .then(data => {
        const dateField = config.dateField || 'StartDate';
        rawData = data.map(r => ({...r, _start: parseDate(r[dateField])}));
        applyFilters();
      });

    initTimePeriodFilter('.time-filter', (from, to) => { rangeFrom = from; rangeTo = to; applyFilters(); });

    document.querySelectorAll('.sort-buttons button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.sort-buttons button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSort = btn.dataset.sort;
        applyFilters();
      });
    });

    document.querySelectorAll('.intake-buttons button').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.classList.toggle('active');
        applyFilters();
      });
    });

    document.querySelectorAll('.chart-btn').forEach(btn => btn.addEventListener('click', () => {
      document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentType = btn.dataset.type;
      if (currentType === 'table') {
        if (chart) chart.destroy();
        document.getElementById('mainChart').classList.add('d-none');
      } else {
        document.getElementById('mainChart').classList.remove('d-none');
      }
      applyFilters();
    }));
  });

  function applyFilters(){
    // Apply date/intake filters then update table and chart
    let data = rawData.slice();
    if(rangeFrom){
      data = data.filter(r => r._start && r._start >= rangeFrom);
    }
    if(rangeTo){
      data = data.filter(r => r._start && r._start <= rangeTo);
    }
    const intakes = Array.from(document.querySelectorAll('.intake-buttons button.active')).map(b => b.dataset.sem);
    if(intakes.length && config.intakeField){
      data = data.filter(r => intakes.includes(r[config.intakeField]));
    }
    if(typeof config.dataFilter === 'function'){
      data = config.dataFilter(data);
    }
    updateTable(data);
    if(currentType !== 'table') drawChart(currentType, data);
  }

  function updateTable(data){
    // Populate table body with filtered rows
    let rows = data.map(r => ({...r}));
    if(config.sortFns && currentSort && config.sortFns[currentSort]){
      rows.sort(config.sortFns[currentSort]);
    }
    const tbody = document.querySelector('#dataTable tbody');
    tbody.innerHTML = '';
    const cols = config.columns || [];
    rows.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = cols.map(c => `<td>${r[c.key] ?? ''}</td>`).join('');
      tbody.appendChild(tr);
    });
  }

  function drawChart(type, data){
    // Render a chart of the filtered data
    const groupKey = config.groupField || (config.columns && config.columns[0] && config.columns[0].key);
    if(!groupKey) return;

    const cols = config.columns || [];
    const valueCols = cols.filter(c => c.key !== groupKey);
    const labels = data.map(r => r[groupKey] || 'Unknown');
    const baseColors = ['#E1122E', '#6290C3', '#06114A', '#454545', '#F4F1DE'];

    let datasets;
    if(valueCols.length <= 1 || type === 'pie' || type === 'doughnut'){
      const field = valueCols[0] ? valueCols[0].key : null;
      const values = field ? data.map(r => Number(r[field]) || 0) : data.map(() => 0);
      const colors = labels.map((_, i) => baseColors[i % baseColors.length]);
      datasets = [{
        label: (valueCols[0] && valueCols[0].label) || config.chartLabel || 'Value',
        data: values,
        backgroundColor: colors
      }];
    } else {
      datasets = valueCols.map((c, idx) => ({
        label: c.label || c.key,
        data: data.map(r => Number(r[c.key]) || 0),
        backgroundColor: baseColors[idx % baseColors.length]
      }));
    }

    if(chart) chart.destroy();
    chart = new Chart(document.getElementById('mainChart'), {
      type: type,
      data: {
        labels: labels,
        datasets: datasets
      },
      options: { indexAxis: 'x', responsive: true }
    });
  }
})();
