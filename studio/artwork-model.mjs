export const WIDTH=80, HEIGHT=60, FRAME_BYTES=4800, MAX_FRAMES=8, MAX_PACK_BYTES=38412;
export function crc32(bytes){let crc=0xffffffff;for(const v of bytes){crc^=v;for(let i=0;i<8;i++)crc=(crc>>>1)^(0xedb88320&-(crc&1));}return (crc^0xffffffff)>>>0;}
export function encodePack(frames,duration,boop){
  if(!Array.isArray(frames)||frames.length<1||frames.length>8||typeof boop!=='boolean'||frames.length<=Number(boop)||!Number.isInteger(duration)||duration<250||duration>5000||frames.some(f=>!(f instanceof Uint8Array)||f.length!==FRAME_BYTES))throw Error('Choose 1–8 frames, at least one loop frame, and 250–5000 ms duration.');
  const bytes=new Uint8Array(12+frames.length*FRAME_BYTES), view=new DataView(bytes.buffer);
  bytes.set([83,86,80,49,frames.length,Number(boop)]);view.setUint16(6,duration,true);
  frames.forEach((f,i)=>bytes.set(f,8+i*FRAME_BYTES));view.setUint32(bytes.length-4,crc32(bytes.subarray(0,-4)),true);return bytes;
}
export function decodePack(bytes){
  if(!(bytes instanceof Uint8Array)||bytes.length<4812||bytes.length>MAX_PACK_BYTES)throw Error('Invalid pack size.');
  const view=new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),n=bytes[4],b=bytes[5],duration=view.getUint16(6,true);
  if(bytes[0]!==83||bytes[1]!==86||bytes[2]!==80||bytes[3]!==49||n<1||n>8||b>1||n<=b||duration<250||duration>5000||bytes.length!==12+n*FRAME_BYTES||view.getUint32(bytes.length-4,true)!==crc32(bytes.subarray(0,-4)))throw Error('Invalid pack header or checksum.');
  return {frames:Array.from({length:n},(_,i)=>bytes.slice(8+i*FRAME_BYTES,8+(i+1)*FRAME_BYTES)),duration,boop:Boolean(b)};
}
export function toBase64(bytes){let s='';for(let i=0;i<bytes.length;i++)s+=String.fromCharCode(bytes[i]);return btoa(s);}
export function fromBase64(value){if(typeof value!=='string'||value.length>51216)throw Error('Invalid pack encoding.');const raw=Uint8Array.from(atob(value),c=>c.charCodeAt(0));if(toBase64(raw)!==value)throw Error('Noncanonical encoding.');return raw;}
export function quantize(rgba){if(rgba.length!==FRAME_BYTES*4)throw Error('Expected 80 × 60 RGBA pixels.');const result=new Uint8Array(FRAME_BYTES);for(let i=0;i<result.length;i++){const p=i*4;result[i]=(rgba[p]&224)|((rgba[p+1]&224)>>3)|(rgba[p+2]>>6);}return result;}
export function expand(value){const r=(value>>5)*31/7|0,g=((value>>2)&7)*63/7|0,b=(value&3)*31/3|0;return [Math.round(r*255/31),Math.round(g*255/63),Math.round(b*255/31),255];}
export function paintFrame(canvas,frame){const ctx=canvas.getContext('2d');const image=ctx.createImageData(WIDTH,HEIGHT);for(let i=0;i<frame.length;i++)image.data.set(expand(frame[i]),i*4);ctx.putImageData(image,0,0);}
