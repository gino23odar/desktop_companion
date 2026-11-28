export const EYES = ['open','happy','sleepy','excited','glasses'];
export const MOUTHS = ['none','smile','neutral','open'];
export const ACCESSORIES = ['none','heart','star','zzz'];
export const DEFAULT_ANIMATION = Object.freeze({blink_ms:4500,ear_wiggle:true,accessory_motion:true});
export function newMood(id='') {
  return {id,background:'#FFD1DE',eyes:'open',mouth:'none',blush:false,accessory:'none',message:'Hello Svinka!',animation:{...DEFAULT_ANIMATION}};
}
const plain = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const exact = (v, keys) => plain(v) && Object.keys(v).length === keys.length && keys.every(k=>Object.hasOwn(v,k));
export function normalizeMood(v) {
  const required=['id','background','eyes','mouth','blush','accessory','message'];
  if (!exact(v,required) && !exact(v,[...required,'animation'])) throw new Error('Unexpected or missing mood fields.');
  if (typeof v.id!=='string'||! /^[a-z0-9_-]{1,24}(?![\s\S])/.test(v.id)) throw new Error('ID: use 1–24 lowercase letters, digits, _ or -.');
  if (typeof v.background!=='string'||! /^#[0-9a-f]{6}(?![\s\S])/i.test(v.background)) throw new Error('Background: expected #RRGGBB.');
  if (!EYES.includes(v.eyes)||!MOUTHS.includes(v.mouth)||!ACCESSORIES.includes(v.accessory)||typeof v.blush!=='boolean') throw new Error('Invalid appearance setting.');
  if(typeof v.message!=='string'||v.message.length>24||/[^\x20-\x7e]/.test(v.message)) throw new Error('Message: maximum 24 printable ASCII characters.');
  const a=Object.hasOwn(v,'animation')?v.animation:DEFAULT_ANIMATION;
  if(!exact(a,['blink_ms','ear_wiggle','accessory_motion'])||!Number.isInteger(a.blink_ms)||(a.blink_ms!==0&&(a.blink_ms<1000||a.blink_ms>15000))||typeof a.ear_wiggle!=='boolean'||typeof a.accessory_motion!=='boolean') throw new Error('Animation: blink must be 0 or an integer from 1000 to 15000; flags must be booleans.');
  return {id:v.id,background:v.background.toUpperCase(),eyes:v.eyes,mouth:v.mouth,blush:v.blush,accessory:v.accessory,message:v.message,animation:{blink_ms:a.blink_ms,ear_wiggle:a.ear_wiggle,accessory_motion:a.accessory_motion}};
}
export function normalizePublication(v) {
  if(!exact(v,['revision','mood','published_at'])||!Number.isSafeInteger(v.revision)||v.revision<1||typeof v.published_at!=='string'||!Number.isFinite(Date.parse(v.published_at))) throw new Error('Invalid published state.');
  return {revision:v.revision,mood:normalizeMood(v.mood),published_at:v.published_at};
}
export function sameMood(a,b) {try{return JSON.stringify(normalizeMood(a))===JSON.stringify(normalizeMood(b));}catch{return false;}}
export function copyId(id, existing) {
  for(let i=1;i<=10000;i++){const suffix=i===1?'_copy':`_copy${i}`;const candidate=(id||'mood').slice(0,24-suffix.length)+suffix;if(!existing.includes(candidate))return candidate;}
  throw new Error('No unused copy ID available.');
}
export function animationFrame(a,elapsed) {
  const t=Math.max(0,elapsed);const phase=t%5000;const step=Math.floor((t%1600)/200);
  const blink=Number.isInteger(a.blink_ms)&&a.blink_ms>=1000&&a.blink_ms<=15000;
  return {eyesClosed:blink&&t%a.blink_ms>=a.blink_ms-120,earOffset:a.ear_wiggle?(phase>=4200&&phase<4350?4:phase>=4350&&phase<4500?-4:phase>=4500&&phase<4650?3:0):0,accessoryOffset:a.accessory_motion?step===0?0:-2*(step<=4?step:8-step):0};
}
export function boopMood(m) {return {...m,eyes:'happy',mouth:'smile',blush:true,accessory:'heart',message:'BOOP!'};}
