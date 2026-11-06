(() => {
  const search = document.getElementById('search');
  const status = document.getElementById('status-filter');
  const rows = [...document.querySelectorAll('.image-section')];
  const filter = () => {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    for (const row of rows) {
      row.hidden = !row.dataset.search.includes(query) ||
        (status.value !== 'all' && !row.dataset.status.split(" ").includes(status.value));
      if (!row.hidden) visible++;
    }
    document.getElementById('result-count').textContent = `${visible} images shown`;
    document.getElementById('empty-state').hidden = visible !== 0;
  };
  search.addEventListener('input', filter);
  status.addEventListener('change', filter);
  filter();
})();
