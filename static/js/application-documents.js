document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".application-submit-form");
  const programSelect = form?.querySelector("#id_program");
  const documentPanel = form?.querySelector("#application-documents");
  const fields = documentPanel?.querySelector("[data-document-fields]");
  if (!form || !programSelect || !documentPanel || !fields) return;
  const text = form.dataset;

  const renderRequirements = (requirements) => {
    fields.replaceChildren();
    if (requirements.length === 0) {
      const empty = document.createElement("p");
      empty.className = "application-documents-empty";
      empty.textContent = text.documentsNone;
      fields.append(empty);
      return;
    }

    requirements.forEach((requirement) => {
      const wrapper = document.createElement("div");
      const label = document.createElement("label");
      const required = document.createElement("span");
      const input = document.createElement("input");
      const format = document.createElement("small");

      wrapper.className = "application-document-field";
      label.htmlFor = `document-${requirement.id}`;
      label.append(document.createTextNode(requirement.name));
      required.textContent = requirement.required ? text.documentsRequired : text.documentsOptional;
      label.append(" ", required);

      input.id = `document-${requirement.id}`;
      input.type = "file";
      input.name = `document_${requirement.id}`;
      input.accept = requirement.format === "jpg" ? ".jpg,.jpeg" : `.${requirement.format}`;
      input.required = requirement.required;

      format.textContent = `${text.documentsFormat}: ${requirement.format_label}`;
      wrapper.append(label, input, format);
      fields.append(wrapper);
    });
  };

  programSelect.addEventListener("change", async () => {
    const programId = programSelect.value;
    documentPanel.dataset.programId = programId;
    if (!programId) {
      fields.replaceChildren();
      return;
    }

    const url = form.dataset.requirementsUrl.replace(/\/0\/documents\/$/, `/${programId}/documents/`);
    const status = document.createElement("p");
    status.className = "application-documents-loading";
    status.setAttribute("role", "status");
    status.textContent = text.documentsLoading;
    fields.replaceChildren(status);

    try {
      const response = await fetch(url, {
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("Requirements request failed");
      const result = await response.json();
      if (documentPanel.dataset.programId !== programId) return;
      renderRequirements(result.requirements);
    } catch {
      if (documentPanel.dataset.programId !== programId) return;
      status.textContent = text.documentsError;
    }
  });
});