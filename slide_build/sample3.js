// Концепт: app-shell с сайдбаром (стиль CHRONYX) под наш продукт. SVG -> PNG.
const sharp = require("sharp");
const W = 1280, H = 864;
const C = {
  page:"#f4f7fb", side:"#ffffff", card:"#ffffff",
  ink:"#1f2a44", ink2:"#5c6b86", ink3:"#9aa6bd", line:"#e9edf6", track:"#eef1f7",
  indigo:"#6366f1", indbg:"#eef0ff", sky:"#38bdf8",
  green:"#22c55e", yellow:"#eab308", red:"#ef4444",
};
let e=[];
const R=(x,y,w,h,f,r=14,o={})=>e.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${f}" ${o.stroke?`stroke="${o.stroke}" stroke-width="${o.sw||1}"`:''}/>`);
const O=(cx,cy,r,f,o={})=>e.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${f}" ${o.stroke?`stroke="${o.stroke}" stroke-width="${o.sw||1}"`:''}/>`);
const T=(x,y,t,s,c,o={})=>{const a=o.align==='center'?'middle':o.align==='right'?'end':'start';const w=o.bold?700:o.semi?600:400;e.push(`<text x="${x}" y="${y}" font-family="Inter,'Segoe UI',sans-serif" font-size="${s}" fill="${c}" font-weight="${w}" text-anchor="${a}">${String(t).replace(/&/g,'&amp;')}</text>`);};
const LN=(x1,y1,x2,y2,c,w=1)=>e.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}"/>`);
function hx(h){return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function lerp(a,b,t){const A=hx(a),B=hx(b);return `rgb(${Math.round(A[0]+(B[0]-A[0])*t)},${Math.round(A[1]+(B[1]-A[1])*t)},${Math.round(A[2]+(B[2]-A[2])*t)})`;}
function heat(t){t=Math.max(0,Math.min(1,t));return t<.5?lerp('#22c55e','#eab308',t/.5):lerp('#eab308','#ef4444',(t-.5)/.5);}
function spark(x,y,w,h,vals,col){const mx=Math.max(...vals),mn=Math.min(...vals);const pts=vals.map((v,i)=>`${(x+i*(w/(vals.length-1))).toFixed(1)},${(y+h-((v-mn)/((mx-mn)||1))*h).toFixed(1)}`);e.push(`<polyline points="${x},${y+h} ${pts.join(' ')} ${x+w},${y+h}" fill="${col}" opacity=".12"/><polyline points="${pts.join(' ')}" fill="none" stroke="${col}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>`);}

R(0,0,W,H,C.page,0);

// ===== SIDEBAR =====
R(0,0,220,H,C.side,0,{stroke:C.line,sw:1});
O(34,40,13,"none",{stroke:C.indigo,sw:3}); O(34,40,5,C.sky); T(56,46,"CityPulse",18,C.ink,{bold:true});
const nav=[["▣","Обзор",1],["▤","Аналитика",0],["🗺","Карта",0],["✔","Задачи",0],["✉","Обращения",0],["🔍","Пропавшие",0]];
let ny=96; nav.forEach(n=>{ if(n[2])R(14,ny-20,192,38,C.indbg,11); T(34,ny+5,n[0],14,n[2]?C.indigo:C.ink3,{align:'center'}); T(56,ny+5,n[1],14,n[2]?C.indigo:C.ink2,{semi:!!n[2]}); ny+=46;});
LN(20,ny+2,200,ny+2,C.line);
const bot=[["⚙","Настройки"],["◐","Тема (свет/тёмная)"],["🛡","Безопасность"],["⎋","Выход"]];
let by=H-172; bot.forEach(b=>{T(34,by+5,b[0],13,C.ink3,{align:'center'}); T(56,by+5,b[1],13,C.ink2); by+=34;});

// ===== TOP METRIC STRIP =====
R(244,20,1012,54,C.card,16,{stroke:C.line,sw:1});
const metrics=[["Обращений","2 127"],["Охват","938K"],["Настроение","49/100"],["Напряжённость","88"],["Авторов","746"],["Районов","30"]];
let mx=272; metrics.forEach((m,i)=>{ T(mx,42,m[0],11,C.ink3); T(mx,62,m[1],17,C.ink,{bold:true}); mx+=168; if(i<metrics.length-1)LN(mx-24,32,mx-24,62,C.line);});

// ===== MAIN CENTER =====
const MX=244, MW=586;
T(MX,110,"Обзор города",22,C.ink,{bold:true}); T(MX,130,"Социальный слух Алматы · 01.01 – 18.06.2026",12,C.ink3);
R(MX+MW-150,96,96,32,C.card,16,{stroke:C.line,sw:1}); T(MX+MW-102,116,"Фильтр ▾",12,C.ink2,{align:'center'});
O(MX+MW-28,112,16,C.indigo); T(MX+MW-28,117,"⟳",14,"#fff",{align:'center'});
// 3 KPI cards
const kw=(MW-2*14)/3, ky=150;
const kpis=[["VO₂ · за сутки","124","+ выше нормы",C.green],["Доля негатива","52%","умеренная",C.red],["Индекс настроения","49/100","стабильно",C.sky]];
kpis.forEach((k,i)=>{const x=MX+i*(kw+14);R(x,ky,kw,92,C.card,16,{stroke:C.line,sw:1});T(x+16,ky+28,k[0],11.5,C.ink3,{semi:true});T(x+16,ky+62,k[1],24,C.ink,{bold:true});T(x+16,ky+82,k[2],10.5,k[3]);});
// Матрица (radar) + Горящие темы
const cardY=260, cH=232, halfW=(MW-14)/2;
R(MX,cardY,halfW,cH,C.card,16,{stroke:C.line,sw:1});
T(MX+18,cardY+30,"Матрица угроз по темам",14,C.ink,{bold:true});
[["Безопасн.",C.indigo],["Дороги",C.ink3],["Экология",C.ink3]].forEach((t,i)=>{O(MX+22+i*95,cardY+50,4,t[1]);T(MX+32+i*95,cardY+54,t[0],10.5,C.ink2);});
// radar
const rcx=MX+halfW/2, rcy=cardY+150, rr=64, cats=["Безопасность","Дороги","Экология","Госуслуги","ЖКХ","Стройка"], vals=[.95,.7,.55,.4,.6,.5];
for(let ring=1;ring<=3;ring++){const rad=rr*ring/3;let p=[];for(let i=0;i<6;i++){const a=-Math.PI/2+i*Math.PI/3;p.push(`${(rcx+rad*Math.cos(a)).toFixed(1)},${(rcy+rad*Math.sin(a)).toFixed(1)}`);}e.push(`<polygon points="${p.join(' ')}" fill="none" stroke="#e5e9f2"/>`);}
let dp=[];for(let i=0;i<6;i++){const a=-Math.PI/2+i*Math.PI/3;LN(rcx,rcy,rcx+rr*Math.cos(a),rcy+rr*Math.sin(a),"#e5e9f2");dp.push(`${(rcx+rr*vals[i]*Math.cos(a)).toFixed(1)},${(rcy+rr*vals[i]*Math.sin(a)).toFixed(1)}`);}
e.push(`<polygon points="${dp.join(' ')}" fill="rgba(99,102,241,.22)" stroke="${C.indigo}" stroke-width="2"/>`);
// Горящие темы (why)
const wx=MX+halfW+14; R(wx,cardY,halfW,cH,C.card,16,{stroke:C.line,sw:1});
T(wx+18,cardY+30,"Почему такой уровень",14,C.ink,{bold:true});
const facts=[["Безопасность","72% негатива",C.red],["Дороги и транспорт","60% негатива",C.yellow],["Экология","65% негатива",C.red]];
facts.forEach((f,i)=>{const yy=cardY+58+i*40;O(wx+24,yy-4,4,f[2]);T(wx+36,yy,f[0],12.5,C.ink,{semi:true});T(wx+36,yy+15,f[1],10.5,C.ink3);});
T(wx+18,cardY+186,"▸ Рекомендация: адресные ответы + патрулирование",11,C.ink2);
// таблица обращений
const tY=cardY+cH+20; R(MX,tY,MW,150,C.card,16,{stroke:C.line,sw:1});
T(MX+18,tY+28,"Последние обращения",14,C.ink,{bold:true}); T(MX+MW-18,tY+28,"Все обращения →",11.5,C.indigo,{align:'right'});
["Тема","Район","Острота","Охват"].forEach((h,i)=>T(MX+20+i*140,tY+52,h,10.5,C.ink3,{semi:true}));
[["Безопасность","Алмалинский","5","6 036"],["Дороги","Медеуский","4","4 917"]].forEach((row,r)=>{const yy=tY+80+r*30;LN(MX+18,yy-14,MX+MW-18,yy-14,C.line);row.forEach((cval,i)=>T(MX+20+i*140,yy,cval,11.5,i===2?C.red:C.ink2,{semi:i===2}));});

// ===== RIGHT RAIL =====
const RX=850, RW=406;
// Районы (вместо сердца)
R(RX,96,RW,250,C.card,18,{stroke:C.line,sw:1});
T(RX+20,126,"Районы города · напряжённость",13.5,C.ink,{bold:true});
const dist=[["Алмалинский",.92],["Бостандыкский",.78],["Медеуский",.7],["Ауэзовский",.55],["Турксибский",.6],["Жетысуский",.45],["Наурызбайский",.35],["Алатауский",.5]];
const cols=2,tw=(RW-40-14)/cols,th=44;
dist.forEach((d,i)=>{const cx=RX+20+(i%cols)*(tw+14),cy=140+Math.floor(i/cols)*(th+8);R(cx,cy,tw,th,heat(d[1]),10);T(cx+12,cy+19,d[0],10.5,"#fff",{semi:true});T(cx+12,cy+35,Math.round(d[1]*100),13,"#fff",{bold:true});});
// overlay index
R(RX+20,326,RW-40,0.1,C.line,0);
T(RX+20,340,"Индекс напряжённости",11,C.ink3); T(RX+RW-20,340,"88 / 100",13,C.red,{align:'right',bold:true});
// Динамика (line)
R(RX,362,RW,150,C.card,18,{stroke:C.line,sw:1});
T(RX+20,390,"Динамика обращений",13,C.ink,{bold:true}); R(RX+RW-84,376,64,22,C.indbg,11); T(RX+RW-52,391,"24ч · 7д",10.5,C.indigo,{align:'center'});
spark(RX+20,414,RW-40,74,[3,5,4,6,5,7,6,8,7,9,8,10,9,11],C.sky);
// Тональность тренд
R(RX,528,RW,150,C.card,18,{stroke:C.line,sw:1});
T(RX+20,556,"Тональность · тренд негатива",13,C.ink,{bold:true}); R(RX+RW-84,542,64,22,C.indbg,11); T(RX+RW-52,557,"30д",10.5,C.indigo,{align:'center'});
spark(RX+20,580,RW-40,74,[6,5,7,6,8,7,6,8,9,7,8,6,7,9],C.red);

const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${e.join('')}</svg>`;
sharp(Buffer.from(svg)).png().toFile("sample3.png").then(()=>console.log("sample3.png written"));
