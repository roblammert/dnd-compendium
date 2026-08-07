(() => {
  let syncTimer = null;
  let syncRequestInFlight = false;

  async function refreshSyncStatus() {
    const panel = document.getElementById("sync-status");
    if (!panel || panel.dataset.syncActive !== "true" || syncRequestInFlight) {
      if (!panel || panel?.dataset.syncActive !== "true") stopSyncPolling();
      return;
    }
    syncRequestInFlight = true;
    try {
      const response = await fetch("/admin/sync/status", {
        headers: { "HX-Request": "true", "Accept": "text/html" },
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`Sync status request failed: ${response.status}`);
      const wrapper = document.createElement("div");
      wrapper.innerHTML = await response.text();
      const replacement = wrapper.querySelector("#sync-status");
      const current = document.getElementById("sync-status");
      if (replacement && current) current.replaceWith(replacement);
      if (!replacement || replacement.dataset.syncActive !== "true") stopSyncPolling();
    } catch (error) {
      console.error(error);
    } finally {
      syncRequestInFlight = false;
    }
  }

  function startSyncPolling() {
    const panel = document.getElementById("sync-status");
    if (!panel || panel.dataset.syncActive !== "true" || syncTimer) return;
    syncTimer = window.setInterval(refreshSyncStatus, 2000);
  }

  function stopSyncPolling() {
    if (syncTimer) window.clearInterval(syncTimer);
    syncTimer = null;
  }

  document.addEventListener("DOMContentLoaded", () => {
    startSyncPolling();
    window.setTimeout(refreshSyncStatus, 500);
    const openList = document.querySelector("[data-open-list-dialog]");
    const listDialog = document.getElementById("add-to-list-dialog");
    const closeList = document.querySelector("[data-close-list-dialog]");
    if (openList && listDialog) openList.addEventListener("click", () => listDialog.showModal());
    if (closeList && listDialog) closeList.addEventListener("click", () => listDialog.close());
    if (listDialog && new URLSearchParams(location.search).get("add_to_list") === "1") listDialog.showModal();

    const hideBlocked = document.querySelector("[data-hide-blocked]");
    const featGrid = document.querySelector("[data-feat-grid]");
    if (hideBlocked && featGrid) {
      const applyBlockedVisibility = () => {
        featGrid.classList.toggle("hide-blocked", hideBlocked.checked);
      };
      hideBlocked.addEventListener("change", applyBlockedVisibility);
      applyBlockedVisibility();
    }

    const weaponSystemFilter = document.querySelector("[data-weapon-system-filter]");
    const weaponSearch = document.querySelector("[data-weapon-search]");
    const weaponChoices = Array.from(document.querySelectorAll("[data-weapon-choice]"));
    const weaponEmpty = document.querySelector("[data-weapon-empty]");
    if (weaponChoices.length && (weaponSystemFilter || weaponSearch)) {
      const filterWeapons = () => {
        const system = weaponSystemFilter ? weaponSystemFilter.value : "";
        const query = weaponSearch ? weaponSearch.value.trim().toLowerCase() : "";
        let visible = 0;
        weaponChoices.forEach((choice) => {
          const matchesSystem = !system || choice.dataset.gameSystem === system;
          const matchesSearch = !query || (choice.dataset.weaponName || "").includes(query);
          const show = matchesSystem && matchesSearch;
          choice.hidden = !show;
          if (show) visible += 1;
        });
        if (weaponEmpty) weaponEmpty.hidden = visible !== 0;
      };
      if (weaponSystemFilter) weaponSystemFilter.addEventListener("change", filterWeapons);
      if (weaponSearch) weaponSearch.addEventListener("input", filterWeapons);
      filterWeapons();
    }


    const listDestination = document.querySelector("[data-list-destination]");
    const newListFields = document.querySelector("[data-new-list-fields]");
    const newListName = document.querySelector("[data-new-list-name]");
    const updateNewListVisibility = () => {
      if (!listDestination || !newListFields) return;
      const creating = listDestination.value === "";
      newListFields.hidden = !creating;
      if (newListName) newListName.required = creating;
    };
    if (listDestination) {
      listDestination.addEventListener("change", updateNewListVisibility);
      updateNewListVisibility();
    }

    const sortableBody = document.querySelector("[data-sortable-list]");
    const sortableForm = document.querySelector("[data-sortable-list-form]");
    const orderInput = document.querySelector("[data-item-order]");
    if (sortableBody && sortableForm && orderInput) {
      let dragged = null;
      const syncOrder = () => {
        orderInput.value = Array.from(sortableBody.querySelectorAll("tr[data-item-id]"))
          .map((row) => row.dataset.itemId).join(",");
      };
      sortableBody.addEventListener("dragstart", (event) => {
        const row = event.target.closest("tr[data-item-id]");
        if (!row) return;
        dragged = row; row.classList.add("is-dragging");
        event.dataTransfer.effectAllowed = "move";
        event.dataTransfer.setData("text/plain", row.dataset.itemId);
      });
      sortableBody.addEventListener("dragover", (event) => {
        if (!dragged) return; event.preventDefault();
        const target = event.target.closest("tr[data-item-id]");
        if (!target || target === dragged) return;
        const rect = target.getBoundingClientRect();
        sortableBody.insertBefore(dragged, event.clientY < rect.top + rect.height / 2 ? target : target.nextSibling);
      });
      sortableBody.addEventListener("dragend", () => {
        if (dragged) dragged.classList.remove("is-dragging");
        dragged = null; syncOrder();
      });
      sortableForm.addEventListener("submit", syncOrder);
    }

    const picker = document.getElementById("source-variant");
    if (picker) picker.addEventListener("change", () => picker.form.submit());

    const filters = document.querySelector('form[data-auto-submit="true"]');
    if (filters) {
      let timer = null;
      filters.addEventListener("change", () => filters.submit());
      const search = filters.querySelector('input[name="q"]');
      if (search) search.addEventListener("input", () => {
        window.clearTimeout(timer);
        timer = window.setTimeout(() => filters.submit(), 350);
      });
    }
  });
})();

// v0.22 inline endpoint management saves.
document.addEventListener("submit", async (event) => {
  const form = event.target.closest?.("[data-endpoint-row-form]");
  if (!form) return;
  event.preventDefault();
  const button = form.querySelector("button[type=submit]");
  if (button) button.disabled = true;
  try {
    const response = await fetch(form.action, {method: "POST", body: new FormData(form), headers: {"Accept": "text/html"}});
    if (!response.ok) throw new Error(`Save failed: ${response.status}`);
    const wrapper = document.createElement("tbody"); wrapper.innerHTML = await response.text();
    const replacement = wrapper.querySelector("tr"); const current = form.closest("tr");
    if (replacement && current) {
      current.replaceWith(replacement);
      const status = replacement.querySelector(".row-save-status");
      if (status) window.setTimeout(() => status.classList.add("is-fading"), 4700);
    }
  } catch (error) {
    const status=form.querySelector(".row-save-status"); if(status) status.textContent="Save failed";
  } finally { if (button) button.disabled = false; }
});
