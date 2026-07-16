// Концепт дашборда в стиле Viora, адаптированный под гос-контекст. SVG -> PNG.
const sharp = require("sharp");
const W = 1280, H = 820;
const C = {
  ink:"#1f2a44", ink2:"#5c6b86", ink3:"#95a2bb",
  card:"#ffffff", line:"#eaeef6", track:"#eef1f7",
  indigo:"#6366f1", sky:"#38bdf8", coral:"#fb7185", amber:"#f6b756", green:"#34d399", greenL:"#6ee7b7",
};
let e = [];
const R = (x,y,w,h,fill,r=20,opts={})=>e.push(`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${r}" fill="${fill}" ${opts.stroke?`stroke="${opts.stroke}" stroke-width="${opts.sw||1}"`:''} ${opts.filter?`filter="url(#soft)"`:''}/>`);
const O = (cx,cy,r,fill,opts={})=>e.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${fill}" ${opts.stroke?`stroke="${opts.stroke}" stroke-width="${opts.sw||1}"`:''}/>`);
const T = (x,y,t,size,color,opts={})=>{
  const a = opts.align==='center'?'middle':opts.align==='right'?'end':'start';
  const w = opts.bold?700:opts.semi?600:400;
  e.push(`<text x="${x}" y="${y}" font-family="Inter, 'Segoe UI', sans-serif" font-size="${size}" fill="${color}" font-weight="${w}" text-anchor="${a}" dominant-baseline="${opts.baseline||'alphabetic'}" letter-spacing="${opts.ls||0}">${String(t).replace(/&/g,'&amp;')}</text>`);
};
const donut = (cx,cy,r,sw,pct,color)=>{
  const Cc = 2*Math.PI*r, dash = pct*Cc;
  e.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${C.track}" stroke-width="${sw}"/>`);
  e.push(`<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-dasharray="${dash} ${Cc-dash}" transform="rotate(-90 ${cx} ${cy})"/>`);
};
const bars = (x,y,h,vals,color)=>{ const bw=4,g=3; vals.forEach((v,i)=>{ const bh=Math.max(3,v*h); e.push(`<rect x="${x+i*(bw+g)}" y="${y+h-bh}" width="${bw}" height="${bh}" rx="2" fill="${color}"/>`); }); };
const spark = (x,y,w,h,vals,color)=>{ const mx=Math.max(...vals),mn=Math.min(...vals); const pts=vals.map((v,i)=>`${x+i*(w/(vals.length-1))},${y+h-((v-mn)/(mx-mn||1))*h}`).join(' '); e.push(`<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`); };

// defs
e.push(`<defs>
 <radialGradient id="bg1" cx="0.88" cy="-0.05" r="0.5"><stop offset="0" stop-color="#6366f1" stop-opacity="0.10"/><stop offset="1" stop-color="#6366f1" stop-opacity="0"/></radialGradient>
 <radialGradient id="bg2" cx="0.02" cy="1.05" r="0.55"><stop offset="0" stop-color="#38bdf8" stop-opacity="0.10"/><stop offset="1" stop-color="#38bdf8" stop-opacity="0"/></radialGradient>
 <linearGradient id="gauge" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#6ee7b7"/><stop offset="0.5" stop-color="#f6b756"/><stop offset="1" stop-color="#fb7185"/></linearGradient>
 <linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6366f1" stop-opacity="0.28"/><stop offset="1" stop-color="#6366f1" stop-opacity="0.02"/></linearGradient>
 <filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="8" stdDeviation="16" flood-color="#1f2a44" flood-opacity="0.07"/></filter>
</defs>`);
e.push(`<rect width="${W}" height="${H}" fill="#f5f7fb"/><rect width="${W}" height="${H}" fill="url(#bg1)"/><rect width="${W}" height="${H}" fill="url(#bg2)"/>`);

// ===== TOP BAR =====
O(60,46,18,"none",{stroke:C.indigo,sw:3}); O(60,46,7,C.sky);
T(90,52,"Акимат · CityPulse",18,C.ink,{semi:true});
// center pill nav
const navX=440,navW=400,navY=28,navH=40; R(navX,navY,navW,navH,"#ffffff",20,{stroke:C.line,filter:true});
const items=["Обзор","Аналитика","Карта","Задачи","Обращения"]; let nx=navX+8;
items.forEach((it,i)=>{ const tw=it.length*8+24; if(i===0){R(nx,navY+5,tw,navH-10,"#eef0ff",15);} T(nx+tw/2,navY+navH/2+4,it,13,i===0?C.indigo:C.ink2,{align:'center',semi:i===0}); nx+=tw+6; });
// right icons
[1140,1180].forEach(cx=>{O(cx,48,17,"#ffffff",{stroke:C.line}); }); T(1140,53,"🔍",13,C.ink2,{align:'center'}); T(1180,53,"🔔",13,C.ink2,{align:'center'});
O(1224,48,19,"#dfe6f2"); T(1224,54,"🙂",16,C.ink2,{align:'center'});

// ===== TITLE ROW =====
T(40,118,"Обзор города",30,C.ink,{bold:true});
R(1010,98,150,34,"#ffffff",17,{stroke:C.line,filter:true}); T(1085,120,"Последние 30 дней",12.5,C.ink2,{align:'center'});
R(1172,98,68,34,"#ffffff",17,{stroke:C.line,filter:true}); T(1206,120,"Фильтр",12.5,C.ink2,{align:'center'});

// ===== KPI ROW =====
const kpis=[
 {l:"Обращений",v:"2 127",d:"↑ 12%",dc:C.green,viz:"bars",vc:C.indigo,data:[.4,.6,.5,.7,.65,.85,.8]},
 {l:"Суммарный охват",v:"938K",d:"↑ 6%",dc:C.green,viz:"spark",vc:C.sky,data:[3,5,4,6,7,6,8]},
 {l:"Индекс настроения",v:"49",u:"/100",d:"→ 0%",dc:C.ink3,viz:"ring",vc:C.amber,pct:.49},
 {l:"Напряжённость",v:"88",u:"/100",d:"↑ 7%",dc:C.coral,viz:"ring",vc:C.coral,pct:.88},
 {l:"Жалоб",v:"1 583",d:"↑ 9%",dc:C.coral,viz:"bars",vc:C.coral,data:[.5,.45,.6,.7,.65,.8,.9]},
];
const kw=227,kg=16,ky=158,kh=132; let kx=40;
kpis.forEach(k=>{
  R(kx,ky,kw,kh,C.card,20,{filter:true});
  T(kx+20,ky+30,k.l,12.5,C.ink3,{semi:true});
  T(kx+20,ky+72,k.v,30,C.ink,{bold:true}); if(k.u)T(kx+20+(String(k.v).length*17),ky+72,k.u,14,C.ink3);
  T(kx+20,ky+102,k.d+"  ",12.5,k.dc,{semi:true}); T(kx+20+44,ky+102,"за месяц",11.5,C.ink3);
  if(k.viz==="bars") bars(kx+kw-70,ky+40,46,k.data,k.vc);
  else if(k.viz==="spark") spark(kx+kw-78,ky+44,56,40,k.data,k.vc);
  else { donut(kx+kw-46,ky+kh/2,24,7,k.pct,k.vc); T(kx+kw-46,ky+kh/2+4,Math.round(k.pct*100),12,C.ink,{align:'center',bold:true}); }
  kx+=kw+kg;
});

// ===== BIG ROW: chart + gauge =====
const by=312, bh=246;
// chart card
R(40,by,740,bh,C.card,20,{filter:true});
T(64,by+34,"Динамика обращений",16,C.ink,{semi:true});
T(64,by+72,"+18%",26,C.ink,{bold:true}); T(118,by+72,"к прошлому месяцу",12.5,C.ink3);
// area chart
const cx0=64,cy0=by+200,cw=688,chh=96;
const ys=[.35,.5,.42,.6,.55,.72,.68,.82,.78,.9];
const pts=ys.map((v,i)=>`${cx0+i*(cw/(ys.length-1))},${cy0-v*chh}`);
e.push(`<polyline points="${cx0},${cy0} ${pts.join(' ')} ${cx0+cw},${cy0}" fill="url(#area)" stroke="none"/>`);
e.push(`<polyline points="${pts.join(' ')}" fill="none" stroke="${C.indigo}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>`);
["Янв","Фев","Мар","Апр","Май","Июн"].forEach((m,i)=>T(cx0+i*(cw/5),cy0+24,m,11,C.ink3,{align:'center'}));
// gauge card
const gx=796,gw=444; R(gx,by,gw,bh,C.card,20,{filter:true});
T(gx+24,by+34,"Индекс напряжённости",16,C.ink,{semi:true});
const gcx=gx+gw/2, gcy=by+170, gr=120, pct=.88;
e.push(`<path d="M ${gcx-gr} ${gcy} A ${gr} ${gr} 0 0 1 ${gcx+gr} ${gcy}" fill="none" stroke="${C.track}" stroke-width="20" stroke-linecap="round"/>`);
const semi=Math.PI*gr, dash=pct*semi;
e.push(`<path d="M ${gcx-gr} ${gcy} A ${gr} ${gr} 0 0 1 ${gcx+gr} ${gcy}" fill="none" stroke="url(#gauge)" stroke-width="20" stroke-linecap="round" stroke-dasharray="${dash} ${semi-dash}"/>`);
const ang=Math.PI-pct*Math.PI; const nx2=gcx+Math.cos(ang)*(gr-30), ny2=gcy-Math.sin(ang)*(gr-30);
e.push(`<line x1="${gcx}" y1="${gcy}" x2="${nx2}" y2="${ny2}" stroke="${C.ink}" stroke-width="3" stroke-linecap="round"/>`); O(gcx,gcy,6,C.ink);
T(gcx,by+150,"88",40,C.ink,{align:'center',bold:true});
T(gcx,by+202,"Высокая напряжённость",13,C.coral,{align:'center',semi:true});

// ===== BOTTOM ROW: alarm + districts =====
const ly=580, lh=192;
// alarm card (мягкий коралл)
R(40,ly,740,lh,"#fff5f7",20,{filter:true}); R(40,ly,5,lh,C.coral,2.5);
T(64,ly+38,"Сигналы тревоги",16,C.ink,{semi:true});
R(64,ly+54,210,28,"#ffe4ea",14); T(169,ly+72,"🚨 Безопасность · +негатив",12,"#c2415c",{align:'center',semi:true});
T(64,ly+108,"Рост негатива за 3 дня по теме «безопасность».",14,C.ink2);
T(64,ly+132,"Рекомендация: усилить патрулирование, дать публичный ответ.",13,C.ink3);
R(64,ly+150,150,30,C.coral,15); T(139,ly+170,"Перейти к задачам",12,"#ffffff",{align:'center',semi:true});
// districts card
const dx=796,dw=444; R(dx,ly,dw,lh,C.card,20,{filter:true});
T(dx+24,ly+38,"Районы по напряжённости",16,C.ink,{semi:true});
const dist=[["Алмалинский",.9,C.coral],["Бостандыкский",.72,C.amber],["Медеуский",.55,C.indigo]];
dist.forEach((d,i)=>{ const yy=ly+72+i*38;
  T(dx+24,yy+4,d[0],13,C.ink2); T(dx+dw-24,yy+4,Math.round(d[1]*100),12.5,C.ink,{align:'right',semi:true});
  R(dx+24,yy+12,dw-48,8,C.track,4); R(dx+24,yy+12,(dw-48)*d[1],8,d[2],4);
});

const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${e.join('')}</svg>`;
sharp(Buffer.from(svg)).png().toFile("sample.png").then(()=>console.log("sample.png written"));
