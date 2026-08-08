(() => {
  const $ = (q, root=document) => root.querySelector(q);
  const $$ = (q, root=document) => [...root.querySelectorAll(q)];
  const openDialog = id => { const d=document.getElementById(id); if(d && !d.open) d.showModal(); return d; };
  const closeDialog = el => { const d=el.closest('dialog'); if(d) d.close(); };

  document.addEventListener('click', async (event) => {
    const opener=event.target.closest('[data-pa-open]'); if(opener){ openDialog(opener.dataset.paOpen); return; }
    if(event.target.closest('[data-pa-close]')){ closeDialog(event.target); return; }
    const del=event.target.closest('[data-pa-delete]');
    if(del){ $('#pa-delete-name').textContent=del.dataset.paName; $('#pa-delete-form').action=`/tools/player-architect/${del.dataset.paDelete}/delete`; openDialog('pa-delete-dialog'); return; }
    const toggle=event.target.closest('[data-pa-blueprint-toggle]');
    if(toggle){ const opening=!document.body.classList.contains('pa-blueprint-open'); document.body.classList.toggle('pa-blueprint-open',opening); document.querySelectorAll('[data-pa-blueprint-toggle]').forEach(b=>b.setAttribute('aria-expanded', opening?'true':'false')); return; }
    const info=event.target.closest('[data-pa-info-url]');
    if(info && !info.disabled){ await showInfo(info.dataset.paInfoUrl); return; }
    const selectInfo=event.target.closest('[data-pa-select-info]');
    if(selectInfo && !selectInfo.disabled){ const select=document.querySelector(`[name="${selectInfo.dataset.paSelectInfo}"]`); const option=select?.selectedOptions?.[0]; if(option?.dataset.info) await showInfo(option.dataset.info); return; }
    const edit=event.target.closest('[data-pa-edit-blueprint]');
    if(edit){
      const data=JSON.parse(edit.dataset.paEditBlueprint); const shell=$('[data-pa-shell]'); const form=$('[data-pa-blueprint-edit-form]');
      form.action=`/tools/player-architect/${shell.dataset.characterId}/blueprint/${data.id}/edit`;
      $('[data-pa-edit-how]').value=data.how; $('[data-pa-edit-mod]').value=data.modifier; $('[data-pa-edit-stat]').value=data.stat; $('[data-pa-edit-note]').value=data.note;
      const dlg=openDialog('pa-blueprint-edit');
      let old=dlg.querySelector('[data-pa-delete-current]'); if(old) old.remove();
      const btn=document.createElement('button'); btn.type='button'; btn.className='danger-outline'; btn.textContent='Delete Entry'; btn.dataset.paDeleteCurrent=data.id; dlg.querySelector('.pa-dialog-actions').prepend(btn); return;
    }
    const deleteEntry=event.target.closest('[data-pa-delete-current]');
    if(deleteEntry){
      const shell=$('[data-pa-shell]'); const form=$('[data-pa-blueprint-delete-form]'); form.action=`/tools/player-architect/${shell.dataset.characterId}/blueprint/${deleteEntry.dataset.paDeleteCurrent}/delete`;
      document.getElementById('pa-blueprint-edit')?.close(); openDialog('pa-blueprint-delete'); return;
    }
  });

  async function showInfo(url){
    const dlg=openDialog('pa-info-dialog'), body=$('[data-pa-info-body]',dlg); body.innerHTML='<p class="pa-loading">Loading compendium record…</p>';
    try { const r=await fetch(url,{headers:{'X-Requested-With':'PlayerArchitect'}}); body.innerHTML=r.ok?await r.text():'<p>Unable to load this record.</p>'; }
    catch { body.innerHTML='<p>Unable to load this record.</p>'; }
  }

  $$('[data-pa-form]').forEach(form => {
    let initial=new FormData(form); const snapshot=()=>[...new FormData(form).entries()].map(([k,v])=>`${k}:${v}`).sort().join('|'); let initialText=[...initial.entries()].map(([k,v])=>`${k}:${v}`).sort().join('|');
    form.addEventListener('input',()=>{ const state=$('[data-pa-save-state]'); if(state) state.textContent=snapshot()===initialText?'Saved':'Unsaved'; });
    form.addEventListener('change',()=>{ const state=$('[data-pa-save-state]'); if(state) state.textContent=snapshot()===initialText?'Saved':'Unsaved'; });
  });

  const xpTable={1:0,2:300,3:900,4:2700,5:6500,6:14000,7:23000,8:34000,9:48000,10:64000,11:85000,12:100000,13:120000,14:140000,15:165000,16:195000,17:225000,18:265000,19:305000,20:355000};
  const levelInput=$('[data-pa-level-input]'), xpInput=$('[data-pa-xp-input]');
  if(levelInput && xpInput){
    levelInput.addEventListener('input',()=>{ const l=Math.max(1,Math.min(20,Number(levelInput.value)||1)); if(Number(xpInput.value)<xpTable[l]) xpInput.value=xpTable[l]; const target=$('[data-pa-status-level]'); if(target) target.textContent=l; const pb=2+Math.floor((l-1)/4); const pbt=$('[data-pa-status-pb]'); if(pbt) pbt.textContent=`+${pb}`; });
    xpInput.addEventListener('input',()=>{ const xp=Math.max(0,Number(xpInput.value)||0); let l=1; for(let i=1;i<=20;i++) if(xp>=xpTable[i]) l=i; levelInput.value=l; levelInput.dispatchEvent(new Event('input',{bubbles:true})); });
  }
  const nameInput=$('[data-pa-name-input]'); if(nameInput) nameInput.addEventListener('input',()=>{ const t=$('[data-pa-status-name]'); if(t) t.textContent=nameInput.value||'New Character'; });

  function scoreMod(score){ return Math.floor((Number(score)-10)/2); }
  const abilityInputs=$$('[data-pa-base-score]');
  if(abilityInputs.length){
    const initialScores={}; const initialMods={}; abilityInputs.forEach(i=>{ const a=i.dataset.paBaseScore; initialScores[a]=Number(i.value)||10; initialMods[a]=scoreMod(initialScores[a]+Number(i.dataset.paBlueprintMod||0)); });
    const initialHp=Number($('[data-pa-status-hp]')?.textContent||1), initialAc=Number($('[data-pa-status-ac]')?.textContent||10), level=Number($('[data-pa-status-level]')?.textContent||1);
    const update=()=>{
      abilityInputs.forEach(i=>{ const a=i.dataset.paBaseScore, live=(Number(i.value)||10)+Number(i.dataset.paBlueprintMod||0), mod=scoreMod(live); $('[data-pa-status-score="'+a+'"]').textContent=live; $('[data-pa-status-mod="'+a+'"]').textContent=(mod>=0?'+':'')+mod; });
      const dex=abilityInputs.find(i=>i.dataset.paBaseScore==='dex'), con=abilityInputs.find(i=>i.dataset.paBaseScore==='con');
      if(dex){ const mod=scoreMod((Number(dex.value)||10)+Number(dex.dataset.paBlueprintMod||0)); $('[data-pa-status-ac]').textContent=initialAc+(mod-initialMods.dex); }
      if(con){ const mod=scoreMod((Number(con.value)||10)+Number(con.dataset.paBlueprintMod||0)); $('[data-pa-status-hp]').textContent=Math.max(1,initialHp+(mod-initialMods.con)*level); }
    };
    abilityInputs.forEach(i=>i.addEventListener('input',update));
    $('[data-pa-auto-abilities]')?.addEventListener('click',()=>{
      const method=$('[name="ability_method"]:checked')?.value||'manual'; let values;
      if(method==='standard_array') values=[15,14,13,12,10,8];
      else if(method==='point_buy') values=[15,15,15,8,8,8];
      else if(method==='rolled') values=Array.from({length:6},()=>{ const d=Array.from({length:4},()=>1+Math.floor(Math.random()*6)).sort((a,b)=>a-b); return d.slice(1).reduce((a,b)=>a+b,0); });
      else return;
      abilityInputs.forEach((i,n)=>{ i.value=values[n]; i.dispatchEvent(new Event('input',{bubbles:true})); });
    });
  }

  $$('[data-pa-description-select]').forEach(select=>{
    const update=()=>{ const option=select.selectedOptions[0], target=document.getElementById(select.dataset.target); if(target) target.textContent=option?.dataset.description||'Choose an option to see its brief description.'; const btn=document.querySelector(`[data-pa-select-info="${select.name}"]`); if(btn) btn.disabled=!option?.dataset.info; };
    select.addEventListener('change',update); update();
  });


  function recalcBlueprintScores(){
    const sums={str:0,dex:0,con:0,int:0,wis:0,cha:0};
    $$('[data-pa-blueprint-row], [data-pa-preview-row]').forEach(row=>{ const stat=(row.dataset.stat||'').toLowerCase(); const m=(row.dataset.mod||'').match(/^\s*([+-]?\d+)\s*$/); if(stat in sums && m) sums[stat]+=Number(m[1]); });
    Object.keys(sums).forEach(a=>{ const el=$(`[data-pa-status-score="${a}"]`); if(!el) return; const live=Number(el.dataset.base||10)+sums[a]; el.textContent=live; const m=Math.floor((live-10)/2), mod=$(`[data-pa-status-mod="${a}"]`); if(mod) mod.textContent=(m>=0?'+':'')+m; });
    const dex=Number($('[data-pa-status-score="dex"]')?.textContent||10), ac=$('[data-pa-status-ac]'); if(ac) ac.textContent=10+Math.floor((dex-10)/2);
  }
  function previewAutomatic(origin, entries){
    $$(`[data-pa-preview-row][data-origin="${origin}"]`).forEach(r=>r.remove());
    const tbody=$('.pa-blueprint-table tbody'); if(!tbody) return;
    (entries||[]).forEach(item=>{ const tr=document.createElement('tr'); tr.className='locked pa-preview-row'; tr.dataset.paPreviewRow='1'; tr.dataset.origin=origin; tr.dataset.stat=item.stat; tr.dataset.mod=item.modifier; tr.innerHTML=`<td>🔒</td><td>${origin}</td><td>${item.modifier}</td><td>${item.stat}</td><td>${item.note||''} <em>(pending save)</em></td><td></td>`; tbody.appendChild(tr); });
    recalcBlueprintScores();
  }
  $$('[data-pa-auto-origin] input[type=radio]').forEach(input=>input.addEventListener('change',()=>{ const card=input.closest('[data-pa-auto-origin]'); if(input.checked) previewAutomatic(card.dataset.paAutoOrigin, JSON.parse(card.dataset.paAuto||'[]')); }));
  $('[name="background_entity_id"]')?.addEventListener('change',event=>{ const option=event.target.selectedOptions[0]; previewAutomatic('Background', option?.dataset.paAuto?JSON.parse(option.dataset.paAuto):[]); });

  const primaryClassInputs=$$('input[name="class_entity_id"]');
  function filterSubclasses(){
    const checked=primaryClassInputs.find(i=>i.checked), card=checked?.closest('[data-pa-class-card]'); const tokens=[card?.dataset.className,card?.dataset.classKey].filter(Boolean);
    let shown=0;
    $$('.pa-subclass-card').forEach(sub=>{ const text=(sub.dataset.parentText||'').toLowerCase(); const visible=tokens.some(t=>text.includes(t)); sub.hidden=!visible; if(visible) shown++; else { const r=sub.querySelector('input[type=radio]'); if(r) r.checked=false; } });
    const prompt=$('[data-pa-subclass-prompt]'); if(prompt) prompt.textContent=checked?(shown?`${shown} subclass option${shown===1?'':'s'} available for ${card.dataset.className}.`:'No cached subclasses identify this primary class.'):'Select a primary class to see its available subclasses.';
  }
  primaryClassInputs.forEach(i=>i.addEventListener('change',filterSubclasses)); filterSubclasses();

  // Choice cards gain selected state immediately for touch/tablet feedback.
  $$('.pa-choice-card input[type=radio], .pa-choice-row input[type=radio]').forEach(input=>input.addEventListener('change',()=>{ const name=input.name; $$(`input[name="${name}"]`).forEach(i=>{ const card=i.closest('.pa-choice-card, .pa-choice-row'); card?.classList.toggle('selected',i.checked); }); }));
})();
