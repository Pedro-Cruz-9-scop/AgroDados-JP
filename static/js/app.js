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
      table.querySelectorAll("tbody tr").forEach(row => row.style.display = row.innerText.toLocaleLowerCase("pt-BR").includes(q) ? "" : "none");
    });
  });

  const exportButton = document.getElementById("exportCsv");
  if (exportButton) exportButton.addEventListener("click", () => {
    const table = document.getElementById("reportTable");
    if (!table) return;
    const rows = [...table.querySelectorAll("tr")].filter(r => r.style.display !== "none");
    const csv = rows.map(row => [...row.querySelectorAll("th,td")].map(cell => '"' + cell.innerText.replace(/"/g, '""').replace(/\s+/g, ' ').trim() + '"').join(";")).join("\r\n");
    const blob = new Blob(["\ufeff" + csv], {type: "text/csv;charset=utf-8;"});
    const url = URL.createObjectURL(blob); const a = document.createElement("a");
    a.href = url; a.download = "agrodados-relatorio.csv"; a.click(); URL.revokeObjectURL(url);
  });
  const apply = document.getElementById("applyReport");
  if (apply) apply.addEventListener("click", () => {
    const prop = document.getElementById("reportProperty").value;
    document.querySelectorAll("#reportTable tbody tr").forEach(row => {
      row.style.display = prop === "all" || row.dataset.property === prop ? "" : "none";
    });
  });
});
