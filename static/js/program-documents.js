document.addEventListener("DOMContentLoaded", () => {
  const addButton = document.querySelector("#add-document-requirement");
  const rows = document.querySelector("[data-document-rows]");
  const emptyForm = document.querySelector("#empty-document-form");
  const totalForms = document.querySelector("#id_requirements-TOTAL_FORMS");

  if (!addButton || !rows || !emptyForm || !totalForms) return;

  addButton.addEventListener("click", () => {
    const formIndex = Number(totalForms.value);
    const row = document.createElement("fieldset");
    row.className = "program-document-row";
    row.innerHTML = `<legend>Документ ${formIndex + 1}</legend>${emptyForm.innerHTML.replaceAll("__prefix__", String(formIndex))}`;
    rows.append(row);
    totalForms.value = String(formIndex + 1);
    row.querySelector("input, select")?.focus();
  });
});