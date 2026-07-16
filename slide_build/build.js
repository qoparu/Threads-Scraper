const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa6 = require("react-icons/fa6");

const C = {
  bg:"0F1B34", bg2:"16244A", card:"1B2A4E", cardLn:"2C3E6B",
  white:"FFFFFF", muted:"9FB0D0", ink3:"6E80A6",
  indigo:"6366F1", sky:"38BDF8", teal:"2DD4BF", rose:"FB5577", green:"34D399", amber:"FBBF24",
};

async function iconPng(IconComponent, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(IconComponent, { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
async function makeBackground(w, h) {
  const W = Math.round(w * 96), H = Math.round(h * 96);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}">
    <defs>
      <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#0F1B34"/><stop offset="0.55" stop-color="#13203F"/><stop offset="1" stop-color="#1A2A52"/></linearGradient>
      <radialGradient id="r1" cx="0.85" cy="0.05" r="0.5"><stop offset="0" stop-color="#4F46E5" stop-opacity="0.40"/><stop offset="1" stop-color="#4F46E5" stop-opacity="0"/></radialGradient>
      <radialGradient id="r2" cx="0.05" cy="0.95" r="0.55"><stop offset="0" stop-color="#0EA5E9" stop-opacity="0.26"/><stop offset="1" stop-color="#0EA5E9" stop-opacity="0"/></radialGradient>
    </defs>
    <rect width="${W}" height="${H}" fill="url(#g)"/><rect width="${W}" height="${H}" fill="url(#r1)"/><rect width="${W}" height="${H}" fill="url(#r2)"/></svg>`;
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.defineLayout({ name: "WIDE", width: 13.333, height: 7.5 });
  pres.layout = "WIDE";
  pres.author = "Акимат г. Алматы";
  pres.title = "Стратегия: data-driven управление городом";

  const s = pres.addSlide();
  s.background = { data: await makeBackground(13.333, 7.5) };
  const HEAD = "Trebuchet MS", BODY = "Calibri";
  const shadow = () => ({ type: "outer", color: "000000", blur: 9, offset: 3, angle: 90, opacity: 0.28 });

  const icCrest = await iconPng(fa6.FaLandmarkDome, "#FFFFFF");
  const icBroadcast = await iconPng(fa6.FaTowerBroadcast, "#FFFFFF");
  const icChip = await iconPng(fa6.FaMicrochip, "#FFFFFF");
  const icList = await iconPng(fa6.FaListCheck, "#FFFFFF");
  const icBolt = await iconPng(fa6.FaBolt, "#FFFFFF");
  const icQuote = await iconPng(fa6.FaQuoteLeft, "#38BDF8");

  // ===== HEADER =====
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 0.4, w: 0.76, h: 0.76, rectRadius: 0.14, fill: { color: C.indigo }, line: { type: "none" }, shadow: shadow() });
  s.addImage({ data: icCrest, x: 0.66, y: 0.56, w: 0.44, h: 0.44 });
  s.addText("Data-driven управление городом", { x: 1.4, y: 0.36, w: 9.2, h: 0.55, margin: 0, fontFace: HEAD, fontSize: 27, bold: true, color: C.white, valign: "middle" });
  s.addText([
    { text: "Социальные сигналы горожан как инструмент управления · ", options: { color: C.muted } },
    { text: "Акимат г. Алматы", options: { color: C.sky, bold: true } },
  ], { x: 1.42, y: 0.9, w: 9.2, h: 0.32, margin: 0, fontFace: BODY, fontSize: 13.5, valign: "middle" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 10.62, y: 0.45, w: 2.21, h: 0.66, rectRadius: 0.1, fill: { color: C.card }, line: { color: C.cardLn, width: 1 } });
  s.addText("Стратегическая инициатива", { x: 10.62, y: 0.45, w: 2.21, h: 0.66, margin: 0, fontFace: BODY, fontSize: 10.5, bold: true, color: C.sky, align: "center", valign: "middle" });

  // ===== VISION BAND =====
  const vy = 1.36, vh = 0.94;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: vy, w: 12.33, h: vh, rectRadius: 0.1, fill: { color: C.card }, line: { color: C.cardLn, width: 1 }, shadow: shadow() });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: vy, w: 0.08, h: vh, fill: { color: C.sky }, line: { type: "none" } });
  s.addImage({ data: icQuote, x: 0.78, y: vy + 0.24, w: 0.4, h: 0.4 });
  s.addText("Управлять городом на основе данных, а не предположений.", { x: 1.4, y: vy + 0.12, w: 11.2, h: 0.4, margin: 0, fontFace: HEAD, fontSize: 18, bold: true, color: C.white, valign: "middle" });
  s.addText([
    { text: "Непрерывно слышим голос горожан в соцсетях и переходим ", options: { color: C.muted } },
    { text: "от реакции на жалобы — к упреждению проблем", options: { color: C.teal, bold: true } },
    { text: ".", options: { color: C.muted } },
  ], { x: 1.4, y: vy + 0.5, w: 11.2, h: 0.34, margin: 0, fontFace: BODY, fontSize: 13, valign: "middle" });

  // ===== 4 STRATEGIC PILLARS =====
  const pillars = [
    { ic: icBroadcast, col: C.sky,    t: "Слышим город 24/7", d: "Непрерывный сбор сигналов из Threads, Facebook и Instagram. Город на связи круглосуточно." },
    { ic: icChip,      col: C.indigo, t: "Суверенный AI",      d: "Локальная модель Qwen фильтрует и проверяет посты. Данные не уходят в облако." },
    { ic: icList,      col: C.teal,   t: "От шума — к задачам", d: "Приоритизация по срочности и адресные поручения профильным управлениям." },
    { ic: icBolt,      col: C.amber,  t: "Проактивность",       d: "Действуем до эскалации, а не по факту кризиса. Ответ — раньше негатива." },
  ];
  const pw = 2.95, pgap = 0.143, ppy = 2.5, pph = 2.06;
  pillars.forEach((p, i) => {
    const x = 0.5 + i * (pw + pgap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: ppy, w: pw, h: pph, rectRadius: 0.1, fill: { color: C.card }, line: { color: C.cardLn, width: 1 }, shadow: shadow() });
    s.addShape(pres.shapes.RECTANGLE, { x, y: ppy, w: pw, h: 0.08, fill: { color: p.col }, line: { type: "none" } });
    s.addShape(pres.shapes.OVAL, { x: x + 0.26, y: ppy + 0.3, w: 0.66, h: 0.66, fill: { color: p.col }, line: { type: "none" } });
    s.addImage({ data: p.ic, x: x + 0.42, y: ppy + 0.46, w: 0.34, h: 0.34 });
    s.addText(p.t, { x: x + 0.26, y: ppy + 1.06, w: pw - 0.5, h: 0.34, margin: 0, fontFace: HEAD, fontSize: 14.5, bold: true, color: C.white, valign: "middle" });
    s.addText(p.d, { x: x + 0.26, y: ppy + 1.42, w: pw - 0.5, h: 0.58, margin: 0, fontFace: BODY, fontSize: 10.5, color: C.muted, valign: "top", lineSpacingMultiple: 1.0 });
  });

  // ===== ROADMAP — 3 HORIZONS =====
  s.addText("Горизонты развития", { x: 0.5, y: 4.74, w: 6, h: 0.3, margin: 0, fontFace: HEAD, fontSize: 13.5, bold: true, color: C.white });
  const horizons = [
    { n: "1", tag: "Сейчас · пилот запущен", col: C.green, t: "Мониторинг и реагирование", d: "Сбор сигналов, AI-фильтр, адресные поручения управлениям." },
    { n: "2", tag: "6–12 месяцев", col: C.sky, t: "Предиктивная аналитика", d: "Раннее предупреждение всплесков, прогноз напряжённости по районам." },
    { n: "3", tag: "Перспектива", col: C.indigo, t: "Единое окно управления", d: "От сигнала до решения в одном контуре с городскими службами." },
  ];
  const hw = 3.93, hgap = 0.22, hyy = 5.1, hh = 1.42;
  horizons.forEach((hz, i) => {
    const x = 0.5 + i * (hw + hgap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: hyy, w: hw, h: hh, rectRadius: 0.1, fill: { color: C.card }, line: { color: C.cardLn, width: 1 }, shadow: shadow() });
    s.addShape(pres.shapes.OVAL, { x: x + 0.24, y: hyy + 0.24, w: 0.5, h: 0.5, fill: { color: hz.col }, line: { type: "none" } });
    s.addText(hz.n, { x: x + 0.24, y: hyy + 0.24, w: 0.5, h: 0.5, margin: 0, fontFace: HEAD, fontSize: 17, bold: true, color: C.bg, align: "center", valign: "middle" });
    s.addText(hz.tag, { x: x + 0.88, y: hyy + 0.2, w: hw - 1.1, h: 0.26, margin: 0, fontFace: BODY, fontSize: 9.5, bold: true, color: hz.col, valign: "middle" });
    s.addText(hz.t, { x: x + 0.88, y: hyy + 0.44, w: hw - 1.1, h: 0.32, margin: 0, fontFace: HEAD, fontSize: 13.5, bold: true, color: C.white, valign: "middle" });
    s.addText(hz.d, { x: x + 0.24, y: hyy + 0.84, w: hw - 0.46, h: 0.5, margin: 0, fontFace: BODY, fontSize: 10, color: C.muted, valign: "top" });
    if (i < 2) s.addText("›", { x: x + hw - 0.02, y: hyy, w: hgap + 0.04, h: hh, margin: 0, fontFace: HEAD, fontSize: 24, bold: true, color: C.ink3, align: "center", valign: "middle" });
  });

  // ===== FOOTER tagline =====
  s.addText([
    { text: "Алматы — город, который ", options: { color: C.muted } },
    { text: "слышит горожан и действует на опережение", options: { color: C.white, bold: true } },
  ], { x: 0.5, y: 6.74, w: 9.0, h: 0.5, margin: 0, fontFace: BODY, fontSize: 13, valign: "middle" });
  s.addText("public-jade-one-29.vercel.app", { x: 9.83, y: 6.74, w: 3.0, h: 0.5, margin: 0, fontFace: BODY, fontSize: 12, bold: true, color: C.sky, align: "right", valign: "middle" });

  await pres.writeFile({ fileName: "Almaty_strategy_infographic.pptx" });
  console.log("written");
})();
