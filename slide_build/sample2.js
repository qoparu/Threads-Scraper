// Концепт «Обзора» в стиле BioSync, под наш продукт. SVG -> PNG.
const sharp = require("sharp");
const W = 1280, H = 720;
const C = {
  page:"#e7e9ee", dark:"#0a0c11", card:"#ffffff",
  ink:"#1f2a44", ink2:"#6b7890", ink3:"#9aa6bd",
  dgrey:"#aab3c5", dline:"#1d2230",
  green:"#22c55e", lime:"#84cc16", yellow:"#eab308", orange:"#f59e0b", red:"#ef4444",
  track:"#eef1f7",
};
let e = [];
const R=(x,y,w,h,fill,r=16,o={})=>e.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" ${o.stroke?`stroke="${o.stroke}" stroke-width="${o.sw||1}"`:''}/>`);
const O=(cx,cy,r,fill,o={})=>e.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${fill}" ${o.stroke?`stroke="${o.stroke}" stroke-width="${o.sw||1}"`:''}/>`);
const T=(x,y,t,s,c,o={})=>{const a=o.align==='center'?'middle':o.align==='right'?'end':'start';const w=o.bold?700:o.semi?600:400;e.push(`<text x="${x}" y="${y}" font-family="Inter,'Segoe UI',sans-serif" font-size="${s}" fill="${c}" font-weight="${w}" text-anchor="${a}" dominant-baseline="${o.bl||'alphabetic'}">${String(t).replace(/&/g,'&amp;')}</text>`);};
const L=(x1,y1,x2,y2,c,w)=>e.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" stroke-linecap="round"/>`);
function hx(h){return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function lerp(a,b,t){const A=hx(a),B=hx(b);return `rgb(${Math.round(A[0]+(B[0]-A[0])*t)},${Math.round(A[1]+(B[1]-A[1])*t)},${Math.round(A[2]+(B[2]-A[2])*t)})`;}
function heat(t){return t<.5?lerp(C.green,C.yellow,t/.5):lerp(C.yellow,C.red,(t-.5)/.5);}

// defs: heat blobs + gradient bars
e.push(`<defs>
 <radialGradient id="hot" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#ef4444" stop-opacity=".95"/><stop offset="0.5" stop-color="#f59e0b" stop-opacity=".6"/><stop offset="1" stop-color="#f59e0b" stop-opacity="0"/></radialGradient>
 <radialGradient id="warm" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#eab308" stop-opacity=".9"/><stop offset="1" stop-color="#eab308" stop-opacity="0"/></radialGradient>
 <radialGradient id="cool" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="#22c55e" stop-opacity=".85"/><stop offset="1" stop-color="#22c55e" stop-opacity="0"/></radialGradient>
 <linearGradient id="risk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#22c55e"/><stop offset="0.55" stop-color="#eab308"/><stop offset="1" stop-color="#ef4444"/></linearGradient>
 <linearGradient id="scaleV" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ef4444"/><stop offset="0.5" stop-color="#eab308"/><stop offset="1" stop-color="#22c55e"/></linearGradient>
 <linearGradient id="amberbar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fdba74"/><stop offset="1" stop-color="#f59e0b"/></linearGradient>
 <linearGradient id="greenbar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#86efac"/><stop offset="1" stop-color="#22c55e"/></linearGradient>
 <linearGradient id="sparkfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#22c55e" stop-opacity=".30"/><stop offset="1" stop-color="#22c55e" stop-opacity="0"/></linearGradient>
</defs>`);
R(0,0,W,H,C.page,0);

// ===== TOP BAR =====
O(56,40,9,"none",{stroke:C.ink,sw:3}); L(56,33,56,47,C.ink,3); L(49,40,63,40,C.ink,3);
T(76,46,"Акимат · CityPulse",18,C.ink,{semi:true});
R(440,20,400,40,C.card,20); let nx=452; ["Обзор","Аналитика","Карта","Задачи","Обращения"].forEach((it,i)=>{const tw=it.length*8+22;if(i===0)R(nx,25,tw,30,C.dark,15);T(nx+tw/2,45,it,13,i===0?"#fff":C.ink2,{align:'center',semi:i===0});nx+=tw+6;});
O(1192,40,18,C.card); T(1192,46,"🔔",14,C.ink2,{align:'center'}); O(1234,40,18,"#cfd6e2"); T(1234,46,"🙂",15,C.ink2,{align:'center'});

// ===== HERO: two dark panels =====
// LEFT — карта/тепловая карта районов
R(40,84,560,280,C.dark,22);
T(64,118,"Карта обращений по районам",16,"#fff",{semi:true});
// thumbnails
[150,212,274].forEach(yy=>{R(60,yy,58,52,"#12161f",10,{stroke:C.dline,sw:1}); e.push(`<ellipse cx="89" cy="${yy+26}" rx="20" ry="16" fill="url(#warm)"/>`);});
// heat blobs (districts)
const blobs=[[300,180,"hot",70],[420,160,"warm",60],[250,260,"cool",66],[400,280,"hot",58],[470,230,"warm",54],[330,230,"warm",70],[200,200,"cool",50]];
blobs.forEach(b=>e.push(`<ellipse cx="${b[0]}" cy="${b[1]}" rx="${b[3]}" ry="${b[3]*0.8}" fill="url(#${b[1]})"/>`));
// vertical color scale
R(556,150,8,170,"url(#scaleV)",4); T(548,156,"макс",9,C.dgrey,{align:'right'}); T(548,322,"0",9,C.dgrey,{align:'right'});

// RIGHT — AI-аналитика
R(620,84,620,280,C.dark,22);
T(644,118,"AI-аналитика города",16,"#fff",{semi:true});
R(1086,100,130,26,"#15favorites".replace("#15favorites","#141925"),13,{stroke:C.dline,sw:1}); T(1151,117,"01.01 – 18.06.2026",10.5,C.dgrey,{align:'center'});
// two risk cards
const risk=[[644,"Доля негатива","рост за 3 дня — внимание","72%",.72],[940,"Острые инциденты","серьёзные обращения","8%",.18]];
risk.forEach(rk=>{R(rk[0],138,276,82,"#11151e",14,{stroke:C.dline,sw:1});
 T(rk[0]+18,164,rk[1],13,"#fff",{semi:true}); T(rk[0]+18,182,rk[2],10.5,C.dgrey);
 T(rk[0]+18,210,rk[3],20,"#fff",{bold:true});
 R(rk[0]+118,196,140,7,"#222a39",4); R(rk[0]+118,196,140,7,"url(#risk)",4);
 O(rk[0]+118+140*rk[4],199.5,7,"#fff",{stroke:"#0a0c11",sw:2});
});
// fan-bar gauge
const gcx=930,gcy=345,ri=58,ro=92,N=40,pct=.88;
for(let i=0;i<N;i++){const t=i/(N-1);const a=Math.PI-t*Math.PI;const dim=t>pct;
 const x1=gcx+ri*Math.cos(a),y1=gcy-ri*Math.sin(a),x2=gcx+ro*Math.cos(a),y2=gcy-ro*Math.sin(a);
 e.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${heat(t)}" stroke-width="4" stroke-linecap="round" opacity="${dim?0.28:1}"/>`);}
T(gcx,gcy-6,"88",36,"#fff",{align:'center',bold:true}); T(gcx,gcy+16,"напряжённость",11,C.dgrey,{align:'center'});

// ===== LIGHT CARDS (left 2x2) =====
function statTag(x,y,txt,col){const w=txt.length*6.5+22;R(x,y,w,20,"#fff",10,{stroke:C.track,sw:1});O(x+11,y+10,3,col);T(x+20,y+14,txt,11,C.ink2);}
// A: Обращения за сутки (sparkline)
R(40,384,287,140,C.card,18);
T(64,412,"Обращений за сутки",13,C.ink3,{semi:true}); statTag(232,400,"норма",C.green);
T(64,448,"124",30,C.ink,{bold:true});
const sx=64,sy=500,sw=240,sh=34;const ys=[.4,.5,.45,.6,.55,.7,.5,.65,.6,.8,.7,.85];
const pts=ys.map((v,i)=>`${sx+i*(sw/(ys.length-1))},${sy-v*sh}`);
e.push(`<polyline points="${sx},${sy} ${pts.join(' ')} ${sx+sw},${sy}" fill="url(#sparkfill)"/>`);
e.push(`<polyline points="${pts.join(' ')}" fill="none" stroke="${C.green}" stroke-width="2.5" stroke-linecap="round"/>`);
// B: Тональность (symmetry-like bars)
R(343,384,287,140,C.card,18);
T(367,412,"Тональность обращений",13,C.ink3,{semi:true}); statTag(560,400,"негатив",C.orange);
T(367,448,"72% −",26,C.ink,{bold:true});
for(let i=0;i<24;i++){const h=8+Math.abs(Math.sin(i*0.7))*22;e.push(`<rect x="${367+i*10}" y="${500-h}" width="4" height="${h}" rx="2" fill="${i<17?C.orange:C.green}"/>`);}
T(367,516,"негатив",9,C.ink3); T(607,516,"позитив",9,C.ink3,{align:'right'});
// C: Сегодня vs среднее (comparison)
R(40,540,287,140,C.card,18);
T(64,568,"Сутки vs среднее",13,C.ink3,{semi:true}); statTag(232,556,"выше",C.orange);
T(64,600,"124",26,C.ink,{bold:true}); T(112,600,"обращений",11,C.ink3);
T(64,626,"среднее",10,C.ink3); R(64,632,200,8,C.track,4); R(64,632,200*0.57,8,"url(#amberbar)",4); T(274,640,"71",10,C.ink2,{align:'right'});
T(64,656,"сегодня",10,C.ink3); R(64,662,200,8,C.track,4); R(64,662,200*0.92,8,"url(#amberbar)",4); T(274,670,"124",10,C.ink2,{align:'right'});
// D: Охват за сутки (comparison, green)
R(343,540,287,140,C.card,18);
T(367,568,"Охват за сутки",13,C.ink3,{semi:true}); statTag(560,556,"норма",C.green);
T(367,600,"42K",26,C.ink,{bold:true});
T(367,626,"среднее",10,C.ink3); R(367,632,200,8,C.track,4); R(367,632,200*0.8,8,"url(#greenbar)",4); T(607,640,"38K",10,C.ink2,{align:'right'});
T(367,656,"сегодня",10,C.ink3); R(367,662,200,8,C.track,4); R(367,662,200*0.86,8,"url(#greenbar)",4); T(607,670,"42K",10,C.ink2,{align:'right'});

// ===== SUGGESTED NEXT STEPS (right tall) =====
R(650,384,590,296,C.card,18);
T(674,414,"Очередь задач акимата",16,C.ink,{bold:true});
R(1118,396,100,28,C.dark,14); T(1168,414,"Создать план +",11.5,"#fff",{align:'center',semi:true});
const steps=[
 ["🛡","Сегодня · 24 ч","Безопасность",["Отработать адресные обращения, дать публичный ответ","Усилить патрулирование по горячим точкам"]],
 ["🚧","Эта неделя","Дороги и транспорт",["Картировать аварийные участки из обращений","Опубликовать график ремонта"]],
 ["📣","Эта неделя","Коммуникация",["Разъяснение по росту негатива","Ответы от лица города по топ-темам"]],
 ["🔄","Постоянно","Мониторинг",["Еженедельная сводка по районам","Трекинг ключевых тем 24/7"]],
];
let yy=444;
steps.forEach((s,i)=>{
 O(686,yy+6,15,"#f1f4fa",{stroke:C.track,sw:1}); T(686,yy+11,s[0],13,C.ink,{align:'center'});
 T(712,yy+2,s[2],13.5,C.ink,{semi:true});
 const tagw=s[1].length*6+18; R(712,yy+10,tagw,18,"#f1f4fa",9); T(712+tagw/2,yy+23,s[1],10,C.ink2,{align:'center'});
 s[3].forEach((b,j)=>{O(900,yy-1+j*18,2,C.ink3); T(910,yy+3+j*18,b,11.5,C.ink2);});
 yy+=58; if(i<steps.length-1)e.push(`<line x1="674" y1="${yy-16}" x2="1216" y2="${yy-16}" stroke="${C.track}" stroke-width="1"/>`);
});

const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${e.join('')}</svg>`;
sharp(Buffer.from(svg)).png().toFile("sample2.png").then(()=>console.log("sample2.png written"));
