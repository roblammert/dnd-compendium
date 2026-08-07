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

// v0.31.4 Character Builder responsive choices, previews, auto-generation, and live abilities.
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
        // Character Builder reference modals are deliberately read-only.  The
        // full Compendium page keeps JSON, list actions, and artwork controls;
        // the embedded modal contains only the informational card itself.
        shell.querySelectorAll([
          '.entity-page-toolbar',
          '.raw-json-panel',
          '.entity-user-actions',
          '.asset-tools',
          '.shared-assets-panel',
          '.card-list-action',
          '#add-to-list-dialog',
          '.list-dialog',
          '[data-open-list-dialog]'
        ].join(',')).forEach((node) => node.remove());
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

  function updateLiveStatsFromScores(scores) {
    const rail = document.querySelector('[data-ability-rail]');
    if (!rail) return;
    const hpNode = rail.querySelector('[data-live-stat="hp"]');
    const acNode = rail.querySelector('[data-live-stat="ac"]');
    const baseHp = Number(rail.dataset.baseHp || hpNode?.textContent || 1);
    const baseAc = Number(rail.dataset.baseAc || acNode?.textContent || 10);
    const baseCon = Number(rail.dataset.baseConMod || 0);
    const baseDex = Number(rail.dataset.baseDexMod || 0);
    const level = Math.max(1, Number(rail.dataset.level || 1));
    if (hpNode && scores.con != null) hpNode.textContent = String(Math.max(1, baseHp + (mod(scores.con) - baseCon) * level));
    if (acNode && scores.dex != null) acNode.textContent = String(Math.max(1, baseAc + (mod(scores.dex) - baseDex)));
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
    updateLiveStatsFromScores(scores);
  }

  function applyLiveState(root=document) {
    const state = root.querySelector?.('[data-character-live-state]');
    const rail = document.querySelector('[data-ability-rail]');
    if (!state || !rail) return;
    let scores = {};
    try { scores = JSON.parse(state.dataset.scores || '{}'); } catch (_) {}
    rail.dataset.baseHp = state.dataset.hp || rail.dataset.baseHp;
    rail.dataset.baseAc = state.dataset.ac || rail.dataset.baseAc;
    rail.dataset.level = state.dataset.level || rail.dataset.level;
    rail.dataset.baseConMod = String(mod(scores.con ?? 10));
    rail.dataset.baseDexMod = String(mod(scores.dex ?? 10));
    const hp=rail.querySelector('[data-live-stat="hp"]'); if(hp) hp.textContent=state.dataset.hp || hp.textContent;
    const ac=rail.querySelector('[data-live-stat="ac"]'); if(ac) ac.textContent=state.dataset.ac || ac.textContent;
    const pb=rail.querySelector('[data-live-stat="pb"]'); if(pb) pb.textContent=`+${state.dataset.pb || 2}`;
    railApplyScores(scores,false);
  }

  function initIdentityBuilder(root=document) {
    const form = root.querySelector?.('[data-identity-builder]');
    if (!form || form.dataset.identityReady === '1') return;
    form.dataset.identityReady='1';
    const levelInput=form.querySelector('input[name="level"]');
    const xpInput=form.querySelector('input[name="experience_points"]');
    const note=form.querySelector('[data-identity-sync-note]');
    let table={};
    try { table=JSON.parse(form.dataset.levelXp || '{}'); } catch (_) {}
    const minXp=(level)=>Number(table[String(level)] ?? table[level] ?? 0);
    const levelForXp=(xp)=>{ let result=1; Object.entries(table).forEach(([level,minimum])=>{ if(Number(xp)>=Number(minimum)) result=Math.max(result,Number(level)); }); return Math.min(20,result); };
    const syncFromLevel=()=>{ if(!levelInput||!xpInput)return; const level=Math.max(1,Math.min(20,Number(levelInput.value||1))); levelInput.value=String(level); const minimum=minXp(level); if(Number(xpInput.value||0)<minimum) xpInput.value=String(minimum); if(note) note.textContent=`Level ${level} requires at least ${minimum.toLocaleString()} XP.`; };
    const syncFromXp=()=>{ if(!levelInput||!xpInput)return; const xp=Math.max(0,Number(xpInput.value||0)); xpInput.value=String(xp); const level=levelForXp(xp); levelInput.value=String(level); if(note) note.textContent=`${xp.toLocaleString()} XP corresponds to Level ${level}.`; };
    ['input','change'].forEach(evt=>levelInput?.addEventListener(evt,syncFromLevel));
    ['input','change'].forEach(evt=>xpInput?.addEventListener(evt,syncFromXp));
  }

  function initBackgroundBuilder(root=document) {
    const form = root.querySelector?.('[data-background-builder]');
    if (!form || form.dataset.backgroundReady==='1') return;
    form.dataset.backgroundReady='1';
    const select = form.querySelector('[data-background-select]');
    const preview = form.querySelector('[data-background-preview]');
    const title = form.querySelector('[data-background-title]');
    const summary = form.querySelector('[data-background-summary]');
    const source = form.querySelector('[data-background-source]');
    const more = form.querySelector('[data-background-more]');
    const asiPanel=form.querySelector('[data-background-ability-panel]');
    const status = form.querySelector('[data-background-bonus-status]');
    const bonusSelects = Array.from(form.querySelectorAll('[data-background-bonus]'));
    const languageRows=Array.from(form.querySelectorAll('[data-language-choice]'));
    const languageCounter=form.querySelector('[data-language-counter]');

    const allowed = () => (select?.selectedOptions[0]?.dataset.abilities || '').split(',').filter(Boolean);
    const is2024=()=>select?.selectedOptions[0]?.dataset.is2024==='1';
    const updateLanguages=()=>{
      const chosen=languageRows.filter(r=>r.dataset.languageChoice!=='Common' && r.querySelector('input')?.checked);
      languageRows.forEach(r=>{ const input=r.querySelector('input'); if(!input||r.dataset.languageChoice==='Common')return; input.disabled=!input.checked && chosen.length>=2; });
      if(languageCounter) languageCounter.textContent=`${chosen.length}/2 additional languages selected.`;
    };
    const updateBonuses = () => {
      const scores = {}; let total=0; const values=[];
      bonusSelects.forEach((control) => {
        const key=control.closest('[data-background-ability]')?.dataset.backgroundAbility;
        if (!key) return;
        const card=document.querySelector(`[data-rail-ability="${key}"]`);
        const currentAmount=control.disabled ? 0 : Number(control.value || 0);
        if (card && !card.dataset.persistedBase) card.dataset.persistedBase=String(Number(card.dataset.score || 10)-currentAmount);
      });
      abilities.forEach((key)=>{ const card=document.querySelector(`[data-rail-ability="${key}"]`); scores[key]=Number(card?.dataset.persistedBase || card?.dataset.score || 10); });
      if(is2024()) bonusSelects.forEach((control) => { if (control.disabled) return; const amount=Number(control.value || 0); total += amount; if(amount) values.push(amount); const key=control.closest('[data-background-ability]')?.dataset.backgroundAbility; if (key) scores[key]=Number(document.querySelector(`[data-rail-ability="${key}"]`)?.dataset.persistedBase || scores[key] || 10)+amount; });
      const valid = total===3 && (values.slice().sort().join(',')==='1,2' || values.slice().sort().join(',')==='1,1,1');
      if (status) { status.textContent = valid ? 'Valid 2024 adjustment: 3 points assigned.' : `Assign exactly 3 points (+2/+1 or +1/+1/+1). Current total: ${total}.`; status.classList.toggle('is-valid',valid); status.classList.toggle('is-invalid',!valid); }
      railApplyScores(scores,true);
    };
    const updatePreview = () => {
      const option = select?.selectedOptions[0]; const has = !!option?.value;
      if (preview) preview.hidden = !has;
      if (asiPanel) asiPanel.hidden=!has || !is2024();
      if (!has) { bonusSelects.forEach(c=>{c.value='0';c.disabled=true;}); updateBonuses(); return; }
      if (title) title.textContent = option.textContent.split(' · ')[0];
      if (summary) { const text=option.dataset.summary || 'No cached description is available.'; summary.textContent = text.length > 220 ? `${text.slice(0,217).trimEnd()}…` : text; }
      if (source) source.textContent = option.dataset.source || '';
      if (more) { more.dataset.referenceTitle = title?.textContent || 'Background'; more.dataset.referenceSummary = option.dataset.summary || ''; more.dataset.referenceUrl = option.dataset.infoUrl || '#'; }
      const permitted = allowed(); const grantedSkills=(option.dataset.skills || '').split('|').filter(Boolean); const grantedProfs=(option.dataset.proficiencies || '').split('|').filter(Boolean);
      form.querySelectorAll('[data-skill-choice]').forEach((row)=>{ const input=row.querySelector('input'); const locked=grantedSkills.includes(row.dataset.skillChoice); row.classList.toggle('background-granted',locked); if(input){ input.disabled=locked; if(locked) input.checked=true; } const lock=row.querySelector('.grant-lock'); if(lock) lock.hidden=!locked; });
      form.querySelectorAll('[data-proficiency-choice]').forEach((row)=>{ const input=row.querySelector('input'); const locked=grantedProfs.includes(row.dataset.proficiencyChoice); row.classList.toggle('background-granted',locked); if(input){ input.disabled=locked; if(locked) input.checked=true; } const lock=row.querySelector('.grant-lock'); if(lock) lock.hidden=!locked; });
      form.querySelectorAll('[data-background-ability]').forEach((label) => { const enabled=is2024() && permitted.includes(label.dataset.backgroundAbility); label.classList.toggle('is-disabled', !enabled); const control=label.querySelector('select'); control.disabled=!enabled; if(!enabled) control.value='0'; });
      updateBonuses(); updateLanguages();
    };
    select?.addEventListener('change', updatePreview);
    bonusSelects.forEach((control)=>control.addEventListener('change',updateBonuses));
    languageRows.forEach(row=>row.querySelector('input')?.addEventListener('change',updateLanguages));
    updatePreview(); updateLanguages();
  }

  function debounce(fn, wait=450) { let timer; return (...args)=>{ clearTimeout(timer); timer=setTimeout(()=>fn(...args),wait); }; }

  function initGearBuilder(root=document) {
    const form=root.querySelector?.('[data-gear-builder]');
    if(!form || form.dataset.gearReady==='1') return;
    form.dataset.gearReady='1';
    const rows=Array.from(form.querySelectorAll('[data-equipment-row]'));
    const totalNode=form.querySelector('[data-equipment-cost]');
    const armorStatus=form.querySelector('[data-armor-limit-status]');
    const message=form.querySelector('[data-gear-rule-message]');
    const search=form.querySelector('[data-character-equipment-search]');
    const filter=form.querySelector('[data-character-equipment-filter]');
    const count=form.querySelector('[data-equipment-visible-count]');
    let serverIds=new Set(rows.map(r=>r.dataset.equipmentId));
    const applyVisibility=()=>{
      const mode=filter?.value||'all'; let visible=0;
      rows.forEach(r=>{
        const checked=!!r.querySelector('input')?.checked;
        const type=r.dataset.equipmentType||'';
        const matchesServer=serverIds.has(r.dataset.equipmentId);
        const matchesMode=mode==='all' ? true : mode==='selected' ? checked : type===mode;
        r.hidden=!(matchesServer && matchesMode); if(!r.hidden) visible++;
      });
      if(count) count.textContent=`${visible} shown`;
    };
    const runSearch=debounce(async()=>{
      const url=search?.dataset.filterUrl; if(!url) return;
      const params=new URLSearchParams({q:(search.value||'').trim()});
      try { const res=await fetch(`${url}?${params}`,{headers:{Accept:'application/json'},cache:'no-store'}); if(res.ok){ const data=await res.json(); serverIds=new Set(data.ids||[]); applyVisibility(); } } catch(_) { applyVisibility(); }
    },450);
    const update=()=>{
      const selected=rows.filter(r=>r.querySelector('input')?.checked);
      const purchased=selected.filter(r=>r.dataset.equipmentLocked!=='1');
      const total=purchased.reduce((sum,r)=>sum+Number(r.dataset.equipmentCostGp||0),0);
      if(totalNode) totalNode.textContent=total ? `${Number.isInteger(total)?total:total.toFixed(2)} GP` : '0 GP';
      const suit=selected.find(r=>['light','medium','heavy','armor'].includes(r.dataset.armorKind));
      const shield=selected.find(r=>r.dataset.armorKind==='shield');
      rows.forEach(r=>{
        const input=r.querySelector('input'); if(!input || r.dataset.equipmentLocked==='1') return;
        const kind=r.dataset.armorKind;
        const untrained=r.dataset.armorTrained==='0';
        const conflict=(['light','medium','heavy','armor'].includes(kind)&&!!suit&&!input.checked)||(kind==='shield'&&!!shield&&!input.checked);
        input.disabled=untrained || conflict;
        r.classList.toggle('is-rule-disabled',untrained);
        r.classList.toggle('is-limit-disabled',!untrained && conflict);
      });
      if(armorStatus) armorStatus.textContent=suit ? (shield ? 'Suit + Shield selected' : 'Armor suit selected') : (shield ? 'Shield selected' : 'Ready');
      if(message) message.textContent=(suit||shield) ? 'Armor capacity is satisfied. The selected armor remains enabled so it can be removed; conflicting choices unlock immediately when it is unchecked.' : 'Armor limits and training are enforced live as you make selections.';
      applyVisibility();
    };
    rows.forEach(r=>r.querySelector('input')?.addEventListener('change',update));
    search?.addEventListener('input',runSearch); filter?.addEventListener('change',()=>{ applyVisibility(); runSearch(); });
    search?.addEventListener('keydown',(event)=>{ if(event.key==='Enter'){ event.preventDefault(); event.stopPropagation(); runSearch(); } });
    update(); runSearch();
  }

  function initSpellBuilder(root=document) {
    const form=root.querySelector?.('[data-spell-builder]');
    if(!form || form.dataset.spellReady==='1') return;
    form.dataset.spellReady='1';
    const rows=Array.from(form.querySelectorAll('[data-spell-row]'));
    const search=form.querySelector('[data-character-spell-search]');
    const levelFilter=form.querySelector('[data-character-spell-level]');
    const count=form.querySelector('[data-spell-visible-count]');
    const status=form.querySelector('[data-spell-limit-status]');
    const cantripLimit=Number(form.dataset.spellCantripLimit||0), knownLimit=Number(form.dataset.spellKnownLimit||0), preparedLimit=Number(form.dataset.spellPreparedLimit||0);
    let serverIds=new Set(rows.map(r=>r.dataset.spellId));
    const selectedRows=()=>rows.filter(r=>r.querySelector('input[name="spells"]')?.checked);
    const applyLimits=()=>{
      const selected=selectedRows();
      const cantrips=selected.filter(r=>Number(r.dataset.spellLevel||0)===0);
      const leveled=selected.filter(r=>Number(r.dataset.spellLevel||0)>0);
      const prepared=rows.filter(r=>r.querySelector('input[name="prepared"]')?.checked);
      rows.forEach(r=>{
        const choose=r.querySelector('input[name="spells"]'); const prep=r.querySelector('input[name="prepared"]'); if(!choose)return;
        const level=Number(r.dataset.spellLevel||0); const chosen=choose.checked;
        choose.disabled=!chosen && ((level===0 && cantripLimit && cantrips.length>=cantripLimit)||(level>0 && knownLimit && leveled.length>=knownLimit));
        if(prep){ if(!chosen) prep.checked=false; prep.disabled=!chosen || (!prep.checked && prepared.length>=preparedLimit); }
      });
      if(status) status.textContent=`Cantrips ${cantrips.length}/${cantripLimit || '—'} · Chosen level 1+ ${leveled.length}/${knownLimit || '—'} · Prepared ${prepared.length}/${preparedLimit || '—'}`;
    };
    const applyVisibility=()=>{ const mode=levelFilter?.value||'all'; let visible=0; rows.forEach(r=>{ const selected=!!r.querySelector('input[name="spells"]')?.checked; const level=String(r.dataset.spellLevel||'0'); const match=serverIds.has(r.dataset.spellId) && (mode==='all'||(mode==='selected'&&selected)||mode===level); r.hidden=!match; if(match)visible++; }); if(count)count.textContent=`${visible} shown`; };
    const runSearch=debounce(async()=>{ const url=search?.dataset.filterUrl; if(!url)return; const params=new URLSearchParams({q:(search.value||'').trim()}); try{const res=await fetch(`${url}?${params}`,{headers:{Accept:'application/json'},cache:'no-store'});if(res.ok){const data=await res.json();serverIds=new Set(data.ids||[]);applyVisibility();}}catch(_){applyVisibility();}},450);
    rows.forEach(r=>{r.querySelector('input[name="spells"]')?.addEventListener('change',()=>{applyLimits();applyVisibility();});r.querySelector('input[name="prepared"]')?.addEventListener('change',applyLimits);});
    search?.addEventListener('input',runSearch); levelFilter?.addEventListener('change',applyVisibility);
    search?.addEventListener('keydown',(event)=>{ if(event.key==='Enter'){ event.preventDefault(); event.stopPropagation(); runSearch(); } });
    applyLimits(); applyVisibility(); runSearch();
  }

  function initCharacterEnhancements(root=document) {
    initIdentityBuilder(root); initClassBuilder(root); initBackgroundBuilder(root); initGearBuilder(root); initSpellBuilder(root);
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
      applyLiveState(event.target);
      const step=new URL(location.href).searchParams.get('step');
      const shell=document.querySelector('.character-builder-shell');
      shell?.classList.toggle('with-ability-rail',['background','gear','spells','details','review'].includes(step));
    }
  });
})();


// v0.31.8 Character Builder guarded navigation and filter-submit protection.
(() => {
  let pendingTarget = null;
  let baseline = '';

  const currentForm = () => document.querySelector('#character-builder-stage .character-step-form');
  const serializableFields = (form) => Array.from(form?.elements || []).filter((el) => {
    if (!el.name || el.disabled || el.matches('[data-nonpersistent-control]')) return false;
    if (el.type === 'submit' || el.type === 'button') return false;
    return true;
  });
  const snapshot = (form) => {
    if (!form) return '';
    return serializableFields(form).map((el) => {
      if (el.type === 'checkbox' || el.type === 'radio') return `${el.name}:${el.value}:${el.checked ? 1 : 0}`;
      return `${el.name}:${el.value}`;
    }).sort().join('|');
  };
  const captureBaseline = () => { baseline = snapshot(currentForm()); };
  const syncMoverState = (root=document) => {
    const state = root.querySelector?.('[data-character-live-state]');
    if (!state) return;
    const characterId = document.querySelector('.character-builder-shell')?.dataset.characterId;
    [['previous', state.dataset.prevStep, state.dataset.canPrev], ['next', state.dataset.nextStep, state.dataset.canNext]].forEach(([kind,target,can]) => {
      const button=document.querySelector(`[data-character-move=\"${kind}\"]`);
      if(!button)return; const enabled=can==='1' && !!target;
      button.classList.toggle('disabled',!enabled);
      button.setAttribute('aria-disabled', enabled ? 'false' : 'true');
      if(enabled){ button.dataset.characterNavTarget=target; button.href=`/tools/character-builder/${characterId}?step=${encodeURIComponent(target)}`; }
      else { delete button.dataset.characterNavTarget; button.removeAttribute('href'); }
    });
  };
  const isDirty = () => {
    const form = currentForm();
    return !!form && snapshot(form) !== baseline;
  };
  const destinationUrl = (target) => {
    const shell = document.querySelector('.character-builder-shell');
    const publicId = shell?.dataset.characterId || location.pathname.split('/').filter(Boolean).pop();
    return `/tools/character-builder/${publicId}?step=${encodeURIComponent(target)}`;
  };
  const dialog = () => document.getElementById('character-unsaved-dialog');
  const moveWithoutSaving = (target) => { window.location.assign(destinationUrl(target)); };
  const saveAndMove = (target) => {
    const form = currentForm();
    if (!form) return moveWithoutSaving(target);
    let hidden = form.querySelector('input[data-dirty-nav-target]');
    if (!hidden) {
      hidden = document.createElement('input');
      hidden.type = 'hidden'; hidden.name = 'next_step'; hidden.dataset.dirtyNavTarget = '1';
      form.appendChild(hidden);
    }
    hidden.value = target;
    baseline = snapshot(form);
    form.requestSubmit();
  };
  const requestMove = (target) => {
    if (!target) return;
    if (!isDirty()) return moveWithoutSaving(target);
    pendingTarget = target;
    dialog()?.showModal();
  };

  document.addEventListener('click', (event) => {
    const nav = event.target.closest?.('[data-character-nav-target]');
    if (nav && !nav.classList.contains('disabled') && nav.getAttribute('aria-disabled') !== 'true') {
      event.preventDefault(); requestMove(nav.dataset.characterNavTarget); return;
    }
    if (event.target.closest?.('[data-dirty-cancel]')) { event.preventDefault(); pendingTarget = null; dialog()?.close(); return; }
    if (event.target.closest?.('[data-dirty-discard]')) { event.preventDefault(); const target=pendingTarget; pendingTarget=null; dialog()?.close(); if(target) moveWithoutSaving(target); return; }
    if (event.target.closest?.('[data-dirty-save]')) { event.preventDefault(); const target=pendingTarget; pendingTarget=null; dialog()?.close(); if(target) saveAndMove(target); return; }
  });

  // Search boxes are workflow controls, never form submission controls.
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') return;
    if (event.target.closest?.('[data-character-equipment-search], [data-character-spell-search]')) {
      event.preventDefault(); event.stopPropagation();
    }
  }, true);

  document.addEventListener('DOMContentLoaded', captureBaseline);
  document.addEventListener('htmx:afterSwap', (event) => {
    if (event.target?.id === 'character-builder-stage') window.setTimeout(()=>{ syncMoverState(event.target); captureBaseline(); }, 0);
  });
})();
