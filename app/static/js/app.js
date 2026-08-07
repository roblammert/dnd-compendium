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

// v0.31 Character Builder interactions: filters and point-buy feedback remain client-side.
(() => {
  const pointBuyCost = {8:0,9:1,10:2,11:3,12:4,13:5,14:7,15:9};
  function refreshPointBuy(form) {
    if (!form) return;
    const method = form.querySelector('input[name="ability_method"]:checked')?.value;
    const badge = form.querySelector('[data-point-buy-status]');
    if (!badge) return;
    if (method !== 'point_buy') { badge.textContent = method === 'standard_array' ? 'STANDARD ARRAY' : 'CUSTOM'; return; }
    let total=0, valid=true;
    form.querySelectorAll('[data-ability-input]').forEach((input) => {
      const score=Number(input.value); if (!(score in pointBuyCost)) valid=false; else total += pointBuyCost[score];
    });
    badge.textContent = valid ? `${total}/27 POINTS` : '8–15 REQUIRED';
    badge.classList.toggle('over-budget', !valid || total>27);
  }
  document.addEventListener('input', (event) => {
    const equipmentSearch = event.target.closest?.('[data-character-equipment-search]');
    if (equipmentSearch) {
      const q=equipmentSearch.value.trim().toLowerCase();
      document.querySelectorAll('[data-character-equipment-list] [data-equipment-name]').forEach((row)=>row.hidden=!!q && !row.dataset.equipmentName.includes(q));
    }
    const spellSearch = event.target.closest?.('[data-character-spell-search]');
    if (spellSearch) {
      const q=spellSearch.value.trim().toLowerCase();
      document.querySelectorAll('[data-character-spell-list] [data-spell-name]').forEach((row)=>row.hidden=!!q && !row.dataset.spellName.includes(q));
    }
    const abilityForm = event.target.closest?.('[data-ability-builder]');
    if (abilityForm) refreshPointBuy(abilityForm);
  });
  document.addEventListener('change', (event) => {
    const form = event.target.closest?.('[data-ability-builder]');
    if (form) refreshPointBuy(form);
  });
  document.addEventListener('htmx:afterSwap', (event) => {
    if (event.target?.id !== 'character-builder-stage') return;
    const step = new URL(location.href).searchParams.get('step');
    document.querySelectorAll('[data-character-step]').forEach((link)=>link.classList.toggle('active',link.dataset.characterStep===step));
    refreshPointBuy(document.querySelector('[data-ability-builder]'));
  });
  document.addEventListener('DOMContentLoaded', ()=>refreshPointBuy(document.querySelector('[data-ability-builder]')));
})();

// v0.31.3 Character Builder responsive choices, previews, auto-generation, and live abilities.
(() => {
  const abilities = ['str','dex','con','int','wis','cha'];
  const mod = (score) => Math.floor((Number(score) - 10) / 2);
  const fmtMod = (value) => `${value >= 0 ? '+' : ''}${value}`;

  async function openReference(button) {
    const dialog = document.getElementById('character-reference-dialog');
    if (!dialog || !button) return;
    const title = dialog.querySelector('[data-reference-modal-title]');
    const summary = dialog.querySelector('[data-reference-modal-summary]');
    const link = dialog.querySelector('[data-reference-modal-link]');
    const host = dialog.querySelector('[data-reference-card-host]');
    const url = button.dataset.referenceUrl || '#';
    if (title) title.textContent = button.dataset.referenceTitle || 'More Info';
    if (summary) { summary.hidden = false; summary.textContent = button.dataset.referenceSummary || 'Loading the cached compendium card…'; }
    if (link) link.href = url;
    if (host) { host.hidden = true; host.innerHTML = ''; }
    dialog.showModal();
    if (!url || url === '#') return;
    try {
      const response = await fetch(url, {headers:{'Accept':'text/html'}, cache:'no-store'});
      if (!response.ok) throw new Error(`Reference request failed: ${response.status}`);
      const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
      const shell = doc.querySelector('.entity-page-shell');
      if (shell && host) {
        shell.querySelector('.entity-page-toolbar')?.remove();
        host.innerHTML = shell.innerHTML;
        host.hidden = false;
        if (summary) summary.hidden = true;
      }
    } catch (error) {
      console.warn(error);
      if (summary) summary.hidden = false;
    }
  }

  function initClassBuilder(root=document) {
    const form = root.querySelector?.('[data-class-builder]');
    if (!form) return;
    const empty = form.querySelector('[data-subclass-empty]');
    const update = () => {
      const selected = form.querySelector('input[name="class_key"]:checked')?.value || '';
      let shown = 0;
      form.querySelectorAll('[data-subclass-parent]').forEach((card) => {
        const show = !!selected && card.dataset.subclassParent === selected;
        card.hidden = !show;
        if (show) shown += 1;
        if (!show) {
          const input = card.querySelector('input[name="subclass_key"]');
          if (input) input.checked = false;
        }
      });
      if (empty) {
        empty.hidden = shown > 0;
        empty.textContent = selected ? (shown ? '' : 'No cached subclass is available for this class.') : 'Select a primary class to see its available subclasses.';
      }
    };
    form.querySelectorAll('input[name="class_key"]').forEach((input)=>input.addEventListener('change', update));
    update();
  }

  function updateAbilityInputs(form) {
    if (!form) return;
    form.querySelectorAll('[data-ability-input]').forEach((input) => {
      const key = input.dataset.abilityInput;
      const score = Number(input.value || 10);
      const modifier = form.querySelector(`[data-ability-modifier="${key}"]`);
      const finalScore = form.querySelector(`[data-final-score="${key}"]`);
      if (modifier) modifier.textContent = fmtMod(mod(score));
      if (finalScore) finalScore.textContent = score;
    });
  }

  function roll4d6DropLowest() {
    const dice = Array.from({length:4},()=>Math.floor(Math.random()*6)+1).sort((a,b)=>a-b);
    return dice.slice(1).reduce((a,b)=>a+b,0);
  }

  function generateAbilities(form) {
    const method = form.querySelector('input[name="ability_method"]:checked')?.value || 'standard_array';
    let values;
    if (method === 'standard_array') values = [15,14,13,12,10,8];
    else if (method === 'point_buy') values = [15,15,15,8,8,8];
    else if (method === 'rolled') values = abilities.map(()=>roll4d6DropLowest());
    else return;
    form.querySelectorAll('[data-ability-input]').forEach((input,index)=>{ input.value=values[index]; input.dispatchEvent(new Event('input',{bubbles:true})); });
    updateAbilityInputs(form);
  }

  function railApplyScores(scores, flash=true) {
    const rail = document.querySelector('[data-ability-rail]');
    if (!rail) return;
    abilities.forEach((key) => {
      const card = rail.querySelector(`[data-rail-ability="${key}"]`);
      if (!card || scores[key] == null) return;
      const previous = Number(card.dataset.score || scores[key]);
      const next = Number(scores[key]);
      card.dataset.score = String(next);
      card.querySelector('[data-rail-score]').textContent = String(next);
      card.querySelector('[data-rail-mod]').textContent = fmtMod(mod(next));
      if (flash && next !== previous) {
        card.classList.remove('score-up','score-down');
        void card.offsetWidth;
        card.classList.add(next > previous ? 'score-up' : 'score-down');
        window.setTimeout(()=>card.classList.remove('score-up','score-down'),5000);
      }
    });
  }

  function initBackgroundBuilder(root=document) {
    const form = root.querySelector?.('[data-background-builder]');
    if (!form) return;
    const select = form.querySelector('[data-background-select]');
    const preview = form.querySelector('[data-background-preview]');
    const title = form.querySelector('[data-background-title]');
    const summary = form.querySelector('[data-background-summary]');
    const source = form.querySelector('[data-background-source]');
    const more = form.querySelector('[data-background-more]');
    const status = form.querySelector('[data-background-bonus-status]');
    const bonusSelects = Array.from(form.querySelectorAll('[data-background-bonus]'));

    const allowed = () => (select?.selectedOptions[0]?.dataset.abilities || abilities.join(',')).split(',').filter(Boolean);
    const updatePreview = () => {
      const option = select?.selectedOptions[0];
      const has = !!option?.value;
      if (preview) preview.hidden = !has;
      if (!has) return;
      if (title) title.textContent = option.textContent.split(' · ')[0];
      if (summary) summary.textContent = option.dataset.summary || 'No cached description is available.';
      if (source) source.textContent = option.dataset.source || '';
      if (more) {
        more.dataset.referenceTitle = title?.textContent || 'Background';
        more.dataset.referenceSummary = option.dataset.summary || '';
        more.dataset.referenceUrl = option.dataset.infoUrl || '#';
      }
      const permitted = allowed();
      form.querySelectorAll('[data-background-ability]').forEach((label) => {
        const enabled = permitted.includes(label.dataset.backgroundAbility);
        label.classList.toggle('is-disabled', !enabled);
        const control = label.querySelector('select');
        control.disabled = !enabled;
        if (!enabled) control.value = '0';
      });
      updateBonuses();
    };
    const updateBonuses = () => {
      const scores = {};
      let total=0; const values=[];
      // On first run, derive the pre-background score from the server-rendered
      // final score minus the currently saved background bonus. Subsequent
      // changes always recompute from that stable baseline.
      bonusSelects.forEach((control) => {
        const key=control.closest('[data-background-ability]')?.dataset.backgroundAbility;
        if (!key) return;
        const card=document.querySelector(`[data-rail-ability="${key}"]`);
        const currentAmount=control.disabled ? 0 : Number(control.value || 0);
        if (card && !card.dataset.persistedBase) card.dataset.persistedBase=String(Number(card.dataset.score || 10)-currentAmount);
      });
      abilities.forEach((key)=>{
        const card=document.querySelector(`[data-rail-ability="${key}"]`);
        scores[key]=Number(card?.dataset.persistedBase || card?.dataset.score || 10);
      });
      bonusSelects.forEach((control) => {
        if (control.disabled) return;
        const amount=Number(control.value || 0); total += amount; if(amount) values.push(amount);
        const key=control.closest('[data-background-ability]')?.dataset.backgroundAbility;
        if (key) scores[key]=Number(document.querySelector(`[data-rail-ability="${key}"]`)?.dataset.persistedBase || scores[key] || 10)+amount;
      });
      const valid = total===3 && (values.sort().join(',')==='1,2' || values.sort().join(',')==='1,1,1');
      if (status) { status.textContent = valid ? 'Valid 2024 adjustment: 3 points assigned.' : `Assign exactly 3 points (+2/+1 or +1/+1/+1). Current total: ${total}.`; status.classList.toggle('is-valid',valid); status.classList.toggle('is-invalid',!valid); }
      railApplyScores(scores,true);
    };
    select?.addEventListener('change', updatePreview);
    bonusSelects.forEach((control)=>control.addEventListener('change',updateBonuses));
    updatePreview();
  }

  function initCharacterEnhancements(root=document) {
    initClassBuilder(root); initBackgroundBuilder(root);
    const abilityForm = root.querySelector?.('[data-ability-builder]');
    if (abilityForm) updateAbilityInputs(abilityForm);
  }

  document.addEventListener('click', (event) => {
    const info = event.target.closest?.('[data-reference-title], [data-background-more]');
    if (info) { event.preventDefault(); openReference(info); }
    if (event.target.closest?.('[data-reference-close]')) document.getElementById('character-reference-dialog')?.close();
    const generate = event.target.closest?.('[data-generate-abilities]');
    if (generate) generateAbilities(generate.closest('[data-ability-builder]'));
  });
  document.addEventListener('input', (event)=>{
    const form=event.target.closest?.('[data-ability-builder]'); if(form) updateAbilityInputs(form);
  });
  document.addEventListener('DOMContentLoaded',()=>initCharacterEnhancements(document));
  document.addEventListener('htmx:afterSwap',(event)=>{
    if(event.target?.id==='character-builder-stage') {
      initCharacterEnhancements(event.target);
      const step=new URL(location.href).searchParams.get('step');
      const shell=document.querySelector('.character-builder-shell');
      shell?.classList.toggle('with-ability-rail',['background','gear','spells','details','review'].includes(step));
    }
  });
})();
