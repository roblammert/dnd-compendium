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
