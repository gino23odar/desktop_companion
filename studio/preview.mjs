import {animationFrame,boopMood} from './model.mjs';
const pink='#F491AA',blush='#F78CA7';
const staticFrame={eyesClosed:false,earOffset:0,accessoryOffset:0};
function ink(bg){const c=bg.slice(1).match(/../g).map(x=>parseInt(x,16));return .299*c[0]+.587*c[1]+.114*c[2]<128?'#FFFFFF':'#000000';}
function path(ctx,points,color,filled=true){ctx.beginPath();ctx.moveTo(...points[0]);for(const p of points.slice(1))ctx.lineTo(...p);if(filled){ctx.closePath();ctx.fillStyle=color;ctx.fill();}else{ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();}}
function circle(ctx,x,y,r,color){ctx.beginPath();ctx.arc(x,y,r,0,2*Math.PI);ctx.fillStyle=color;ctx.fill();}
function rounded(ctx,x,y,w,h,r,color,fill=true){ctx.beginPath();ctx.roundRect(x,y,w,h,r);if(fill){ctx.fillStyle=color;ctx.fill();}else{ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();}}
export function drawMood(canvas,m,frame=staticFrame){
  const c=canvas.getContext('2d'),i=ink(m.background),e=frame.earOffset,o=frame.accessoryOffset;
  c.fillStyle=m.background;c.fillRect(0,0,320,240);
  path(c,[[60,90],[90+e,45],[120,90]],pink);path(c,[[200,90],[230-e,45],[260,90]],pink);
  for(const x of [110,210]){
    if(m.eyes==='happy')path(c,[[x-12,115],[x,103],[x+12,115]],i,false);
    else if(m.eyes==='sleepy')path(c,[[x-12,115],[x,121],[x+12,115]],i,false);
    else if(frame.eyesClosed)path(c,[[x-12,115],[x+12,115]],i,false);
    else if(m.eyes==='excited'){circle(c,x,112,14,i);circle(c,x-4,108,4,m.background);}
    else circle(c,x,115,10,i);
    if(m.eyes==='glasses')rounded(c,x-23,96,46,37,5,i,false);
  }
  if(m.eyes==='glasses')path(c,[[133,109],[187,109]],i,false);
  if(m.blush){rounded(c,66,139,40,16,8,blush);rounded(c,214,139,40,16,8,blush);}
  rounded(c,125,140,70,45,20,pink);circle(c,145,162,6,'#222222');circle(c,175,162,6,'#222222');
  if(m.mouth==='smile')path(c,[[150,193],[160,199],[170,193]],i,false);
  if(m.mouth==='neutral')path(c,[[150,195],[170,195]],i,false);
  if(m.mouth==='open')rounded(c,153,190,14,10,4,i);
  if(m.accessory==='heart'){circle(c,272,42+o,9,'#DF426B');circle(c,288,42+o,9,'#DF426B');path(c,[[263,45+o],[297,45+o],[280,64+o]],'#DF426B');}
  if(m.accessory==='star'){for(const p of [[[280,29],[268,65],[297,43]],[[280,29],[292,65],[263,43]],[[263,43],[297,43],[280,57]]])path(c,p.map(([x,y])=>[x,y+o]),'#E7B63A');}
  c.fillStyle=i;c.font='bold 16px monospace';c.textBaseline='top';c.textAlign='left';
  if(m.accessory==='zzz')c.fillText('Zzz',263,40+o);
  c.textAlign='center';c.fillText(m.message,160,210,288);
}
export class Preview {
  constructor(canvas){this.canvas=canvas;this.mood=null;this.animate=true;this.start=0;this.boopUntil=0;this.last='';this.running=false;this.handle=0;}
  set(mood,animate=true){this.mood=mood;this.animate=animate;this.start=performance.now();this.boopUntil=0;this.last='';if(mood)drawMood(this.canvas,mood);else this.canvas.getContext('2d').clearRect(0,0,320,240);}
  boop(){if(this.mood){this.boopUntil=performance.now()+1000;this.last='';}}
  tick(now){if(!this.mood)return;const booping=now<this.boopUntil;if(!booping&&this.boopUntil){this.boopUntil=0;this.start=now;}const frame=booping||!this.animate?staticFrame:animationFrame(this.mood.animation,now-this.start);const key=JSON.stringify([booping,frame]);if(key!==this.last){drawMood(this.canvas,booping?boopMood(this.mood):this.mood,frame);this.last=key;}}
  run(){if(this.running)return;this.running=true;const loop=now=>{if(!this.running)return;this.tick(now);this.handle=requestAnimationFrame(loop);};this.handle=requestAnimationFrame(loop);}
  stop(){this.running=false;cancelAnimationFrame(this.handle);}
}
