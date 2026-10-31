document.addEventListener("DOMContentLoaded", () => {
  const typeSelect = document.getElementById("reportType");
  const propertySelect = document.getElementById("reportProperty");
  const periodSelect = document.getElementById("reportPeriod");
  const searchInput = document.getElementById("reportSearch");
  const applyButton = document.getElementById("applyReport");
  const exportButton = document.getElementById("exportCsv");
  const tables = [...document.querySelectorAll("[data-report-table]")];
  const heading = document.getElementById("reportHeading");
  const resultCount = document.getElementById("reportResultCount");

  if (
    !typeSelect || !propertySelect || !periodSelect || !searchInput
    || !applyButton || !exportButton || !tables.length
  ) {
    return;
  }

  const labels = {
    activities: "Atividades",
    inputs: "Insumos",
    properties: "Propriedades",
  };
  const activeTable = () => tables.find(table => table.dataset.reportTable === typeSelect.value);

  const applyFilters = () => {
    const table = activeTable();
    tables.forEach(item => { item.hidden = item !== table; });
    propertySelect.disabled = typeSelect.value !== "activities";
    periodSelect.disabled = typeSelect.value !== "activities";

    if (!table) return;
    const property = propertySelect.value;
    const period = Number(periodSelect.value);
    const cutoff = period ? new Date() : null;
    if (cutoff) cutoff.setDate(cutoff.getDate() - period);
    const query = searchInput.value.trim().toLocaleLowerCase("pt-BR");
    let visibleRows = 0;

    table.querySelectorAll("tbody tr").forEach(row => {
      const emptyRow = row.cells.length === 1;
      const rowDate = row.dataset.date ? new Date(`${row.dataset.date}T00:00:00`) : null;
      const matchesProperty = typeSelect.value !== "activities"
        || property === "all"
        || row.dataset.property === property;
      const matchesPeriod = !cutoff || !rowDate || rowDate >= cutoff;
      const matchesSearch = emptyRow || row.innerText.toLocaleLowerCase("pt-BR").includes(query);
      row.hidden = !(matchesProperty && matchesPeriod && matchesSearch);
      if (!row.hidden && !emptyRow) visibleRows += 1;
    });

    if (heading) heading.textContent = labels[typeSelect.value] || "Relatório";
    if (resultCount) resultCount.textContent = `${visibleRows} registro(s)`;
    exportButton.textContent = `⇩ Exportar ${labels[typeSelect.value] || "relatório"} CSV`;
  };

  applyButton.addEventListener("click", applyFilters);
  typeSelect.addEventListener("change", applyFilters);
  searchInput.addEventListener("input", applyFilters);
  propertySelect.addEventListener("change", applyFilters);
  periodSelect.addEventListener("change", applyFilters);

  exportButton.addEventListener("click", () => {
    const table = activeTable();
    if (!table) return;

    const rows = [...table.querySelectorAll("tr")]
      .filter(row => !row.hidden && !(row.closest("tbody") && row.cells.length === 1));
    const csv = rows.map(row => [...row.querySelectorAll("th, td")]
      .map(cell => `"${cell.innerText.replace(/"/g, '""').replace(/\s+/g, " ").trim()}"`)
      .join(";"))
      .join("\r\n");
    const blob = new Blob(["\ufeff", csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `agrodados-${typeSelect.value}.csv`;
    anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
  });

  applyFilters();
});
