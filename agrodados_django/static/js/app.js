document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (toggle && sidebar) toggle.addEventListener("click", () => sidebar.classList.toggle("open"));

  document.querySelectorAll("[data-modal-open]").forEach(btn => {
    btn.addEventListener("click", () => {
      const modal = document.getElementById(btn.dataset.modalOpen);
      if (modal) modal.classList.add("show");
    });
  });
  document.querySelectorAll("[data-modal-close]").forEach(btn => {
    btn.addEventListener("click", () => btn.closest(".modal-backdrop")?.classList.remove("show"));
  });
  document.querySelectorAll(".modal-backdrop").forEach(modal => {
    modal.addEventListener("click", e => { if (e.target === modal) modal.classList.remove("show"); });
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") document.querySelectorAll(".modal-backdrop.show").forEach(m => m.classList.remove("show"));
  });

  document.querySelectorAll("[data-table-search]").forEach(input => {
    input.addEventListener("input", () => {
      const table = input.closest(".panel")?.querySelector("table[data-search-table]") || document.querySelector("table[data-search-table]");
      if (!table) return;
      const q = input.value.toLocaleLowerCase("pt-BR");
      table.querySelectorAll("tbody tr").forEach(row => {
        const matchesSearch = row.innerText.toLocaleLowerCase("pt-BR").includes(q);
        const matchesReport = row.dataset.reportVisible !== "false";
        row.style.display = matchesSearch && matchesReport ? "" : "none";
      });
      updateReportSummary();
    });
  });

  const exportButton = document.getElementById("exportCsv");
  if (exportButton) exportButton.addEventListener("click", () => {
    const table = document.getElementById("reportTable");
    if (!table) return;
    const rows = [...table.querySelectorAll("tr")].filter(r => r.style.display !== "none");
    if (rows.length <= 1 && rows[0]?.querySelectorAll("th").length === 0) return;
    const csv = rows.map(row => [...row.querySelectorAll("th,td")].map(cell => '"' + cell.innerText.replace(/"/g, '""').replace(/\s+/g, ' ').trim() + '"').join(";")).join("\r\n");
    const blob = new Blob(["\ufeff" + csv], {type: "text/csv;charset=utf-8;"});
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = "agrodados-relatorio.csv"; document.body.appendChild(a); a.click(); a.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  const apply = document.getElementById("applyReport");
  if (apply) apply.addEventListener("click", applyReportFilters);

  function applyReportFilters() {
    const table = document.getElementById("reportTable");
    if (!table) return;
    const property = document.getElementById("reportProperty")?.value || "all";
    const period = document.getElementById("reportPeriod")?.value || "all";
    const cutoff = new Date();
    cutoff.setHours(0, 0, 0, 0);
    if (period !== "all") cutoff.setDate(cutoff.getDate() - (Number(period) - 1));

    table.querySelectorAll("tbody tr").forEach(row => {
      const date = row.dataset.date ? new Date(`${row.dataset.date}T00:00:00`) : null;
      const matchesProperty = property === "all" || row.dataset.property === property;
      const matchesPeriod = period === "all" || (date && !Number.isNaN(date.getTime()) && date >= cutoff);
      row.dataset.reportVisible = String(matchesProperty && matchesPeriod);
      const search = document.querySelector("#reportTable")?.closest(".panel")?.querySelector("[data-table-search]");
      const query = search?.value.toLocaleLowerCase("pt-BR") || "";
      row.style.display = matchesProperty && matchesPeriod && row.innerText.toLocaleLowerCase("pt-BR").includes(query) ? "" : "none";
    });
    updateReportSummary();
  }

  function updateReportSummary() {
    const table = document.getElementById("reportTable");
    if (!table) return;
    const visibleRows = [...table.querySelectorAll("tbody tr")].filter(row => row.style.display !== "none" && row.dataset.type);
    const count = document.querySelector("[data-report-count]");
    if (count) count.textContent = String(visibleRows.length);
    const chartItems = [...document.querySelectorAll("#activityChart [data-chart-type]")];
    const counts = new Map(chartItems.map(item => [
      item.dataset.chartType,
      visibleRows.filter(row => row.dataset.type === item.dataset.chartType).length
    ]));
    const max = Math.max(0, ...counts.values());
    chartItems.forEach(item => {
      const typeCount = counts.get(item.dataset.chartType);
      const bar = item.querySelector("[data-chart-bar]");
      const value = item.querySelector("[data-chart-count]");
      if (bar) bar.style.width = max ? `${Math.round(typeCount / max * 100)}%` : "0%";
      if (value) value.textContent = String(typeCount);
    });
  }
});
