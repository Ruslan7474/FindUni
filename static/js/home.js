document.addEventListener("DOMContentLoaded", () => {
  const registrationForm = document.querySelector(".registration-form");
  if (registrationForm) {
    const nameLabel = registrationForm.querySelector('label[for="id_name"]');
    const lastNameInput = registrationForm.querySelector("#id_last_name");
    const lastNameField = lastNameInput?.closest("p");
    const roleInputs = registrationForm.querySelectorAll('input[name="role"]');
    const updateRegistrationFields = () => {
      const selectedRole = registrationForm.querySelector('input[name="role"]:checked')?.value;
      const isInstitution = selectedRole === "institution";
      nameLabel.textContent = isInstitution ? "Название учебного заведения:" : "Имя:";
      if (lastNameField && lastNameInput) {
        lastNameField.hidden = isInstitution;
        lastNameInput.required = !isInstitution;
      }
    };
    roleInputs.forEach((input) => input.addEventListener("change", updateRegistrationFields));
    updateRegistrationFields();
  }

  const menuButton = document.querySelector(".menu-toggle");
  const mobileNavigation = document.querySelector("#mobile-navigation");

  if (menuButton && mobileNavigation) {
    menuButton.addEventListener("click", () => {
      const isOpen = menuButton.getAttribute("aria-expanded") === "true";
      menuButton.setAttribute("aria-expanded", String(!isOpen));
      menuButton.setAttribute("aria-label", isOpen ? "Открыть меню" : "Закрыть меню");
      mobileNavigation.hidden = isOpen;
      menuButton.querySelector("use").setAttribute("href", isOpen ? "#icon-menu" : "#icon-x");
    });
    mobileNavigation.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        mobileNavigation.hidden = true;
        menuButton.setAttribute("aria-expanded", "false");
      });
    });
  }

  const searchDialog = document.querySelector("#site-search");
  const searchForm = document.querySelector("#site-search-form");
  if (searchDialog && searchForm) {
    const searchInput = document.querySelector("#site-search-input");
    const clearButton = searchDialog.querySelector(".search-dialog-clear");
    const closeButton = searchDialog.querySelector(".search-dialog-close");
    const historyList = searchDialog.querySelector("#search-history-list");
    const historyEmpty = searchDialog.querySelector("#search-history-empty");
    const historyClear = searchDialog.querySelector(".search-history-clear");
    const historyKey = "finduni-search-history";
    const scopeLabelsByLanguage = {
      ru: { university: "Университет", college: "Колледж", student: "Абитуриент" },
      en: { university: "University", college: "College", student: "Applicant" },
      ky: { university: "Университет", college: "Колледж", student: "Абитуриент" },
    };
    const scopeLabels = scopeLabelsByLanguage[document.documentElement.lang] || scopeLabelsByLanguage.ru;
    const scopeButtons = [...searchDialog.querySelectorAll("[data-search-scope]")];
    let activeScope = "university";
    clearButton.hidden = searchInput.value.length === 0;

    const readHistory = () => {
      try {
        const history = JSON.parse(window.localStorage.getItem(historyKey) || "[]");
        return Array.isArray(history) ? history.filter((item) => item && item.query && scopeLabels[item.scope]) : [];
      } catch {
        return [];
      }
    };

    const saveHistory = (query, scope) => {
      const history = readHistory().filter((item) => !(item.query === query && item.scope === scope));
      history.unshift({ query, scope });
      try {
        window.localStorage.setItem(historyKey, JSON.stringify(history.slice(0, 8)));
      } catch {
        return;
      }
    };

    const renderHistory = () => {
      const history = readHistory();
      historyList.replaceChildren();
      historyEmpty.hidden = history.length > 0;
      historyClear.hidden = history.length === 0;

      history.forEach((item) => {
        const button = document.createElement("button");
        const query = document.createElement("span");
        const scope = document.createElement("span");
        button.type = "button";
        button.className = "search-history-item";
        query.textContent = item.query;
        scope.textContent = scopeLabels[item.scope];
        button.append(query, scope);
        button.addEventListener("click", () => runSearch(item.query, item.scope));
        historyList.append(button);
      });
    };

    const setScope = (scope) => {
      activeScope = scope;
      scopeButtons.forEach((button) => {
        const isActive = button.dataset.searchScope === scope;
        button.classList.toggle("is-active", isActive);
        button.setAttribute("aria-pressed", String(isActive));
      });
    };

    const runSearch = (query, scope) => {
      const normalizedQuery = query.trim();
      if (!normalizedQuery) {
        searchInput.focus();
        return;
      }

      const basePath = scope === "student" ? searchForm.dataset.studentsUrl : searchForm.dataset.institutionsUrl;
      const destination = new URL(basePath, window.location.origin);
      destination.searchParams.set("q", normalizedQuery);
      if (scope === "university") destination.searchParams.set("type", "university");
      if (scope === "college") destination.searchParams.delete("type");
      saveHistory(normalizedQuery, scope);
      window.location.href = `${destination.pathname}${destination.search}`;
    };

    document.querySelectorAll(".search-open").forEach((button) => {
      button.addEventListener("click", () => {
        renderHistory();
        searchDialog.showModal();
        searchInput.focus();
      });
    });

    scopeButtons.forEach((button) => {
      button.addEventListener("click", () => setScope(button.dataset.searchScope));
    });

    searchForm.addEventListener("submit", (event) => {
      event.preventDefault();
      runSearch(searchInput.value, activeScope);
    });

    searchInput.addEventListener("input", () => {
      clearButton.hidden = searchInput.value.length === 0;
    });

    clearButton.addEventListener("click", () => {
      searchInput.value = "";
      clearButton.hidden = true;
      searchInput.focus();
    });

    closeButton.addEventListener("click", () => searchDialog.close());
    searchDialog.addEventListener("keydown", (event) => {
      if (event.key === "Escape") searchDialog.close();
    });
    searchDialog.addEventListener("click", (event) => {
      if (event.target === searchDialog) searchDialog.close();
    });
    historyClear.addEventListener("click", () => {
      window.localStorage.removeItem(historyKey);
      renderHistory();
    });
    renderHistory();
  }

  const inboxDialog = document.querySelector("#inbox-dialog");
  if (inboxDialog) {
    const closeInbox = inboxDialog.querySelector(".inbox-dialog-close");
    document.querySelectorAll("[data-inbox-open]").forEach((button) => {
      button.addEventListener("click", () => inboxDialog.showModal());
    });
    closeInbox.addEventListener("click", () => inboxDialog.close());
    inboxDialog.addEventListener("click", (event) => {
      if (event.target === inboxDialog) inboxDialog.close();
    });
  }

  document.querySelectorAll(".city-picker").forEach((picker) => {
    const trigger = picker.querySelector(".picker-trigger");
    const valueInput = picker.querySelector('input[type="hidden"]');
    const label = trigger.querySelector("span");
    picker.querySelectorAll("[data-value]").forEach((option) => {
      if (option.dataset.value === valueInput.value) option.classList.add("is-selected");
      option.addEventListener("click", () => {
        valueInput.value = option.dataset.value;
        label.textContent = option.dataset.value;
        picker.dataset.open = "false";
        trigger.setAttribute("aria-expanded", "false");
        picker.querySelectorAll("[data-value]").forEach((item) => item.classList.toggle("is-selected", item === option));
      });
    });
    trigger.addEventListener("click", () => {
      const isOpen = picker.dataset.open === "true";
      picker.dataset.open = String(!isOpen);
      trigger.setAttribute("aria-expanded", String(!isOpen));
    });
    picker.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        picker.dataset.open = "false";
        trigger.setAttribute("aria-expanded", "false");
        trigger.focus();
      }
    });
  });

  document.addEventListener("click", (event) => {
    document.querySelectorAll(".city-picker[data-open='true']").forEach((picker) => {
      if (!picker.contains(event.target)) {
        picker.dataset.open = "false";
        picker.querySelector(".picker-trigger").setAttribute("aria-expanded", "false");
      }
    });
  });

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest(".profile-comment-vote-form");
    if (!form) return;

    event.preventDefault();
    const button = form.querySelector("button");
    const comment = form.closest(".profile-comment");
    const status = comment.querySelector(".profile-comment-status");
    button.disabled = true;
    status.textContent = "";

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
        credentials: "same-origin",
      });
      if (!response.ok) throw new Error("Vote request failed");

      const result = await response.json();
      status.hidden = true;
      comment.querySelector(".profile-comment-actions").querySelectorAll(".profile-comment-vote-form").forEach((voteForm) => {
        const voteButton = voteForm.querySelector("button");
        const value = voteForm.querySelector('input[name="value"]').value;
        const count = value === "like" ? result.like_count : result.dislike_count;
        voteButton.classList.toggle("is-selected", result.selected === value);
        voteButton.setAttribute("aria-pressed", String(result.selected === value));
        voteButton.querySelector("span:last-child").textContent = count;
      });
    } catch {
      status.hidden = false;
      status.textContent = "Не удалось сохранить реакцию. Попробуйте ещё раз.";
    } finally {
      button.disabled = false;
    }
  });

  let favorites = [];
  try {
    favorites = JSON.parse(window.localStorage.getItem("finduni-favorites") || "[]");
  } catch {
    favorites = [];
  }
  document.querySelectorAll("[data-favorite]").forEach((button) => {
    const name = button.dataset.favorite;
    const setFavorite = (active) => {
      button.setAttribute("aria-pressed", String(active));
      button.setAttribute("aria-label", active ? "Удалить из избранного" : "Добавить в избранное");
    };
    setFavorite(favorites.includes(name));
    button.addEventListener("click", () => {
      favorites = favorites.includes(name) ? favorites.filter((item) => item !== name) : [...favorites, name];
      setFavorite(favorites.includes(name));
      try {
        window.localStorage.setItem("finduni-favorites", JSON.stringify(favorites));
      } catch {
        return;
      }
    });
  });
});