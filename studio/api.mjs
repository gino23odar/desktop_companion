import {normalizeMood,normalizePublication} from './model.mjs';
export class ApiError extends Error {constructor(status,message){super(message);this.status=status;}}
export class StudioApi {
  #token;
  constructor(token,fetcher=globalThis.fetch.bind(globalThis)) {
    if(typeof token!=='string'||!/^[A-Za-z0-9_-]{32,256}(?![\s\S])/.test(token)) throw new Error('Enter a valid administrative token (32–256 URL-safe characters).');
    this.#token=token;this.fetcher=fetcher;
  }
  async request(method,path,body) {
    const options={method,headers:{Authorization:`Bearer ${this.#token}`,Accept:'application/json'},cache:'no-store',redirect:'error',credentials:'omit',signal:AbortSignal.timeout(8000)};
    if(body!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
    let r;try{r=await this.fetcher(`/api/v1${path}`,options);}catch{throw new ApiError(0,'Cannot reach the backend. Check the server and retry.');}
    if(!r.ok){const messages={401:'Invalid administrative token.',403:'Administrative token required (not device token).',404:'Mood no longer exists. Refresh the catalog.',409:'Conflict: duplicate ID or currently published mood.',422:'Backend rejected the mood definition.',503:'Database unavailable. Try again.'};throw new ApiError(r.status,messages[r.status]||`API request failed (${r.status}).`);}
    if(r.status===204)return null;
    if(!r.headers.get('content-type')?.includes('application/json'))throw new Error('Expected JSON from backend.');
    return r.json();
  }
  async catalog(){const result=await this.request('GET','/moods');if(!Array.isArray(result))throw new Error('Invalid catalog.');return result.map(normalizeMood);}
  async active(){return normalizePublication(await this.request('GET','/active'));}
  async get(id){return normalizeMood(await this.request('GET',`/moods/${encodeURIComponent(id)}`));}
  async save(mood,exists){const m=normalizeMood(mood);return normalizeMood(await this.request(exists?'PUT':'POST',exists?`/moods/${encodeURIComponent(m.id)}`:'/moods',m));}
  async remove(id){return this.request('DELETE',`/moods/${encodeURIComponent(id)}`);}
  async publish(id){return normalizePublication(await this.request('PUT','/active',{mood_id:id}));}
}
