import {newMood,normalizeMood,sameMood,copyId} from './model.mjs';
import {StudioApi} from './api.mjs';
import {Preview} from './preview.mjs';
import {decodePack,fromBase64,paintFrame} from './artwork-model.mjs';
import {normalizePublication} from './model.mjs';
async function fetchActive(api){const v=await api.request('GET','/active',undefined,2);return {...normalizePublication({revision:v.revision,mood:v.mood,published_at:v.published_at}),artwork:v.artwork};}
const $=id=>document.getElementById(id);
const draftPreview=new Preview($('preview')),publishedPreview=new Preview($('published-preview'));
const fields=['mood-id','background','eyes','mouth','accessory','blush','message','blink','ears','motion','animate'];
let api=null,catalog=[],active=null,savedId=null,baseline=newMood(),busy=false;
const reduceMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
$('animate').checked=!reduceMotion;
function status(message,error=false){$('status').textContent=message;$('status').dataset.error=String(error);}
function readDraft(){return {id:$('mood-id').value,background:$('background').value.toUpperCase(),eyes:$('eyes').value,mouth:$('mouth').value,blush:$('blush').checked,accessory:$('accessory').value,message:$('message').value,animation:{blink_ms:$('blink').valueAsNumber,ear_wiggle:$('ears').checked,accessory_motion:$('motion').checked}};}
function dirty(){const d=readDraft();return (!savedId&&d.id!=='')||JSON.stringify(d)!==JSON.stringify(baseline);}
function writeDraft(m,existing=null){savedId=existing;baseline=structuredClone(m);$('mood-id').value=m.id;$('mood-id').readOnly=existing!==null;$('background').value=m.background;$('eyes').value=m.eyes;$('mouth').value=m.mouth;$('accessory').value=m.accessory;$('blush').checked=m.blush;$('message').value=m.message;$('blink').value=m.animation.blink_ms;$('ears').checked=m.animation.ear_wiggle;$('motion').checked=m.animation.accessory_motion;update(true);renderCatalog();}
function update(preview=false){
  const d=readDraft();let valid=true;let validation='';try{normalizeMood(d);if(!savedId&&catalog.some(m=>m.id===d.id))throw new Error('This ID already exists. Choose a new ID.');}catch(e){valid=false;validation=e.message;}
  $('validation').textContent=validation;$('message-count').textContent=`${d.message.length} / 24`;
  const changed=dirty();$('draft-state').textContent=savedId?(changed?'Unsaved changes':'Saved'):'New draft';
  $('save').disabled=busy||!api||!valid||(!!savedId&&!changed);
  $('publish').disabled=busy||!api||!savedId||changed||!valid;
  $('duplicate').disabled=busy||!api;$('delete').disabled=busy||!api||!savedId||savedId===active?.mood.id;
  if(preview)draftPreview.set(d,$('animate').checked);
}
function renderCatalog(){const parent=$('catalog');parent.replaceChildren();for(const mood of catalog){const b=document.createElement('button');b.type='button';b.textContent=mood.id+(active?.mood.id===mood.id?(active?.artwork?' · Fallback':' · Published'):'');b.setAttribute('aria-pressed',String(mood.id===savedId));b.disabled=busy;b.addEventListener('click',()=>{if(mood.id===savedId||!discard())return;writeDraft(mood,mood.id);status(`Editing ${mood.id}.`);});parent.append(b);}}
function renderActive(){if(!active)return;$('revision').textContent=`Rev ${active.revision}`;$('published-id').textContent=active.mood.id;$('published-message').textContent=active.mood.message;$('published-time').textContent=new Date(active.published_at).toLocaleString();if(active.artwork){publishedPreview.stop();const c=document.createElement('canvas');c.width=80;c.height=60;paintFrame(c,decodePack(fromBase64(active.artwork.pack)).frames[0]);const ctx=$('published-preview').getContext('2d');ctx.imageSmoothingEnabled=false;ctx.drawImage(c,0,0,320,240);$('published-id').textContent=active.artwork.id+' (artwork)';$('published-message').textContent='Primitive fallback: '+active.mood.id;}else{publishedPreview.set(active.mood,!reduceMotion);publishedPreview.run();}renderCatalog();update();}
function discard(){return !dirty()||window.confirm('Discard unsaved draft changes?');}
function setBusy(value){busy=value;for(const id of [...fields,'new','refresh','logout','boop'])$(id).disabled=value;for(const b of $('login').querySelectorAll('button,input'))b.disabled=value;renderCatalog();if(api)update();}
async function perform(fn){if(busy)return;setBusy(true);try{await fn();}catch(e){status(e.message||'Operation failed.',true);}finally{setBusy(false);}}
function clearSession(){api=null;catalog=[];active=null;savedId=null;baseline=newMood();$('token').value='';$('workspace').hidden=true;$('logout').hidden=true;$('login').hidden=false;$('connection').textContent='Disconnected';draftPreview.stop();publishedPreview.stop();draftPreview.set(null);publishedPreview.set(null);$('catalog').replaceChildren();$('published-id').textContent='—';$('published-message').textContent='';$('published-time').textContent='';$('revision').textContent='—';}
$('login').addEventListener('submit',e=>{e.preventDefault();const token=$('token').value.trim();$('token').value='';perform(async()=>{const candidate=new StudioApi(token);const [list,pub]=await Promise.all([candidate.catalog(),fetchActive(candidate)]);api=candidate;catalog=list;active=pub;$('workspace').hidden=false;$('login').hidden=true;$('logout').hidden=false;$('connection').textContent='Connected';const first=list.find(m=>m.id===pub.mood.id)||list[0];writeDraft(first||newMood(),first?.id??null);renderActive();draftPreview.run();status('Connected. Choose a mood or create a new one.');});});
$('logout').addEventListener('click',()=>{if(!discard())return;clearSession();status('Disconnected. Token cleared from the application.');});
$('refresh').addEventListener('click',()=>{if(!discard())return;perform(async()=>{const [list,pub]=await Promise.all([api.catalog(),fetchActive(api)]);catalog=list;active=pub;const chosen=list.find(m=>m.id===savedId)||list.find(m=>m.id===pub.mood.id)||list[0];writeDraft(chosen||newMood(),chosen?.id??null);renderActive();status('Catalog and published state refreshed.');});});
$('new').addEventListener('click',()=>{if(!discard())return;writeDraft(newMood());status('New draft. Choose a unique ID and save it.');$('mood-id').focus();});
$('duplicate').addEventListener('click',()=>{const draft=readDraft();draft.id=copyId(draft.id,catalog.map(m=>m.id));writeDraft(draft);status('Duplicate created as a new draft. Save to add it to the catalog.');$('mood-id').focus();});
$('editor-form').addEventListener('input',()=>update(true));
$('editor-form').addEventListener('submit',e=>{e.preventDefault();if($('save').disabled)return;perform(async()=>{const m=await api.save(readDraft(),savedId!==null);catalog=[...catalog.filter(v=>v.id!==m.id),m].sort((a,b)=>a.id.localeCompare(b.id));writeDraft(m,m.id);status(`Saved ${m.id}. The published mood is unchanged.`);});});
$('publish').addEventListener('click',()=>{if($('publish').disabled||!window.confirm(`Publish ${savedId} to Svinka?`))return;perform(async()=>{const latest=await api.get(savedId);if(!sameMood(latest,baseline))throw new Error('Saved mood changed in another client. Refresh and review it before publishing.');active=await api.publish(savedId);renderActive();status(`Published revision ${active.revision}. Waiting for companion sync.`);});});
$('delete').addEventListener('click',()=>{if($('delete').disabled||!window.confirm(`Delete ${savedId}${dirty()?' and discard unsaved changes':''}?`))return;perform(async()=>{const id=savedId;await api.remove(id);catalog=catalog.filter(m=>m.id!==id);const next=catalog.find(m=>m.id===active?.mood.id)||catalog[0];writeDraft(next||newMood(),next?.id??null);status(`Deleted ${id}.`);});});
$('boop').addEventListener('click',()=>draftPreview.boop());
window.addEventListener('beforeunload',event=>{if(api&&dirty()){event.preventDefault();event.returnValue='';}});
