// Faithful PNG mock of the STRATEGY slide for visual QA (same inch coords * 96).
const sharp = require("sharp");
const PX = 96;
const W = 13.333 * PX, H = 7.5 * PX;
const C = { card:"#1B2A4E", cardLn:"#2C3E6B", white:"#FFFFFF", muted:"#9FB0D0", ink3:"#6E80A6",
  indigo:"#6366F1", sky:"#38BDF8", teal:"#2DD4BF", rose:"#FB5577", green:"#34D399", amber:"#FBBF24", bg:"#0F1B34" };
const pt = n => n * 1.3333;
let el = [];
const rect=(x,y,w,h,fill,r=8,stroke=null)=>el.push(`<rect x="${x*PX}" y="${y*PX}" width="${w*PX}" height="${h*PX}" rx="${r}" fill="${fill}" ${stroke?`stroke="${stroke}" stroke-width="1"`:''}/>`);
const oval=(x,y,w,h,fill)=>el.push(`<ellipse cx="${(x+w/2)*PX}" cy="${(y+h/2)*PX}" rx="${w/2*PX}" ry="${h/2*PX}" fill="${fill}"/>`);
const txt=(x,y,w,h,t,size,color,opts={})=>{
  const anchor=opts.align==='center'?'middle':opts.align==='right'?'end':'start';
  const tx=(opts.align==='center'?(x+w/2):opts.align==='right'?(x+w):x)*PX;
  const ty=(y+h/2)*PX; const weight=opts.bold?'700':'400';
  const lines=Array.isArray(t)?t:[t];
  const lh=pt(size)*1.18; const startY=(opts.top? y*PX+pt(size) : ty-(lines.length-1)*lh/2);
  lines.forEach((ln,i)=>{
    el.push(`<text x="${tx}" y="${startY+i*lh}" font-family="${opts.face||'Calibri, sans-serif'}" font-size="${pt(size)}" fill="${color}" font-weight="${weight}" text-anchor="${anchor}" dominant-baseline="${opts.top?'auto':'central'}">${ln.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</text>`);
  });
};
const wrap=(t,n)=>{const words=t.split(' ');const out=[];let cur='';words.forEach(w=>{if((cur+' '+w).trim().length>n){out.push(cur.trim());cur=w;}else cur+=' '+w;});if(cur.trim())out.push(cur.trim());return out;};

el.push(`<defs>
  <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0F1B34"/><stop offset="0.55" stop-color="#13203F"/><stop offset="1" stop-color="#1A2A52"/></linearGradient>
  <radialGradient id="r1" cx="0.85" cy="0.05" r="0.5"><stop offset="0" stop-color="#4F46E5" stop-opacity="0.4"/><stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>
  <radialGradient id="r2" cx="0.05" cy="0.95" r="0.55"><stop offset="0" stop-color="#0EA5E9" stop-opacity="0.26"/><stop offset="1" stop-color="#0EA5E9" stop-opacity="0"/></radialGradient></defs>
  <rect width="${W}" height="${H}" fill="url(#g)"/><rect width="${W}" height="${H}" fill="url(#r1)"/><rect width="${W}" height="${H}" fill="url(#r2)"/>`);

// header
rect(0.5,0.4,0.76,0.76,C.indigo,11); txt(0.5,0.4,0.76,0.76,"🏛",18,C.white,{align:'center'});
txt(1.4,0.36,9.2,0.55,"Data-driven управление городом",27,C.white,{bold:true,face:'Trebuchet MS'});
txt(1.42,0.9,9.2,0.32,"Социальные сигналы горожан как инструмент управления · Акимат г. Алматы",13.5,C.muted);
rect(10.62,0.45,2.21,0.66,C.card,8,C.cardLn); txt(10.62,0.45,2.21,0.66,"Стратегическая инициатива",10.5,C.sky,{align:'center',bold:true});

// vision band
const vy=1.36,vh=0.94;
rect(0.5,vy,12.33,vh,C.card,8,C.cardLn); rect(0.5,vy,0.08,vh,C.sky,0);
oval(0.78,vy+0.24,0.4,0.4,'#10243f'); txt(0.78,vy+0.24,0.4,0.4,"❝",16,C.sky,{align:'center'});
txt(1.4,vy+0.12,11.2,0.4,"Управлять городом на основе данных, а не предположений.",18,C.white,{bold:true,face:'Trebuchet MS'});
txt(1.4,vy+0.5,11.2,0.34,"Непрерывно слышим голос горожан в соцсетях и переходим от реакции на жалобы — к упреждению проблем.",13,C.muted);

// pillars
const pillars=[["Слышим город 24/7","Непрерывный сбор сигналов из Threads, Facebook и Instagram. Город на связи круглосуточно.",C.sky],
 ["Суверенный AI","Локальная модель Qwen фильтрует и проверяет посты. Данные не уходят в облако.",C.indigo],
 ["От шума — к задачам","Приоритизация по срочности и адресные поручения профильным управлениям.",C.teal],
 ["Проактивность","Действуем до эскалации, а не по факту кризиса. Ответ — раньше негатива.",C.amber]];
const pw=2.95,pgap=0.143,ppy=2.5,pph=2.06;
pillars.forEach((p,i)=>{const x=0.5+i*(pw+pgap);
  rect(x,ppy,pw,pph,C.card,10,C.cardLn); rect(x,ppy,pw,0.08,p[2],0);
  oval(x+0.26,ppy+0.3,0.66,0.66,p[2]); txt(x+0.26,ppy+0.3,0.66,0.66,"●",14,C.bg,{align:'center'});
  txt(x+0.26,ppy+1.06,pw-0.5,0.34,p[0],14.5,C.white,{bold:true,face:'Trebuchet MS'});
  txt(x+0.26,ppy+1.42,pw-0.5,0.58,wrap(p[1],30),10.5,C.muted,{top:true});
});

// roadmap
txt(0.5,4.74,6,0.3,"Горизонты развития",13.5,C.white,{bold:true,face:'Trebuchet MS'});
const horizons=[["1","Сейчас · пилот запущен","Мониторинг и реагирование","Сбор сигналов, AI-фильтр, адресные поручения управлениям.",C.green],
 ["2","6–12 месяцев","Предиктивная аналитика","Раннее предупреждение всплесков, прогноз напряжённости по районам.",C.sky],
 ["3","Перспектива","Единое окно управления","От сигнала до решения в одном контуре с городскими службами.",C.indigo]];
const hw=3.93,hgap=0.22,hyy=5.1,hh=1.42;
horizons.forEach((hz,i)=>{const x=0.5+i*(hw+hgap);
  rect(x,hyy,hw,hh,C.card,10,C.cardLn);
  oval(x+0.24,hyy+0.24,0.5,0.5,hz[4]); txt(x+0.24,hyy+0.24,0.5,0.5,hz[0],17,C.bg,{align:'center',bold:true});
  txt(x+0.88,hyy+0.2,hw-1.1,0.26,hz[1],9.5,hz[4],{bold:true});
  txt(x+0.88,hyy+0.44,hw-1.1,0.32,hz[2],13.5,C.white,{bold:true,face:'Trebuchet MS'});
  txt(x+0.24,hyy+0.84,hw-0.46,0.5,wrap(hz[3],46),10,C.muted,{top:true});
  if(i<2) txt(x+hw-0.02,hyy,hgap+0.04,hh,"›",24,C.ink3,{align:'center',bold:true});
});

// footer
txt(0.5,6.74,9.0,0.5,"Алматы — город, который слышит горожан и действует на опережение",13,C.white,{bold:true});
txt(9.83,6.74,3.0,0.5,"public-jade-one-29.vercel.app",12,C.sky,{align:'right',bold:true});

const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${el.join('')}</svg>`;
sharp(Buffer.from(svg)).png().toFile("preview.png").then(()=>console.log("preview.png written"));
