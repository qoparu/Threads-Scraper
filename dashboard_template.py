# -*- coding: utf-8 -*-
"""HTML-шаблон дашборда акимата — светлый premium-gov дизайн.
/*__DATA__*/ и /*__GEO__*/ заменяются на JSON при сборке (build_dashboard.py).
Полный текст постов не обрезается: сворачивание через CSS + кнопку «Развернуть»."""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Data-driven аналитика соцсетей · Акимат Алматы</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{
 --bg:#f4f7fb;--surface:#ffffff;--ink:#1f2a44;--ink2:#5c6b86;--ink3:#95a2bb;
 --line:#e9edf6;--soft:#f1f4fa;--track:#eef1f7;
 --indigo:#6366f1;--sky:#38bdf8;--teal:#2dd4bf;--amber:#f6b756;--rose:#fb7185;--green:#34d399;
 --ind-bg:#eef0ff;--ind-bd:#e2e5ff;
 --neg-bg:#fff1f4;--neg-bd:#ffdbe3;--neg-ink:#c2415c;
 --warn-bg:#fff6e8;--warn-bd:#ffe6bd;--warn-ink:#9a6a18;
 --ok-bg:#e9fbf2;--ok-bd:#c9f0dd;--ok-ink:#129469;
 --quote-ink:#3a455c;
 --barbg:rgba(255,255,255,.78);--tabbar-bg:rgba(244,247,251,.9);
 --rank:#eef1f7;--dotbg:#cdd6e6;--mapbg:#dfe7f2;
 --glow1:rgba(99,102,241,.10);--glow2:rgba(56,189,248,.10);
 --sh:0 1px 2px rgba(20,30,60,.04),0 10px 30px rgba(20,30,60,.06);
 --sh2:0 2px 8px rgba(20,30,60,.06),0 24px 60px rgba(20,30,60,.10);
 --sans:'Inter',system-ui,sans-serif;--disp:'Manrope',var(--sans);
}
html[data-theme="dark"]{
 --bg:#0f1626;--surface:#19233b;--ink:#e8edf7;--ink2:#a7b4d0;--ink3:#74829f;
 --line:#27324d;--soft:#202c46;--track:#27324d;
 --indigo:#818cf8;--sky:#56c5f5;--teal:#2dd4bf;--amber:#f6b756;--rose:#fb7185;--green:#34d399;
 --ind-bg:rgba(129,140,248,.16);--ind-bd:rgba(129,140,248,.32);
 --neg-bg:rgba(251,113,133,.16);--neg-bd:rgba(251,113,133,.32);--neg-ink:#fda4b4;
 --warn-bg:rgba(246,183,86,.16);--warn-bd:rgba(246,183,86,.32);--warn-ink:#f6c987;
 --ok-bg:rgba(52,211,153,.15);--ok-bd:rgba(52,211,153,.3);--ok-ink:#6ee7b7;
 --quote-ink:#c4cfe6;
 --barbg:rgba(15,22,38,.72);--tabbar-bg:rgba(15,22,38,.82);
 --rank:#202c46;--dotbg:#3a4865;--mapbg:#0e1726;
 --glow1:rgba(99,102,241,.20);--glow2:rgba(56,189,248,.14);
 --sh:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.34);
 --sh2:0 2px 8px rgba(0,0,0,.34),0 24px 60px rgba(0,0,0,.45);
}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;font-family:var(--sans);color:var(--ink);font-size:15px;line-height:1.5;transition:background-color .3s,color .3s;
 background-color:var(--bg);
 background-image:radial-gradient(1200px 600px at 85% -10%,var(--glow1),transparent 60%),
  radial-gradient(900px 500px at -5% 0%,var(--glow2),transparent 55%);}
a{color:var(--indigo);text-decoration:none}
h1,h2,h3{margin:0;font-family:var(--disp);font-weight:800;letter-spacing:-.01em}
.mono{font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
/* APP BAR */
.bar{position:sticky;top:0;z-index:60;background:var(--barbg);backdrop-filter:blur(12px);
 border-bottom:1px solid var(--line)}
.bar .wrap{display:flex;align-items:center;gap:16px;height:64px}
.crest{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;font-size:20px;
 background:linear-gradient(135deg,var(--indigo),var(--sky));color:#fff;box-shadow:var(--sh)}
.brand b{font-family:var(--disp);font-size:15px;display:block;line-height:1.15}
.brand span{font-size:11.5px;color:var(--ink2)}
.gsearch{margin-left:auto;width:340px;max-width:38vw;background:var(--soft);border:1px solid var(--line);border-radius:11px;padding:9px 13px;font-size:13px;font-family:var(--sans);color:var(--ink)}
.gsearch:focus{outline:none;border-color:var(--indigo);background:var(--surface);width:420px}
.bar .clock{font-size:12.5px;color:var(--ink2);text-align:right;white-space:nowrap}
@media(max-width:760px){.gsearch{display:none}}
.bar .clock b{font-family:var(--disp);font-size:17px;color:var(--ink)}
.livedot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);margin-right:6px;
 box-shadow:0 0 0 0 rgba(22,163,74,.5);animation:pulse 1.8s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(22,163,74,.45)}70%{box-shadow:0 0 0 8px rgba(22,163,74,0)}100%{box-shadow:0 0 0 0 rgba(22,163,74,0)}}
/* HERO */
.hero{padding:34px 0 8px}
.tagline{display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:600;color:var(--indigo);
 background:var(--ind-bg);border:1px solid var(--ind-bd);padding:5px 12px;border-radius:30px}
.hero h1{font-size:34px;line-height:1.1;margin:14px 0 8px;max-width:880px}
.hero h1 .grad{background:linear-gradient(90deg,var(--indigo),var(--sky));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero .lead{color:var(--ink2);font-size:16px;max-width:820px}
.hero .lead b{color:var(--ink)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin-top:22px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:16px 18px;box-shadow:var(--sh)}
.kpi .ic{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:17px;margin-bottom:10px}
.kpi .v{font-family:var(--disp);font-size:26px;font-weight:800;line-height:1}
.kpi .l{font-size:12px;color:var(--ink2);margin-top:5px}
.kpi .s{font-size:11.5px;color:var(--ink3);margin-top:3px}
/* SECTIONS */
section{padding:30px 0 4px;scroll-margin-top:74px}
.sec-h{display:flex;align-items:center;gap:12px;margin-bottom:16px}
.sec-h .n{font-family:var(--disp);font-size:12px;font-weight:700;color:var(--indigo);background:var(--ind-bg);border-radius:8px;padding:4px 9px}
.sec-h h2{font-size:21px}.sec-h .hint{margin-left:auto;font-size:12px;color:var(--ink3)}
.grid{display:grid;gap:16px}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}
@media(max-width:880px){.g2,.g3,.g4{grid-template-columns:1fr}}
.card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:var(--sh);position:relative}
.card h3{font-size:16px;margin-bottom:6px}
.muted{color:var(--ink2)}.tiny{font-size:11.5px;color:var(--ink3)}
.lead-num{font-family:var(--disp);font-size:30px;font-weight:800}
.accentbar{position:absolute;left:0;top:18px;bottom:18px;width:4px;border-radius:4px}
.rank{position:absolute;top:14px;right:18px;font-family:var(--disp);font-size:30px;font-weight:800;color:var(--track)}
.pill{display:inline-flex;align-items:center;font-size:11.5px;font-weight:600;padding:3px 10px;border-radius:30px;border:1px solid var(--line);color:var(--ink2);background:var(--soft);margin:2px 4px 2px 0;white-space:nowrap}
.pill.neg{color:var(--neg-ink);background:var(--neg-bg);border-color:var(--neg-bd)}
.pill.warn{color:var(--warn-ink);background:var(--warn-bg);border-color:var(--warn-bd)}
.pill.ok{color:var(--ok-ink);background:var(--ok-bg);border-color:var(--ok-bd)}
.pill.ind{color:var(--indigo);background:var(--ind-bg);border-color:var(--ind-bd)}
.bar7{height:8px;border-radius:8px;background:var(--track);overflow:hidden;margin:8px 0}
.bar7>i{display:block;height:100%;border-radius:8px;background:linear-gradient(90deg,var(--indigo),var(--sky))}
.bar7.neg>i{background:linear-gradient(90deg,#fb7185,var(--rose))}
.spark{display:inline-flex;align-items:flex-end;gap:2px;height:26px;vertical-align:middle}
.spark i{width:5px;background:var(--sky);border-radius:2px;opacity:.85}
.quote{background:var(--soft);border-left:3px solid var(--indigo);border-radius:0 10px 10px 0;padding:11px 14px;margin:10px 0;font-size:14px;color:var(--quote-ink)}
.quote.neg{border-left-color:var(--rose)}
.quote .ptext::before{content:'«'}
.quote .ptext::after{content:'»'}
.cf{display:flex;gap:10px;background:var(--warn-bg);border:1px solid var(--warn-bd);border-radius:12px;padding:11px 14px;margin:10px 0;font-size:13.5px;color:var(--warn-ink)}
.cf b{color:var(--warn-ink)}
/* раскрываемый текст поста (НЕ обрезаем данные) */
.ptext{font-size:14px;color:var(--quote-ink);white-space:pre-wrap;word-break:break-word}
.ptext.clamp{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}
.morebtn{font-size:12px;font-weight:600;color:var(--indigo);cursor:pointer;background:none;border:none;padding:4px 0;margin-top:4px}
.sevtag{font-family:var(--disp);font-weight:800;font-size:11px;padding:2px 8px;border-radius:7px}
.s5,.s4{background:var(--neg-bg);color:var(--neg-ink)}.s3{background:var(--warn-bg);color:var(--warn-ink)}.s2,.s1{background:var(--ok-bg);color:var(--ok-ink)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:11.5px;color:var(--ink3);text-transform:uppercase;letter-spacing:.5px;font-weight:600;cursor:pointer;position:sticky;top:0;background:var(--surface)}
tbody tr:hover{background:var(--soft)}
.toolbar{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:14px}
.toolbar input,.toolbar select{background:var(--surface);border:1px solid var(--line);color:var(--ink);border-radius:11px;padding:9px 13px;font-size:13.5px;font-family:var(--sans)}
.toolbar input{flex:1;min-width:220px}
.btn{font-size:12.5px;font-weight:600;background:var(--soft);border:1px solid var(--line);color:var(--ink2);border-radius:10px;padding:7px 13px;cursor:pointer}
.btn:hover{border-color:var(--indigo);color:var(--indigo)}
#map{height:440px;border-radius:14px;overflow:hidden}.leaflet-container{background:var(--mapbg);font-family:var(--sans)}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--ink2);margin-top:8px}.legend i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:5px;vertical-align:middle}
.stack{display:flex;height:18px;border-radius:6px;overflow:hidden;margin:5px 0}.stack i{display:block;height:100%}
.bubble{cursor:pointer;transition:.15s}.bubble:hover{filter:brightness(.92)}
details.method{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:6px 18px;box-shadow:var(--sh)}
details.method summary{cursor:pointer;font-weight:600;color:var(--ink);padding:12px 0}
.fade{opacity:0;transform:translateY(12px);transition:.5s}.fade.in{opacity:1;transform:none}
.toc{position:fixed;right:18px;top:50%;transform:translateY(-50%);z-index:40;display:flex;flex-direction:column;gap:7px}
.toc a{width:9px;height:9px;border-radius:50%;background:var(--dotbg);transition:.2s}.toc a:hover,.toc a.act{background:var(--indigo);transform:scale(1.3)}
@media(max-width:1100px){.toc{display:none}}
.foot{color:var(--ink3);font-size:12.5px;text-align:center;padding:30px 0;border-top:1px solid var(--line);margin-top:24px}
svg text{font-family:var(--sans)}
/* Фидбек по постам (обучение ИИ-фильтра) */
.fb-btns{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px}
.fb-note{font-size:11.5px;color:var(--ink3)}
.fb-btn{font-size:12px;font-weight:600;border-radius:9px;border:1px solid var(--line);background:var(--soft);color:var(--ink2);padding:5px 11px;cursor:pointer}
.fb-btn:hover{border-color:var(--indigo);color:var(--indigo)}
.fb-btn.up.voted{background:var(--ok-bg);border-color:var(--green);color:var(--ok-ink)}
.fb-btn.down.voted{background:var(--neg-bg);border-color:var(--rose);color:var(--neg-ink)}
.fb-btn[disabled]{cursor:default;opacity:.5}
/* Статус сбора данных 24/7 (подвал) */
.statusdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px;vertical-align:middle}
.statusdot.on{background:var(--green);box-shadow:0 0 0 0 rgba(22,163,74,.5);animation:pulse 1.8s infinite}
.statusdot.off{background:var(--ink3)}
.term-box{background:#0f1b2e;color:#7dd3fc;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;line-height:1.5;border-radius:10px;padding:10px 12px;max-height:160px;overflow-y:auto;white-space:pre-wrap;word-break:break-all}
.scraper-runs{display:flex;flex-direction:column;gap:4px;font-size:12px}
.scraper-runs .row{display:flex;justify-content:space-between;gap:10px;border-bottom:1px dashed var(--line);padding-bottom:3px}
.quiet-card{background:var(--soft);border-style:dashed}
/* Вкладки-страницы */
.tabbar-wrap{position:sticky;top:64px;z-index:55;background:var(--tabbar-bg);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.tabbar{display:flex;gap:8px;overflow-x:auto;padding:12px 0;scrollbar-width:thin}
.tab{font-family:var(--disp);font-size:13px;font-weight:700;color:var(--ink2);background:var(--surface);border:1px solid var(--line);
 border-radius:30px;padding:9px 18px;cursor:pointer;white-space:nowrap;transition:.15s;box-shadow:var(--sh)}
.tab:hover{border-color:var(--indigo);color:var(--indigo)}
.tab.active{background:linear-gradient(135deg,var(--indigo),var(--sky));color:#fff;border-color:transparent}
.page{display:none}
.page.active{display:block}
/* Слайдер постов (Сигналы тревоги) */
.slider{position:relative}
.sl-viewport{overflow:hidden;border-radius:12px}
.sl-track{display:flex;transition:transform .35s cubic-bezier(.4,0,.2,1)}
.sl-slide{flex:0 0 100%;min-width:100%;padding:2px}
.sl-nav{display:flex;align-items:center;gap:10px;margin-top:10px}
.sl-arrow{width:34px;height:34px;flex:none;border-radius:50%;border:1px solid var(--line);background:var(--surface);
 color:var(--ink2);font-size:18px;line-height:1;cursor:pointer;display:grid;place-items:center;box-shadow:var(--sh)}
.sl-arrow:hover:not([disabled]){border-color:var(--rose);color:var(--rose)}
.sl-arrow[disabled]{opacity:.35;cursor:default}
.sl-count{font-size:12px;font-weight:700;color:var(--ink2);font-variant-numeric:tabular-nums}
.sl-dots{display:flex;gap:6px;margin-left:auto;flex-wrap:wrap}
.sl-dot{width:7px;height:7px;border-radius:50%;background:var(--dotbg);cursor:pointer;transition:.2s;border:none;padding:0}
.sl-dot.act{background:var(--rose);transform:scale(1.3)}
/* фильтр по датам (топ-посты) */
.datefilter{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:14px}
.df-btn{font-size:12.5px;font-weight:600;border-radius:30px;border:1px solid var(--line);background:var(--surface);
 color:var(--ink2);padding:7px 15px;cursor:pointer;transition:.15s}
.df-btn:hover{border-color:var(--indigo);color:var(--indigo)}
.df-btn.act{background:linear-gradient(135deg,var(--indigo),var(--sky));color:#fff;border-color:transparent}
/* персональная рекомендация под пост */
.reco{display:flex;gap:8px;margin-top:10px;background:var(--ok-bg);border:1px solid var(--ok-bd);border-left:3px solid var(--green);
 border-radius:0 10px 10px 0;padding:10px 13px;font-size:13px;color:var(--ok-ink)}
.reco .reco-ic{color:var(--green);font-weight:800}
.reco b{color:var(--ok-ink)}
/* цветной фон блоков по смыслу */
section{border-radius:20px;transition:background .3s}
section.tint-rose{background:linear-gradient(180deg,rgba(225,29,72,.07),rgba(225,29,72,.015) 260px,transparent 420px)}
section.tint-green{background:linear-gradient(180deg,rgba(22,163,74,.08),rgba(22,163,74,.015) 260px,transparent 420px)}
section.tint-amber{background:linear-gradient(180deg,rgba(245,158,11,.09),rgba(245,158,11,.02) 260px,transparent 420px)}
section.tint-indigo{background:linear-gradient(180deg,rgba(79,70,229,.07),rgba(79,70,229,.015) 260px,transparent 420px)}
section.tint-rose,section.tint-green,section.tint-amber,section.tint-indigo{padding-left:18px;padding-right:18px;margin-left:-18px;margin-right:-18px;width:calc(100% + 36px)}
/* большой смысловой эмодзи-водяной знак на фоне блока */
section[data-emoji]{position:relative;overflow:hidden}
section[data-emoji]::before{content:attr(data-emoji);position:absolute;top:4px;right:16px;font-size:155px;line-height:1;
 opacity:.07;pointer-events:none;z-index:0;filter:saturate(1.1)}
section[data-emoji]::after{content:attr(data-emoji);position:absolute;bottom:-26px;left:8px;font-size:90px;line-height:1;
 opacity:.045;pointer-events:none;z-index:0;transform:rotate(-12deg)}
section[data-emoji] > *{position:relative;z-index:1}
@media(max-width:680px){section[data-emoji]::before{font-size:96px}section[data-emoji]::after{display:none}}
/* Поп-ап «Проактивное управление» */
.modal-bg{position:fixed;inset:0;z-index:200;background:rgba(15,27,52,.55);backdrop-filter:blur(4px);
 display:flex;align-items:center;justify-content:center;padding:24px;opacity:0;visibility:hidden;transition:opacity .35s}
.modal-bg.show{opacity:1;visibility:visible}
.modal{background:var(--surface);border-radius:22px;max-width:680px;width:100%;max-height:86vh;overflow-y:auto;
 box-shadow:var(--sh2);transform:translateY(20px) scale(.96);transition:transform .45s cubic-bezier(.34,1.3,.5,1)}
.modal-bg.show .modal{transform:none}
.modal-top{position:sticky;top:0;background:linear-gradient(135deg,var(--rose),#fb7185);color:#fff;padding:22px 24px;border-radius:22px 22px 0 0}
.modal-top .mt-tag{font-size:11.5px;font-weight:800;letter-spacing:.6px;text-transform:uppercase;opacity:.9}
.modal-top h2{color:#fff;font-size:23px;margin-top:5px}
.modal-top p{margin:7px 0 0;font-size:13.5px;opacity:.95}
.modal-x{position:absolute;top:16px;right:18px;width:32px;height:32px;border:none;border-radius:50%;
 background:rgba(255,255,255,.2);color:#fff;font-size:16px;cursor:pointer;line-height:1}
.modal-x:hover{background:rgba(255,255,255,.34)}
.modal-body{padding:18px 24px 8px}
.pm-item{display:flex;gap:12px;padding:13px 0;border-bottom:1px solid var(--line)}
.pm-item:last-child{border-bottom:none}
.pm-rank{flex:none;width:30px;height:30px;border-radius:9px;display:grid;place-items:center;font-family:var(--disp);font-weight:800;background:var(--neg-bg);color:var(--neg-ink)}
.pm-body h4{margin:0;font-size:15px;font-family:var(--disp)}
.pm-meta{font-size:12px;color:var(--ink3);margin:3px 0 6px}
.pm-reco{font-size:13px;color:var(--ok-ink);background:var(--ok-bg);border:1px solid var(--ok-bd);border-radius:9px;padding:8px 11px}
.modal-foot{position:sticky;bottom:0;background:var(--surface);padding:14px 24px 20px;display:flex;gap:10px;flex-wrap:wrap;border-top:1px solid var(--line)}
.modal-foot .btn-primary{background:linear-gradient(135deg,var(--indigo),var(--sky));color:#fff;border:none;font-weight:700;font-size:13px;padding:11px 18px;border-radius:11px;cursor:pointer}
.modal-foot .btn-ghost{background:var(--soft);border:1px solid var(--line);color:var(--ink2);font-weight:600;font-size:13px;padding:11px 18px;border-radius:11px;cursor:pointer}
.pm-fab{position:fixed;left:18px;bottom:18px;z-index:90;background:linear-gradient(135deg,var(--rose),#fb7185);color:#fff;
 border:none;border-radius:30px;padding:11px 16px;font-weight:700;font-size:13px;cursor:pointer;box-shadow:var(--sh2);display:flex;align-items:center;gap:7px}
.pm-fab:hover{filter:brightness(1.06)}
@media(max-width:560px){.pm-fab span{display:none}}
/* Переключатель темы + полировка под прохладно-нейтральный стиль */
.themebtn{width:38px;height:38px;border-radius:11px;border:1px solid var(--line);background:var(--surface);color:var(--ink2);
 font-size:17px;cursor:pointer;display:grid;place-items:center;box-shadow:var(--sh);transition:.15s}
.themebtn:hover{border-color:var(--indigo);color:var(--indigo)}
.card,.kpi{border-radius:20px}
.sec-h h2{font-weight:700}
.tabbar{justify-content:center}
@media(max-width:760px){.tabbar{justify-content:flex-start}}
html[data-theme="dark"] section.tint-rose{background:linear-gradient(180deg,rgba(251,113,133,.12),rgba(251,113,133,.03) 260px,transparent 420px)}
html[data-theme="dark"] section.tint-green{background:linear-gradient(180deg,rgba(52,211,153,.12),rgba(52,211,153,.03) 260px,transparent 420px)}
html[data-theme="dark"] section.tint-amber{background:linear-gradient(180deg,rgba(246,183,86,.12),rgba(246,183,86,.03) 260px,transparent 420px)}
html[data-theme="dark"] section.tint-indigo{background:linear-gradient(180deg,rgba(129,140,248,.12),rgba(129,140,248,.03) 260px,transparent 420px)}
html[data-theme="dark"] section[data-emoji]::before{opacity:.10}
html[data-theme="dark"] .kpi .ic{background:var(--soft)!important}
html[data-theme="dark"] .gsearch:focus{background:var(--surface)}
/* ===== BioSync-стиль: тёмные панели данных + светлые карточки ===== */
.hero-top{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px}
.hero-h{font-size:25px;line-height:1.15;margin:6px 0 4px}
.cc-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:10px}
@media(max-width:880px){.cc-grid{grid-template-columns:1fr}}
.dpanel{background:#2a3242;color:#fff;border-radius:20px;padding:20px;position:relative;overflow:hidden;box-shadow:var(--sh2)}
.dpanel h3{color:#fff;font-size:15px;margin:0 0 14px}
.datechip{position:absolute;top:18px;right:18px;font-size:10.5px;font-weight:600;color:#cdd6e6;background:#20283a;border:1px solid #3a4459;border-radius:20px;padding:5px 11px}
.heatrow{display:flex;align-items:center;gap:10px;margin:9px 0}
.heatrow .nm{width:128px;font-size:12.5px;color:#cdd6e6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.heatrow .ht{flex:1;height:9px;border-radius:6px;background:#212a3c;overflow:hidden}
.heatrow .ht>i{display:block;height:100%;border-radius:6px}
.heatrow .hv{font-size:11.5px;color:#aab3c5;width:40px;text-align:right;font-variant-numeric:tabular-nums}
.dpanel .dlink{display:inline-block;margin-top:12px;font-size:12px;font-weight:600;color:#7dd3fc;cursor:pointer}
.riskrow{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.riskcard{background:#212a3c;border:1px solid #3a4459;border-radius:14px;padding:13px}
.riskcard .rt{font-size:12.5px;font-weight:600;color:#fff}
.riskcard .rs{font-size:10px;color:#8a97ad;margin:2px 0 7px}
.riskcard .rv{font-family:var(--disp);font-size:20px;font-weight:800;color:#fff}
.riskbar{height:7px;border-radius:5px;background:#323c52;overflow:hidden;margin-top:8px}
.riskbar>i{display:block;height:100%;border-radius:5px;background:linear-gradient(90deg,#22c55e,#eab308 55%,#ef4444)}
.gauge-wrap{display:flex;justify-content:center;margin-top:8px}
.bk{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin-top:16px}
.bcard{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px 18px;box-shadow:var(--sh)}
.bcard .bh{display:flex;align-items:center;gap:8px;margin-bottom:8px}
.bcard .bh .bl{font-size:12px;color:var(--ink3);font-weight:600}
.bcard .bv{font-family:var(--disp);font-size:26px;font-weight:800;line-height:1}
.stag{margin-left:auto;display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:600;color:var(--ink2);background:var(--soft);border:1px solid var(--line);border-radius:20px;padding:3px 9px}
.stag i{width:6px;height:6px;border-radius:50%}
.cmp{margin-top:6px}
.cmp .crow{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--ink3);margin:6px 0}
.cmp .crow .ct{width:56px}
.cmp .crow .cb{flex:1;height:8px;border-radius:5px;background:var(--track);overflow:hidden}
.cmp .crow .cb>i{display:block;height:100%;border-radius:5px}
.cmp .crow .cn{width:46px;text-align:right;color:var(--ink2);font-variant-numeric:tabular-nums}
.plats{display:flex;gap:8px;flex-wrap:wrap}
.platchip{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;font-weight:600;color:var(--ink2);background:var(--surface);border:1px solid var(--line);border-radius:20px;padding:6px 12px;box-shadow:var(--sh)}
.platchip svg{width:15px;height:15px;display:block;flex:none}
.picon{width:21px;height:21px;display:inline-flex;flex:none}.picon svg{width:100%;height:100%}
.platchip b{color:var(--ink);font-family:var(--disp)}
.nsteps{display:flex;flex-direction:column;margin-top:6px}
.nstep{display:grid;grid-template-columns:36px 1fr;gap:12px;padding:13px 0;border-bottom:1px solid var(--line)}
.nstep:last-child{border-bottom:none}
.nstep .nic{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;background:var(--soft);border:1px solid var(--line);font-size:16px}
.nstep .nh{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}
.nstep .nh b{font-family:var(--disp);font-size:14px}
.nstep .ntag{font-size:10.5px;font-weight:600;color:var(--ink2);background:var(--soft);border:1px solid var(--line);border-radius:20px;padding:2px 9px}
.nstep ul{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:5px}
.nstep li{font-size:12.5px;color:var(--ink2);display:flex;gap:8px}
.nstep li::before{content:'';flex:none;width:5px;height:5px;border-radius:50%;background:var(--ink3);margin-top:7px}
.cv-list{margin:6px 0 0;padding:0;list-style:none;display:flex;flex-direction:column;gap:5px}
.cv-list li{font-size:13px;color:var(--ink2);display:flex;gap:8px}
.cv-list li::before{content:'▸';color:var(--green);flex:none;font-weight:800}
.voicebox{margin-top:10px;background:var(--soft);border:1px solid var(--line);border-left:3px solid var(--green);border-radius:0 10px 10px 0;padding:10px 12px}
.topsol{margin:8px 0 0;padding-left:22px;display:flex;flex-direction:column;gap:10px}
.topsol li{font-size:13.5px;color:var(--ink)}
.topsol li b{font-family:var(--disp)}
.topsol li::marker{color:var(--green);font-weight:800}
/* ===== App-shell с сайдбаром (CHRONYX-стиль) ===== */
.app{display:flex;min-height:100vh}
.sidebar{position:sticky;top:0;height:100vh;width:222px;flex:none;background:var(--surface);border-right:1px solid var(--line);display:flex;flex-direction:column;padding:18px 14px;z-index:70;overflow-y:auto}
.sb-logo{display:flex;align-items:center;gap:10px;font-family:var(--disp);font-weight:800;font-size:18px;padding:6px 8px 16px}
.sb-logo .crest{width:32px;height:32px;border-radius:9px;display:grid;place-items:center;font-size:16px;background:linear-gradient(135deg,var(--indigo),var(--sky));color:#fff}
.viewtog{display:flex;gap:4px;background:var(--soft);border:1px solid var(--line);border-radius:11px;padding:4px;margin:2px 4px 6px}
.viewtog .vt{flex:1;text-align:center;font-size:12.5px;font-weight:700;color:var(--ink2);padding:7px 6px;border-radius:8px;white-space:nowrap;transition:.15s}
.viewtog .vt:hover{color:var(--indigo)}
.viewtog .vt.active{background:var(--surface);color:var(--indigo);box-shadow:var(--sh)}
.sb-scope{font-size:11px;color:var(--ink3);padding:0 10px 10px;line-height:1.35}
.sb-nav{display:flex;flex-direction:column;gap:3px}
.sb-item{display:flex;align-items:center;gap:11px;padding:10px 12px;border-radius:11px;font-size:14px;font-weight:600;color:var(--ink2);background:none;border:none;cursor:pointer;text-align:left;width:100%;font-family:var(--sans)}
.sb-item .sb-ic{width:18px;text-align:center;font-size:15px;flex:none}
.sb-item:hover{background:var(--soft);color:var(--ink)}
.sb-item.active{background:var(--ind-bg);color:var(--indigo)}
.sb-bottom{margin-top:auto;padding-top:14px;border-top:1px solid var(--line);display:flex;flex-direction:column;gap:3px}
.sb-toggle{display:none;position:fixed;top:12px;left:12px;z-index:80;width:40px;height:40px;border-radius:11px;border:1px solid var(--line);background:var(--surface);color:var(--ink);font-size:18px;cursor:pointer;box-shadow:var(--sh)}
.content{flex:1;min-width:0;padding:0 26px 40px}
.topbar{position:sticky;top:0;z-index:50;background:var(--barbg);backdrop-filter:blur(12px);display:flex;align-items:center;gap:16px;padding:11px 0;margin-bottom:10px;border-bottom:1px solid var(--line)}
.topstrip{display:flex;flex:1;overflow-x:auto;scrollbar-width:none}
.topstrip::-webkit-scrollbar{display:none}
.topstrip .ts{padding:0 17px;border-right:1px solid var(--line);white-space:nowrap}
.topstrip .ts:first-child{padding-left:0}.topstrip .ts:last-child{border-right:none}
.topstrip .ts .tl{font-size:10.5px;color:var(--ink3)}
.topstrip .ts .tv{font-family:var(--disp);font-size:16px;font-weight:800;color:var(--ink);line-height:1.1}
.topbar .gsearch{margin:0;width:230px;max-width:26vw}
.topbar .clock{font-size:12px;color:var(--ink2);text-align:right;white-space:nowrap}
.ov-grid{display:grid;grid-template-columns:1fr 372px;gap:18px;align-items:start}
@media(max-width:1080px){.ov-grid{grid-template-columns:1fr}}
.ov-head{display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.ov-head h2{font-size:22px}
.ov-rail{display:flex;flex-direction:column;gap:16px;position:sticky;top:74px}
.ov-mapcard #rmap{height:232px;border-radius:12px;overflow:hidden;margin-top:6px}
.ov-index{display:flex;align-items:center;justify-content:space-between;margin-top:10px;font-size:12.5px;color:var(--ink3)}
.ov-index b{font-family:var(--disp);font-size:16px;color:var(--rose)}
@media(max-width:760px){.sidebar{position:fixed;left:0;top:0;transform:translateX(-100%);transition:.25s;box-shadow:var(--sh2)}.sidebar.open{transform:none}.sb-toggle{display:grid;place-items:center}.content{padding:56px 14px 40px}.topbar .gsearch{display:none}}
/* ===== Обзор месяца: игровая карта районов + ИИ-сводка ===== */
.mr-hud{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.mr-chip{display:flex;align-items:center;gap:9px;background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:9px 15px;box-shadow:var(--sh);font-size:12px;color:var(--ink2)}
.mr-chip .ic{font-size:18px}.mr-chip b{font-family:var(--disp);font-size:17px;color:var(--ink)}
.mr-grid{display:grid;grid-template-columns:1.55fr 1fr;gap:16px;align-items:start}
@media(max-width:1080px){.mr-grid{grid-template-columns:1fr}}
#mrmap{height:480px;border-radius:14px;overflow:hidden;margin-top:8px}
.mr-pin{width:46px;height:46px;border-radius:50%;display:grid;place-items:center;font-size:22px;background:var(--surface);border:2px solid var(--indigo);box-shadow:0 4px 14px rgba(79,70,229,.35);position:relative;cursor:pointer;transition:transform .15s;animation:mrdrop .55s cubic-bezier(.2,.9,.3,1.4)}
.mr-pin:hover{transform:scale(1.14)}
.mr-pin.ghost{border:2px dashed var(--dotbg);opacity:.6;box-shadow:none;font-size:17px}
.mr-cnt{position:absolute;top:-7px;right:-7px;min-width:20px;height:20px;border-radius:10px;background:linear-gradient(135deg,var(--indigo),var(--sky));color:#fff;font:800 11px/20px var(--disp);text-align:center;padding:0 5px;box-shadow:var(--sh)}
@keyframes mrdrop{0%{transform:translateY(-16px) scale(.6);opacity:0}100%{transform:none;opacity:1}}
.mr-pop{font-size:13px;max-width:250px;font-family:var(--sans)}
.mr-popq{background:var(--soft);border-radius:8px;padding:7px 9px;margin:7px 0 5px;font-size:12px;color:var(--quote-ink)}
.ai-sum{border:2px solid transparent;background:linear-gradient(var(--surface),var(--surface)) padding-box,linear-gradient(135deg,var(--indigo),var(--sky),var(--teal)) border-box}
.ai-sum p{font-size:13.5px;line-height:1.66;color:var(--quote-ink);margin:0 0 11px}
.ai-head{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.ai-badge{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;font-weight:700;color:#fff;background:linear-gradient(135deg,var(--indigo),var(--sky));border-radius:30px;padding:4px 12px}
.quest{overflow:hidden}
.quest .q-ic{width:46px;height:46px;border-radius:13px;display:grid;place-items:center;font-size:24px;background:var(--ind-bg);border:1px solid var(--ind-bd);margin-bottom:9px}
.quest .q-rank{position:absolute;top:13px;right:15px;font:800 12px var(--disp);color:var(--indigo);background:var(--ind-bg);border:1px solid var(--ind-bd);border-radius:8px;padding:3px 9px}
</style>
<script>(function(){try{var t=localStorage.getItem('theme')||(window.matchMedia&&matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');document.documentElement.dataset.theme=t;}catch(e){}})();</script>
<!-- Vercel Web Analytics (заходы, источники, гео, устройства) -->
<script>window.va=window.va||function(){(window.vaq=window.vaq||[]).push(arguments);};</script>
<script defer src="/_vercel/insights/script.js"></script>
</head>
<body>
<button class="sb-toggle" id="sbToggle" aria-label="Меню">☰</button>
<div class="app">
 <aside class="sidebar" id="sidebar">
   <div class="sb-logo"><span class="crest">🏛️</span>CityPulse</div>
   <div class="viewtog"><a class="vt" id="vt-city" href="index.html">🏙 Город</a><a class="vt" id="vt-ump" href="ump.html">🎓 Молодёжь</a></div>
   <div class="sb-scope" id="sbScope"></div>
   <nav class="sb-nav" id="sbnav"></nav>
   <div class="sb-bottom">
     <button class="sb-item" id="themeBtn" type="button"><span class="sb-ic">◐</span><span>Тема</span></button>
     <button class="sb-item" type="button" onclick="if(window.showPage)showPage('methodology')"><span class="sb-ic">⚙</span><span>Настройки</span></button>
     <button class="sb-item" type="button" onclick="if(window.showPage)showPage('methodology')"><span class="sb-ic">🛡</span><span>Методология</span></button>
   </div>
 </aside>
 <main class="content">
   <div class="topbar">
     <input id="gs" class="gsearch" placeholder="🔎 Поиск по обращениям…" autocomplete="off">
     <div class="topstrip" id="topstrip"></div>
     <div class="clock" id="clock">—</div>
   </div>
   <section class="hero" id="s1"><div id="hero"></div></section>
   <div id="app"></div>
   <div class="foot" id="foot"></div>
 </main>
</div>
<script>(function(){var b=document.getElementById('themeBtn');if(b){function sync(){var d=document.documentElement.dataset.theme==='dark';var s=b.querySelector('.sb-ic');if(s)s.textContent=d?'☀':'◐';}sync();
 b.addEventListener('click',function(){var n=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=n;try{localStorage.setItem('theme',n);}catch(e){}sync();});}
 var tg=document.getElementById('sbToggle'),sb=document.getElementById('sidebar');if(tg&&sb)tg.addEventListener('click',function(){sb.classList.toggle('open');});})();</script>
<script>
const DATA=/*__DATA__*/;const GEO=/*__GEO__*/;const VIEW=/*__VIEW__*/;
(function(){var u=VIEW==='ump';var a=document.getElementById(u?'vt-ump':'vt-city');if(a)a.classList.add('active');
 var sc=document.getElementById('sbScope');if(sc)sc.textContent=u?'Управление молодёжной политики · вузы, общежития, студенты':'Акимат г. Алматы · город целиком';
 try{document.title=(u?'Молодёжная политика':'Акимат Алматы')+' · CityPulse';}catch(e){}})();
if(DATA.posts_by_id){DATA.all_posts=(DATA.all_posts||[]).map(id=>DATA.posts_by_id[id]).filter(Boolean);DATA.feed_posts=(DATA.feed_posts||[]).map(id=>DATA.posts_by_id[id]).filter(Boolean);DATA.missing_persons=(DATA.missing_persons||[]).map(id=>DATA.posts_by_id[id]).filter(Boolean);}
const $=(t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;};
const fmt=n=>Number(n||0).toLocaleString('ru-RU');
const pct=x=>Math.round(x*100)+'%';
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const sc=s=>'s'+Math.max(1,Math.min(5,s||1));
const fmtDate=s=>{const d=new Date(s);return isNaN(d)?'':d.toLocaleDateString('ru-RU',{day:'2-digit',month:'short',year:'2-digit'});};
const COL={'🔴':'var(--rose)','🟠':'var(--amber)','🟡':'#eab308','🟢':'var(--green)'};
const reacEng=r=>r?(r.angry+r.sad+r.love+r.care+r.haha+r.wow):0;
const linkLabel=p=>p.platform==='Threads'?'открыть в Threads ↗':p.platform==='Facebook'?'открыть пост ↗':'смотреть в Meta ↗';
const D=DATA,M=D.meta,app=document.getElementById('app');const SECTIONS=[];
const PAGE_DEFS=[['overview','Обзор'],['analytics','Аналитика'],['map','Карта'],['actions','Задачи и ответы'],['posts','Обращения'],['voice','Мнения жителей'],['methodology','Методология']];
if(DATA.month_review)PAGE_DEFS.splice(1,0,['month','Итоги · '+DATA.month_review.title]);
const PAGES={};
PAGE_DEFS.forEach(([id,label])=>{const el=$('div','page');el.id='page-'+id;el.dataset.page=id;app.appendChild(el);PAGES[id]={el,label,sections:[]};});
function sec(n,title,hint,page,tint,emoji){const s=$('section');s.id='s'+n;if(tint)s.classList.add('tint-'+tint);if(emoji)s.setAttribute('data-emoji',emoji);const h=$('div','sec-h');
 h.appendChild($('span','n',String(n).padStart(2,'0')));h.appendChild($('h2',null,title));
 if(hint)h.appendChild($('span','hint',hint));s.appendChild(h);const b=$('div');s.appendChild(b);
 const pg=PAGES[page||'overview'];pg.el.appendChild(s);pg.sections.push([n,title]);SECTIONS.push([n,title]);return b;}
// раскрываемый блок текста — ПОЛНЫЙ текст в DOM, сворачивание только визуально
function ptext(t,expanded){const id='p'+Math.random().toString(36).slice(2,8);
 return `<div class="ptext${expanded?'':' clamp'}" id="${id}">${esc(t)}</div><button class="morebtn" onclick="(function(b){const e=document.getElementById('${id}');e.classList.toggle('clamp');b.textContent=e.classList.contains('clamp')?'Развернуть ▾':'Свернуть ▴';})(this)">${expanded?'Свернуть ▴':'Развернуть ▾'}</button>`;}
function mefmt(p){return [p.platform,p.lang,p.tier,p.owner?('@'+p.owner):'',fmtDate(p.created_at)].filter(Boolean).join(' · ');}
function postCard(p,extra){const neg=p.severity>=4||p.sentiment==='негатив';
 return `<div class="card"><div class="accentbar" style="background:${neg?'var(--rose)':'var(--indigo)'}"></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
   <span class="sevtag ${sc(p.severity)}">острота ${p.severity}</span>
   <span class="pill ind">${esc(p.category)}</span>
   ${p.district?`<span class="pill">📍 ${esc(p.district)}</span>`:''}
   <span class="pill ${p.sentiment==='негатив'?'neg':p.sentiment==='позитив'?'ok':''}">${esc(p.sentiment)}</span>
   ${extra||''}</div>
  ${ptext(p.text)}
  <div class="tiny" style="margin-top:8px">${esc(mefmt(p))}</div>
  <div style="margin-top:8px">
   <span class="pill" title="лайки">👍 ${fmt(p.likes)}</span><span class="pill" title="комментарии">💬 ${fmt(p.comments)}</span>
   <span class="pill" title="репосты">🔁 ${fmt(p.shares)}</span>${reacEng(p.reactions)?`<span class="pill neg" title="негативные реакции">😡😢 ${fmt(p.reactions.angry+p.reactions.sad)}</span>`:''}
   <span class="pill ind" title="суммарная вовлечённость (лайки + комментарии + репосты)">охват ${fmt(p.eng)}</span>
   ${p.url?`<a class="pill" href="${esc(p.url)}" target="_blank">${linkLabel(p)}</a>`:''}</div>
  ${voiceBox(p)}
  ${feedbackBtns(p)}</div>`;}
function voiceBox(p){const v=p.voice;if(!v||!(v.summary||(v.suggestions&&v.suggestions.length)))return '';
 const SP={'возмущение':'neg','раскол':'warn','поддержка':'ok','нейтрально':''};
 return `<div class="voicebox"><div class="tiny" style="margin-bottom:4px">💬 Мнение жителей ${v.stance?`<span class="pill ${SP[v.stance]||''}">${esc(v.stance)}</span>`:''}</div>
   ${v.summary?`<div style="font-size:13px">${esc(v.summary)}</div>`:''}
   ${v.suggestions&&v.suggestions.length?`<ul class="cv-list">${v.suggestions.slice(0,3).map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`:''}</div>`;}
function spark(a){const m=Math.max(...a,1);return '<span class="spark">'+a.map(v=>`<i style="height:${Math.max(3,v/m*26)}px"></i>`).join('')+'</span>';}
function feedbackBtns(p){
 const meta={id:p.id,text:(p.text||'').slice(0,500),category:p.category,theme:p.theme||'',sentiment:p.sentiment,severity:p.severity,platform:p.platform};
 return `<div class="fb-btns" data-fb="${esc(JSON.stringify(meta))}">
   <span class="fb-note">Помогите обучить ИИ-фильтр:</span>
   <button class="fb-btn up" onclick="_sendFeedback(this,'up')" title="Собирать больше таких постов">👍 Собирать</button>
   <button class="fb-btn down" onclick="_sendFeedback(this,'down')" title="Не собирать такие посты">👎 Не собирать</button>
  </div>`;}
window._copyLink=function(btn,url){if(!url)return;
 navigator.clipboard&&navigator.clipboard.writeText(url);
 const old=btn.textContent;btn.textContent='✓ Скопировано';setTimeout(()=>btn.textContent=old,1500);};
/* Слайдер постов: один пост на слайд, листание стрелками/точками */
// Персональная рекомендация под конкретный пост (генерится из его содержания)
const CAT_ACT={
 'Дороги и транспорт':'проверить аварийный участок и организовать ремонт/регулирование движения',
 'ЖКХ и инфраструктура':'направить аварийную бригаду и восстановить услугу по адресу',
 'Вода и канализация':'проверить адрес перебоя и восстановить водоснабжение',
 'Электроснабжение':'сверить отключение с графиком АЖК и восстановить электроснабжение',
 'Экология и воздух':'проверить источник загрязнения и дать разъяснение по качеству среды',
 'Благоустройство и мусор':'организовать вывоз мусора и уборку территории',
 'Строительство и застройка':'проверить законность работ по объекту и соблюдение норм',
 'Безопасность и правопорядок':'усилить патрулирование, проверить обстоятельства и подключить полицию',
 'Здравоохранение':'запросить ответ у конкретного медучреждения и проверить ситуацию',
 'Образование':'подключить управление образования и проверить ситуацию в учреждении',
 'Госуслуги и бюрократия':'устранить сбой в госсервисе и упростить процедуру',
 'Цены и социальные вопросы':'разъяснить тарифы/цены и меры поддержки'};
function recoAction(text,cat){const t=(text||'').toLowerCase();
 if(/вод[аыоуе]|водоснаб|без воды|нет воды|канализ/.test(t))return 'восстановить водоснабжение, устранить аварию и сообщить сроки';
 if(/свет|электр|отключ.*(?:ток|энерг)|нет света|подстанц/.test(t))return 'восстановить электроснабжение и проверить сети';
 if(/отоплен|батаре|тепл[оая]|холодн.*(?:кварт|дом|подъезд)/.test(t))return 'проверить теплоснабжение и устранить сбой';
 if(/дорог|ям[аыу]|асфальт|тротуар|колдоб|разбит.*дорог/.test(t))return 'организовать ремонт дорожного покрытия';
 if(/дтп|авари|сбил|столкнов|наезд/.test(t))return 'проверить организацию движения и безопасность участка';
 if(/мусор|свалк|отход|грязь|убор|контейнер/.test(t))return 'организовать вывоз мусора и санитарную уборку';
 if(/пробк|затор|парков|трафик|развязк/.test(t))return 'проработать схему движения и парковочное пространство';
 if(/школ|детсад|садик|учител|ученик|буллинг|травл|образован/.test(t))return 'подключить управление образования и проверить ситуацию';
 if(/больниц|поликлин|врач|медиц|лечен|скорая|здоров/.test(t))return 'подключить управление здравоохранения';
 if(/автобус|трамвай|транспорт|остановк|маршрут|метро/.test(t))return 'проверить работу общественного транспорта на маршруте';
 if(/собак|животн|бродяч|кошк/.test(t))return 'организовать отлов и контроль безнадзорных животных';
 if(/мошен|обман|афер|развод.*деньг|вымога/.test(t))return 'передать материалы в полицию и предупредить горожан';
 if(/краж|грабёж|грабеж|разбой|нападени|избил|драк|стрельб|нож|убий|насил/.test(t))return 'усилить патрулирование и передать материалы в полицию';
 if(/шум|стройк|строит|снос|застро/.test(t))return 'проверить законность работ и соблюдение норм';
 if(/парк|сквер|дерев|озелен|вырубк/.test(t))return 'проверить состояние зелёной зоны и благоустройство';
 return CAT_ACT[cat]||'отработать обращение силами профильной службы';}
function postReco(p,a){const sev=+p.severity||1;
 const urg=sev>=5?'🔴 Немедленно (в течение 24 ч)':sev>=4?'🟠 Приоритетно (2–3 дня)':'🟡 В плановом порядке';
 const dept=(a&&a.department)?a.department:'профильное управление';
 const where=p.district?` в ${esc(p.district)} районе`:'';
 return `${urg} — <b>${esc(dept)}</b>${where}: ${esc(recoAction(p.text,p.category))}; дать публичный ответ автору и проверить факт.`;}
function alarmSlide(p,a){
 return `<div class="sl-slide"><div class="quote neg" style="margin:0">
   ${ptext(p.text)}
   <div class="tiny" style="margin-top:8px">${esc(mefmt(p))}</div>
   <div style="margin-top:8px">
     <span class="pill" title="лайки">👍 ${fmt(p.likes)}</span>
     <span class="pill" title="комментарии">💬 ${fmt(p.comments)}</span>
     <span class="pill" title="репосты">🔁 ${fmt(p.shares)}</span>
     <span class="pill ind" title="суммарная вовлечённость">охват ${fmt(p.eng)}</span>
     ${p.district?`<span class="pill">📍 ${esc(p.district)}</span>`:''}
     <span class="sevtag ${sc(p.severity)}">острота ${p.severity}</span>
     ${p.url?`<a class="pill" href="${esc(p.url)}" target="_blank">${linkLabel(p)}</a>`:''}
   </div>
   <div class="reco"><span class="reco-ic">▸</span><div><b>Рекомендация по обращению:</b> ${postReco(p,a)}</div></div>
   </div></div>`;}
function cardSlide(p){return `<div class="sl-slide">${postCard(p)}</div>`;}
function sliderHTML(samples,render){render=render||(p=>alarmSlide(p));
 const dots=samples.map((_,i)=>`<button class="sl-dot${i===0?' act':''}" data-go="${i}"></button>`).join('');
 return `<div class="slider" data-idx="0" data-n="${samples.length}">
   <div class="sl-viewport"><div class="sl-track">${samples.map(render).join('')}</div></div>
   <div class="sl-nav">
     <button class="sl-arrow sl-prev" disabled aria-label="назад">‹</button>
     <button class="sl-arrow sl-next"${samples.length<=1?' disabled':''} aria-label="вперёд">›</button>
     <span class="sl-count">1 / ${samples.length}</span>
     <div class="sl-dots">${dots}</div>
   </div></div>`;}
function wireSliders(root){root.querySelectorAll('.slider').forEach(sl=>{
 const track=sl.querySelector('.sl-track'),n=+sl.dataset.n||1;
 const prev=sl.querySelector('.sl-prev'),next=sl.querySelector('.sl-next');
 const count=sl.querySelector('.sl-count'),dots=[...sl.querySelectorAll('.sl-dot')];
 function go(i){i=Math.max(0,Math.min(n-1,i));sl.dataset.idx=i;
   track.style.transform=`translateX(-${i*100}%)`;count.textContent=(i+1)+' / '+n;
   prev.disabled=i===0;next.disabled=i===n-1;dots.forEach((d,k)=>d.classList.toggle('act',k===i));}
 prev.onclick=()=>go((+sl.dataset.idx)-1);next.onclick=()=>go((+sl.dataset.idx)+1);
 dots.forEach(d=>d.onclick=()=>go(+d.dataset.go));});}
function missingPersonCard(p){
 return `<div class="card" style="border-color:var(--rose)"><div class="accentbar" style="background:var(--rose)"></div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
   <span class="pill neg" style="font-weight:700">🆘 Пропавший человек</span>
   <span class="pill ind">${esc(p.category)}</span>
   ${p.district?`<span class="pill">📍 ${esc(p.district)}</span>`:''}
   <span class="tiny" style="margin-left:auto">${esc(fmtDate(p.created_at))}</span>
  </div>
  ${ptext(p.text)}
  <div class="tiny" style="margin-top:8px">${esc(mefmt(p))}</div>
  <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
   ${p.url?`<a class="btn" href="${esc(p.url)}" target="_blank" style="border-color:var(--rose);color:var(--rose)">Поделиться ↗</a>`:''}
   ${p.url?`<button class="btn" onclick="_copyLink(this,'${esc(p.url)}')">Скопировать ссылку</button>`:''}
  </div></div>`;}
function scraperStatusFooter(){
 const st=D.scraper_status;if(!st)return '';
 const mins=st.updated_at?Math.round((Date.now()-new Date(st.updated_at))/60000):null;
 const ago=mins===null?'нет данных':mins<1?'только что':mins<60?mins+' мин назад':Math.round(mins/60)+' ч назад';
 const lines=(st.lines||[]).slice(-12).map(esc).join('\n');
 const runs=(st.runs||[]).slice(0,5).map(r=>{const d=new Date(r.run_at);
  const dt=isNaN(d)?r.run_at:d.toLocaleString('ru-RU',{day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});
  return `<div class="row"><span>${esc(dt)}</span><span>${fmt(r.kept)}/${fmt(r.total_seen)} обращ.</span><span class="muted">${r.pass_rate_pct}%</span></div>`;}).join('');
 return `<div class="card" style="text-align:left;margin-bottom:18px">
   <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap">
    <span class="statusdot ${st.online?'on':'off'}"></span>
    <b>Сбор данных 24/7</b>
    <span class="pill ${st.online?'ok':''}">${st.online?'идёт сбор данных':'ожидание следующего запуска'}</span>
    <span class="pill" style="margin-left:auto">обновлено: ${ago}</span>
   </div>
   <div class="grid g2">
    <div><div class="tiny" style="margin-bottom:6px">Лог</div><div class="term-box">${lines||'лог пока пуст…'}</div></div>
    <div><div class="tiny" style="margin-bottom:6px">История запусков</div><div class="scraper-runs">${runs||'<span class="muted">нет истории</span>'}</div></div>
   </div></div>`;}

/* Иконки платформ (Threads / Facebook / Instagram) */
function platIcon(name){const n=(name||'').toLowerCase();
 if(n.indexOf('face')>=0)return `<svg viewBox="0 0 24 24" style="color:#1877f2" fill="currentColor"><path d="M9.101 23.69v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.6 8.6 0 0 0-.653-.036 26.8 26.8 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.69 1.69 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044 24 5.417 18.627.044 12 .044S0 5.417 0 12.044c0 5.628 3.874 10.35 9.101 11.647z"/></svg>`;
 if(n.indexOf('insta')>=0)return `<svg viewBox="0 0 24 24" style="color:#e1306c" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.3" cy="6.7" r="1.3" fill="currentColor" stroke="none"/></svg>`;
 if(n.indexOf('thread')>=0)return `<svg viewBox="0 0 24 24" style="color:var(--ink)" fill="currentColor"><path d="M16.7 11.16c-.09-.04-.18-.08-.27-.12-.16-2.93-1.76-4.6-4.45-4.62-1.62-.01-2.97.67-3.8 1.93l1.5 1.02c.62-.94 1.59-1.14 2.3-1.14h.03c.88.01 1.55.27 1.98.77.31.37.52.88.63 1.52a11.4 11.4 0 0 0-2.56-.12c-2.57.15-4.23 1.65-4.12 3.74.06 1.06.59 1.97 1.49 2.57.76.5 1.74.75 2.76.7 1.35-.08 2.4-.59 3.15-1.53.56-.71.92-1.63 1.07-2.79.63.38 1.1.88 1.36 1.48.44 1.02.46 2.7-.9 4.06-1.2 1.19-2.63 1.71-4.8 1.72-2.4-.02-4.22-.79-5.4-2.28C5.2 15.92 4.63 13.95 4.6 12c.02-1.95.6-3.91 1.7-5.27 1.18-1.5 3-2.26 5.4-2.28 2.42.02 4.25.79 5.45 2.29.59.74 1.03 1.66 1.32 2.74l1.6-.43c-.35-1.32-.9-2.47-1.66-3.42C18.36 3.7 16.07 2.74 13.1 2.72h-.01c-2.96.02-5.22.99-6.71 2.88C5 7.26 4.27 9.5 4.25 11.99v.02c.02 2.5.75 4.74 2.13 6.4 1.5 1.88 3.75 2.84 6.71 2.86h.01c2.63-.02 4.48-.71 6.01-2.23 2-1.98 1.94-4.46 1.28-5.99-.47-1.1-1.37-1.99-2.6-2.58zm-4.43 4.5c-1.13.06-2.3-.45-2.36-1.53-.04-.8.57-1.69 2.43-1.8.21-.01.42-.02.62-.02.68 0 1.31.07 1.89.2-.22 2.7-1.49 3.08-2.58 3.15z"/></svg>`;
 return '';}
/* Тепловой цвет зелёный→жёлтый→красный */
function _hx(h){return [parseInt(h.slice(1,3),16),parseInt(h.slice(3,5),16),parseInt(h.slice(5,7),16)];}
function _lerp(a,b,t){const A=_hx(a),B=_hx(b);return `rgb(${Math.round(A[0]+(B[0]-A[0])*t)},${Math.round(A[1]+(B[1]-A[1])*t)},${Math.round(A[2]+(B[2]-A[2])*t)})`;}
function heatColor(t){t=Math.max(0,Math.min(1,t));return t<.5?_lerp('#22c55e','#eab308',t/.5):_lerp('#eab308','#ef4444',(t-.5)/.5);}
/* Веерный bar-гейдж */
function fanGauge(val,max,label){val=val||0;max=max||100;const pct=Math.max(0,Math.min(1,val/max));
 const W=240,H=152,cx=120,cy=124,ri=64,ro=104,N=40;let bars='';
 for(let i=0;i<N;i++){const t=i/(N-1),a=Math.PI-t*Math.PI;
  const x1=cx+ri*Math.cos(a),y1=cy-ri*Math.sin(a),x2=cx+ro*Math.cos(a),y2=cy-ro*Math.sin(a);
  bars+=`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${heatColor(t)}" stroke-width="4" stroke-linecap="round" opacity="${t>pct?0.28:1}"/>`;}
 return `<svg viewBox="0 0 ${W} ${H}" style="width:240px;max-width:100%">${bars}
  <text x="${cx}" y="${cy-4}" text-anchor="middle" fill="#fff" font-family="Manrope" font-size="36" font-weight="800">${val}</text>
  <text x="${cx}" y="${cy+18}" text-anchor="middle" fill="#aab3c5" font-size="11">${esc(label||'')}</text></svg>`;}
/* Мини-спарклайн */
function sparkSvg(vals,color){if(!vals||!vals.length)return '';const w=220,h=42,mx=Math.max(...vals),mn=Math.min(...vals);
 const pts=vals.map((v,i)=>`${(i*(w/(vals.length-1))).toFixed(1)},${(h-((v-mn)/((mx-mn)||1))*(h-6)-3).toFixed(1)}`);
 return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="width:100%;height:42px"><polyline points="0,${h} ${pts.join(' ')} ${w},${h}" fill="${color}" opacity=".13"/><polyline points="${pts.join(' ')}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;}

/* HERO — командный центр (BioSync-стиль) + ЖИВЫЕ ЧАСЫ */
(function(){
 const negPct=Math.max(0,100-(M.sent_index||0));
 const allp=D.all_posts||[];const acute=allp.filter(p=>(+p.severity||0)>=4).length;
 const acutePct=allp.length?Math.round(100*acute/allp.length):0;
 const dmax=Math.max(...D.districts.map(d=>d.count),1);
 const heatRows=[...D.districts].sort((a,b)=>(b.neg||0)-(a.neg||0)).slice(0,6).map(d=>
   `<div class="heatrow"><span class="nm">${esc(d.name)}</span><span class="ht"><i style="width:${Math.max(8,Math.round(d.count/dmax*100))}%;background:${heatColor(d.neg||0)}"></i></span><span class="hv">${fmt(d.count)}</span></div>`).join('')
   ||'<div class="dpsub" style="color:#aab3c5">нет данных по районам</div>';
 const distTop=[...D.districts].sort((a,b)=>(b.neg||0)-(a.neg||0)).slice(0,4).map(d=>
   `<div style="display:flex;align-items:center;gap:10px;margin:9px 0">
     <span style="width:118px;font-size:12.5px;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(d.name)}</span>
     <span style="flex:1;height:8px;border-radius:5px;background:var(--track);overflow:hidden"><i style="display:block;height:100%;width:${Math.max(6,Math.round((d.neg||0)*100))}%;background:${heatColor(d.neg||0)}"></i></span>
     <span style="width:42px;text-align:right;font-size:11.5px;color:var(--ink3)">${pct(d.neg||0)}</span>
   </div>`).join('')||'<div class="tiny">нет данных</div>';
 const tl=D.timeline.map(t=>t.count);
 const dayHi=D.now24.n>D.now24.avg;
 const reachAvg=Math.round(M.reach/Math.max(D.timeline.length*7,1));
 const platChips=D.platforms.map(p=>`<span class="platchip">${platIcon(p.platform)}${esc(p.platform)} <b>${fmt(p.n)}</b></span>`).join('');
 const TAGS=['Сегодня · 24 ч','Эта неделя','Эта неделя'],NIC=['🛡','🚧','📣'];
 const nsteps=D.alarms.slice(0,3).map((a,i)=>{const p=(a.samples&&a.samples[0])||{};
   return `<div class="nstep"><div class="nic">${NIC[i]||'▸'}</div><div>
     <div class="nh"><b>${esc(a.category)}</b><span class="ntag">${TAGS[i]||'Эта неделя'}</span><span class="tiny" style="margin-left:auto">${esc(a.department)}</span></div>
     <ul><li>${esc(recoAction(p.text,p.category))}</li><li>${esc(a.recommendation)}</li></ul></div></div>`;}).join('');
 const TS=[['Обращений',fmt(M.total_kept)],['Охват',fmt(M.reach)],['Настроение',M.sent_index+'/100'],['Напряжённость',String(D.tension.value)],['Авторов',fmt(M.authors)],['Районов',String(M.districts)]];
 const tsEl=document.getElementById('topstrip');if(tsEl)tsEl.innerHTML=TS.map(m=>`<div class="ts"><div class="tl">${m[0]}</div><div class="tv">${m[1]}</div></div>`).join('');
 document.getElementById('hero').innerHTML=`
  <div class="ov-grid">
   <div class="ov-main">
    <div class="ov-head"><div><h2>${VIEW==='ump'?'Обзор · молодёжная политика':'Обзор города'}</h2><div class="tiny">${VIEW==='ump'?'Молодёжь, вузы и общежития Алматы':'Социальный слух Алматы'} · ${esc(M.period)}</div></div>
      <div class="plats" style="margin-left:auto">${platChips}</div></div>
    <div class="bk">
      <div class="bcard"><div class="bh"><span class="bl">Обращений за сутки</span><span class="stag"><i style="background:${dayHi?'var(--amber)':'var(--green)'}"></i>${dayHi?'выше':'норма'}</span></div>
        <div class="bv">${fmt(D.now24.n)}</div>${sparkSvg(tl,'#22c55e')}</div>
      <div class="bcard"><div class="bh"><span class="bl">Доля негатива</span><span class="stag"><i style="background:var(--rose)"></i>${negPct>=50?'высокая':'умеренная'}</span></div>
        <div class="bv">${negPct}%</div>
        <div class="cmp"><div class="crow"><span class="ct">негатив</span><span class="cb"><i style="width:${negPct}%;background:linear-gradient(90deg,#fb7185,#ef4444)"></i></span><span class="cn">${negPct}%</span></div>
          <div class="crow"><span class="ct">позитив</span><span class="cb"><i style="width:${100-negPct}%;background:linear-gradient(90deg,#86efac,#22c55e)"></i></span><span class="cn">${100-negPct}%</span></div></div></div>
      <div class="bcard"><div class="bh"><span class="bl">Острые инциденты</span><span class="stag">острота 4–5</span></div>
        <div class="bv">${acutePct}%</div><div class="tiny" style="margin-top:8px">${fmt(acute)} обращений повышенной остроты</div></div>
    </div>
    <div class="grid g2" style="margin-top:16px;align-items:start">
      <div class="card"><h3>🧠 AI-аналитика · напряжённость</h3>
        <div class="gauge-wrap" style="background:#2a3242;border-radius:14px;padding:8px 0 4px;margin-top:6px">${fanGauge(D.tension.value,100,'индекс напряжённости')}</div>
        <div style="display:flex;gap:8px;margin-top:10px"><span class="pill neg">негатив ${negPct}%</span><span class="pill warn">острые ${acutePct}%</span></div>
        <div class="tiny" style="margin:14px 0 2px">Самые напряжённые районы</div>
        ${distTop}</div>
      <div class="card"><div style="display:flex;align-items:center;gap:8px"><h3 style="margin:0">Очередь задач</h3>
        <button class="btn" style="margin-left:auto" onclick="if(window.showPage)showPage('actions')">Все →</button></div>
        <div class="nsteps">${nsteps}</div></div>
    </div>
   </div>
   <aside class="ov-rail">
    <div class="card ov-mapcard"><h3>🗺️ Районы города · напряжённость</h3>
      <div id="rmap"></div>
      <div class="ov-index"><span>Индекс напряжённости</span><b>${D.tension.value}/100</b></div></div>
    <div class="card"><h3 style="font-size:14px">Динамика обращений · по неделям</h3><div style="position:relative;height:160px"><canvas id="rtl"></canvas></div></div>
    <div class="card"><h3 style="font-size:14px">Структура по категориям</h3><canvas id="rct" height="140"></canvas></div>
   </aside>
  </div>`;
 setTimeout(()=>{try{
   const _dark=document.documentElement.dataset.theme==='dark';
   const rm=L.map('rmap',{scrollWheelZoom:false,attributionControl:false,zoomControl:false}).setView([43.245,76.92],10);
   (window._maps=window._maps||[]).push(rm);
   L.tileLayer(`https://{s}.basemaps.cartocdn.com/${_dark?'dark_all':'light_all'}/{z}/{x}/{y}{r}.png`,{maxZoom:18}).addTo(rm);
   const dc={};D.districts.forEach(d=>dc[d.name]=d);
   const md=n=>{for(const k in dc){if(n&&n.indexOf(k.replace(/ район.*/,''))>=0)return dc[k];}return null;};
   if(typeof GEO!=='undefined'&&GEO){const layer=L.geoJSON(GEO,{style:f=>{const d=md(f.properties.nameRu);return {color:_dark?'#3a4865':'#b9c4da',weight:1,fillColor:d?heatColor(d.neg||0):(_dark?'rgba(255,255,255,.06)':'#e8edf6'),fillOpacity:.82};},
     onEachFeature:(f,l)=>{const d=md(f.properties.nameRu);l.bindPopup(`<b>${esc(f.properties.nameRu||'')}</b><br>Обращений: ${d?fmt(d.count):0} · негатив ${d?pct(d.neg||0):'—'}`);}}).addTo(rm);
     try{rm.fitBounds(layer.getBounds(),{padding:[6,6]});}catch(e){}}
   setTimeout(()=>{try{rm.invalidateSize();}catch(e){}},220);
  }catch(e){}
  try{const cs=getComputedStyle(document.documentElement),cv=n=>cs.getPropertyValue(n).trim();
   Chart.defaults.color=cv('--ink2');Chart.defaults.borderColor=cv('--line');Chart.defaults.font.family='Inter';
   const wkLbl=w=>{const m=String(w).match(/(\d{4})-W(\d{2})/);if(!m)return w;const y=+m[1],wk=+m[2];const d=new Date(y,0,1+(wk-1)*7);const dow=d.getDay()||7;d.setDate(d.getDate()-dow+1);return d.toLocaleDateString('ru-RU',{day:'2-digit',month:'2-digit'});};
   new Chart(document.getElementById('rtl'),{type:'line',data:{labels:D.timeline.map(t=>wkLbl(t.week)),datasets:[{label:'обращений',data:D.timeline.map(t=>t.count),borderColor:'#38bdf8',backgroundColor:'rgba(56,189,248,.15)',fill:true,tension:.35,pointRadius:2,pointHoverRadius:5}]},
     options:{maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{title:it=>'неделя от '+it[0].label,label:it=>fmt(it.parsed.y)+' обращений'}}},
      scales:{x:{ticks:{maxRotation:0,autoSkip:true,maxTicksLimit:6,font:{size:9}},grid:{display:false}},
       y:{beginAtZero:true,ticks:{maxTicksLimit:4,font:{size:9}},grid:{color:cv('--line')}}}}});
   const pal=['#6366f1','#38bdf8','#2dd4bf','#f6b756','#fb7185','#a78bfa','#f472b6','#34d399'];
   new Chart(document.getElementById('rct'),{type:'doughnut',data:{labels:D.problems.slice(0,7).map(p=>p.category),datasets:[{data:D.problems.slice(0,7).map(p=>p.count),backgroundColor:pal,borderColor:cv('--surface'),borderWidth:2}]},options:{cutout:'60%',plugins:{legend:{position:'right',labels:{boxWidth:9,font:{size:9}}}}}});
  }catch(e){}
 },140);
 function tick(){const now=new Date();const alm=new Date(now.getTime()+(now.getTimezoneOffset()+300)*60000);
  const t=[alm.getHours(),alm.getMinutes(),alm.getSeconds()].map(x=>String(x).padStart(2,'0')).join(':');
  const dd=alm.toLocaleDateString('ru-RU',{weekday:'short',day:'2-digit',month:'long'});
  const mins=Math.round((now-new Date(M.updated_iso))/60000);
  const ago=isNaN(mins)?'':(mins<1?'только что':mins<60?mins+' мин назад':Math.round(mins/60)+' ч назад');
  document.getElementById('clock').innerHTML=`<span class="livedot"></span>Алматы · <b>${t}</b><br><span class="tiny">${dd} · обновлено ${ago}</span>`;}
 tick();setInterval(tick,1000);
})();

/* 2. САМЫЕ ОБСУЖДАЕМЫЕ ЗА СУТКИ (KPI за сутки теперь в командном центре) */
(function(){const l=D.now24;
 const viral=(l.viral_posts&&l.viral_posts.length)?l.viral_posts:(l.viral?[l.viral]:[]);
 if(!viral.length)return;
 const b=sec(2,'Самые обсуждаемые за сутки','посты с наибольшим резонансом · листайте ‹ ›','overview','indigo','📡');
 b.innerHTML=sliderHTML(viral,cardSlide);
 wireSliders(b);
})();

/* 3. ТОП ПРОБЛЕМ */
(function(){const b=sec(3,'ТОП проблем города','ранжирование по остроте, объёму и охвату','overview','amber','⚠️');
 const mx=Math.max(...D.problems.map(p=>p.count),1);
 b.innerHTML=`<div class="grid g3">`+D.problems.slice(0,9).map((p,i)=>{
  const tr=p.trend>0?`<span class="pill warn">▲ +${p.trend}</span>`:p.trend<0?`<span class="pill ok">▼ ${p.trend}</span>`:`<span class="pill">● ровно</span>`;
  return `<div class="card"><div class="rank">${i+1}</div>
   <h3>${p.status} ${esc(p.category)}</h3>
   <div class="muted tiny">${fmt(p.count)} обращений · охват ${fmt(p.engagement)}</div>
   <div class="bar7 ${p.neg_share>=.25?'neg':''}"><i style="width:${Math.round(p.count/mx*100)}%"></i></div>
   <div>${spark(p.spark)} <span class="pill ${p.neg_share>=.25?'neg':'warn'}">негатив ${pct(p.neg_share)}</span> ${tr}</div>
   <div style="margin:8px 0">${p.top_themes.slice(0,3).map(t=>`<span class="pill">${esc(t)}</span>`).join('')}</div>
   ${p.samples[0]?`<div class="quote ${p.neg_share>=.25?'neg':''}" style="margin:0">${ptext(p.samples[0].text)}</div>`:''}
  </div>`;}).join('')+`</div>`;
})();

/* 4. СИГНАЛЫ ТРЕВОГИ (слайдер постов по теме, рекомендация под каждый пост) */
(function(){const b=sec(4,'Сигналы тревоги','листайте обращения по каждой теме ‹ › · рекомендация под каждым','overview','rose','🚨');
 const dl=new Date(Date.now()+3*864e5).toLocaleDateString('ru-RU',{day:'2-digit',month:'long'});
 b.innerHTML=D.alarms.map((a,i)=>`<div class="card" style="margin-bottom:14px"><div class="accentbar" style="background:var(--rose)"></div>
   <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
    <span class="pill neg">#${i+1} СРОЧНО</span><h3>${esc(a.category)}</h3>
    <span class="tiny" style="margin-left:auto">${a.district?esc(a.district)+' район · ':''}${esc(a.department)}</span></div>
   <div style="margin:8px 0"><span class="lead-num" style="font-size:22px">${a.count}</span> обращений
    <span class="pill neg">негатив ${pct(a.neg_share)}</span><span class="pill warn">за 3 дня: ${a.recent}</span>
    <span class="sevtag ${sc(Math.round(a.avg_severity))}">острота ${a.avg_severity}</span></div>
   ${a.samples&&a.samples.length?`<div class="tiny" style="margin:8px 0 8px">Обращения по теме (${a.samples.length}) — листайте, под каждым своя рекомендация:</div>${sliderHTML(a.samples,p=>alarmSlide(p,a))}`:''}
   <div class="cf"><span>⚠</span><div>Без реакции до <b>${dl}</b> тема может усилиться. Рекомендации по каждому обращению — в карточках выше.</div></div>
  </div>`).join('');
 wireSliders(b);
})();

/* 18. ПРОПАВШИЕ ЛЮДИ */
(function(){const mposts=D.missing_persons||[];if(!mposts.length)return;
 const b=sec(18,'Пропавшие — нужна помощь','автособранные обращения о поиске людей · поделитесь, если можете','overview','rose','🔍');
 b.innerHTML=`<div class="cf"><b>⚠</b>&nbsp;Ниже — посты о поиске пропавших людей, собранные автоматически. Если можете — поделитесь.</div>
   <div class="grid g2" style="margin-top:12px">${mposts.map(missingPersonCard).join('')}</div>`;
})();

/* 19. МНЕНИЯ ЖИТЕЛЕЙ (отдельная вкладка): топ-решения + разбор по постам */
(function(){const cv=D.citizen_voice||[],tops=D.top_solutions||[];
 if(!cv.length&&!tops.length)return;
 const b=sec(19,'Мнения жителей','ИИ читает комментарии под резонансными постами и собирает решения','voice','green','💬');
 const SP={'возмущение':'neg','раскол':'warn','поддержка':'ok','нейтрально':''};
 const stance=s=>`<span class="pill ${SP[s]||''}">${esc(s||'—')}</span>`;
 let html=`<div class="cf" style="background:var(--ok-bg);border-color:var(--ok-bd);color:var(--ok-ink)"><b>💬</b>&nbsp;ИИ читает комментарии под резонансными постами, отсеивает спам и флуд и собирает, что жители предлагают.</div>`;
 if(tops.length){
   html+=`<div class="card" style="margin-top:14px"><div class="accentbar" style="background:var(--green)"></div>
     <h3>🏆 Топ решений для города</h3>
     <div class="tiny" style="margin-bottom:8px">сведено ИИ из предложений горожан под резонансными постами</div>
     <ol class="topsol">`+tops.map(t=>`<li><b>${esc(t.title)}</b>${t.category?` <span class="pill ind">${esc(t.category)}</span>`:''}${t.detail?`<div class="tiny" style="margin-top:2px">${esc(t.detail)}</div>`:''}</li>`).join('')+`</ol></div>`;
 }
 if(cv.length){
   html+=`<h3 style="margin:18px 0 10px">Разбор по постам</h3><div class="grid g2">`+cv.map(c=>`<div class="card">
     <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
       <span class="pill ind">${esc(c.category)}</span>${stance(c.stance)}
       <span class="tiny" style="margin-left:auto">${fmt(c.replies_total)} комм.</span></div>
     <div class="quote" style="margin:0 0 10px;font-size:13px">${esc(c.post_text)}…${c.url?` <a href="${esc(c.url)}" target="_blank" title="открыть пост">↗</a>`:''}</div>
     <div style="font-size:13.5px;margin-bottom:6px"><b>Мнение жителей:</b> ${esc(c.summary)}</div>
     ${c.suggestions&&c.suggestions.length?`<div class="tiny">Предложения горожан:</div><ul class="cv-list">${c.suggestions.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`:''}
   </div>`).join('')+`</div>`;
 }
 b.innerHTML=html;
})();

/* 5. МАТРИЦА УГРОЗ */
(function(){const b=sec(5,'Матрица угроз','ускорение × серьёзность · размер = объём','analytics');
 const W=760,H=420,PL=58,PB=44,PT=18,PR=20,mx=Math.max(...D.problems.map(t=>t.count),1);
 const gx=v=>PL+(Math.max(-1,Math.min(1,v))+1)/2*(W-PL-PR);
 const gy=v=>PT+(1-Math.min(v,.5)/.5)*(H-PT-PB);
 const bub=D.problems.map((t,i)=>{const x=gx(t.growth!=null?t.growth:0),y=gy(t.neg_share),r=8+Math.sqrt(t.count/mx)*26,red=t.neg_share>=.25;
   return `<circle class="bubble" cx="${x}" cy="${y}" r="${r}" fill="${red?'rgba(225,29,72,.18)':'rgba(79,70,229,.16)'}" stroke="${red?'var(--rose)':'var(--indigo)'}" stroke-width="1.5" data-i="${i}"/>
     <text x="${x}" y="${y-r-4}" fill="var(--ink2)" font-size="9" text-anchor="middle">${esc(t.category.split(' ')[0])}</text>`;}).join('');
 b.innerHTML=`<div class="card"><svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto">
   <line x1="${(PL+W-PR)/2}" y1="${PT}" x2="${(PL+W-PR)/2}" y2="${H-PB}" stroke="var(--line)"/>
   <line x1="${PL}" y1="${(PT+H-PB)/2}" x2="${W-PR}" y2="${(PT+H-PB)/2}" stroke="var(--line)"/>
   <text x="${PL+6}" y="${PT+13}" fill="var(--rose)" font-size="11" font-weight="600">🔴 действовать сейчас</text>
   <text x="${W-PR-6}" y="${PT+13}" fill="var(--amber)" font-size="11" font-weight="600" text-anchor="end">🟠 готовиться</text>
   <text x="${PL+6}" y="${H-PB-6}" fill="#a16207" font-size="11">🟡 контролировать</text>
   <text x="${W-PR-6}" y="${H-PB-6}" fill="var(--green)" font-size="11" text-anchor="end">🟢 наблюдать</text>
   <text x="${W/2}" y="${H-8}" fill="var(--ink3)" font-size="10" text-anchor="middle">ускорение темпа →</text>
   <text x="14" y="${H/2}" fill="var(--ink3)" font-size="10" transform="rotate(-90 14 ${H/2})" text-anchor="middle">% негатива →</text>
   ${bub}</svg><div id="bd" class="quote" style="display:none;margin-top:12px"></div></div>`;
 b.querySelectorAll('.bubble').forEach(c=>c.onclick=()=>{const t=D.problems[+c.dataset.i],d=b.querySelector('#bd');
   d.style.display='block';d.innerHTML=`<b>${t.status} ${esc(t.category)}</b> — ${t.count} обращений · негатив ${pct(t.neg_share)} · тренд ${t.trend>0?'+':''}${t.trend} · ${esc(t.recommendation)}`;});
})();

/* 6. ГОРЯЩИЕ ТЕМЫ + РЕКОМЕНДАЦИИ */
(function(){const b=sec(6,'Горящие темы и рекомендации','что делать профильным управлениям','analytics','amber','🔥');
 b.innerHTML=D.problems.slice(0,5).map(t=>{const act=t.neg_share>.25?'Эскалация':t.trend>0?'Координация':'В зоне контроля';
  return `<div class="card" style="margin-bottom:14px"><div class="accentbar" style="background:${COL[t.status]}"></div>
   <div style="display:flex;align-items:center;gap:10px"><h3>${t.status} ${esc(t.category)}</h3>
    <span class="tiny" style="margin-left:auto">${fmt(t.count)} обращений · ${esc(t.department)}</span></div>
   <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin:8px 0">${spark(t.spark)}
    <span class="pill ${t.neg_share>.25?'neg':'warn'}">негатив ${pct(t.neg_share)}</span>
    ${t.top_themes.slice(0,4).map(x=>`<span class="pill ind">${esc(x)}</span>`).join('')}
    <span class="pill ${t.neg_share>.25?'neg':'ok'}">${act}</span></div>
   <div style="font-size:14px">▸ <b>Рекомендация:</b> ${esc(t.recommendation)}</div></div>`;}).join('');
})();

/* 7. ОЧЕРЕДЬ ЗАДАЧ (конкретные задачи из реальных обращений) */
(function(){const b=sec(7,'Очередь задач акимата','конкретные задачи из реальных обращений · по адресам и темам','actions','indigo','🗂️');
 function plural(n){const a=n%10,bb=n%100;return (a===1&&bb!==11)?'обращение':(a>=2&&a<=4&&(bb<10||bb>=20))?'обращения':'обращений';}
 // группируем обращения темы по конкретному действию (из текста), берём топ-N групп
 function tasksFor(t,limit){const groups={};
   (t.samples||[]).forEach(p=>{const k=recoAction(p.text,p.category);(groups[k]=groups[k]||[]).push(p);});
   return Object.entries(groups).sort((a,c)=>c[1].length-a[1].length).slice(0,limit).map(([action,ps])=>{
     const districts=[...new Set(ps.map(x=>x.district).filter(Boolean))].slice(0,3).join(', ');
     const ex=ps[0],sev=Math.max(...ps.map(x=>+x.severity||1));
     const snippet=((ex.summary&&ex.summary.trim())||ex.text||'').replace(/\s+/g,' ').slice(0,130);
     return {action,n:ps.length,districts,sev,snippet,url:ex.url};});}
 function block(t,urgent){const items=tasksFor(t,urgent?4:2);
   const sub=items.map(it=>`<div style="display:flex;gap:9px;margin-top:9px">
      <span class="sevtag ${sc(it.sev)}" style="flex:none;height:fit-content">${it.sev}</span>
      <div style="min-width:0"><div style="font-size:13.5px">▸ <b>${esc(it.action)}</b>
        <span class="pill ${it.n>=3?'neg':'warn'}">${it.n} ${plural(it.n)}</span>${it.districts?` <span class="pill">📍 ${esc(it.districts)}</span>`:''}</div>
        <div class="quote ${t.neg_share>.25?'neg':''}" style="margin:5px 0 0;font-size:12.5px">«${esc(it.snippet)}…»${it.url?` <a href="${esc(it.url)}" target="_blank" title="открыть обращение">↗</a>`:''}</div></div></div>`).join('')
     ||'<div class="tiny" style="margin-top:6px">детализированных обращений нет</div>';
   const ab=t.neg_share>.25?'Нужна эскалация':t.trend>0?'Нужна координация':'Решается на месте',abc=t.neg_share>.25?'neg':t.trend>0?'warn':'ok';
   return `<div class="card" style="margin-bottom:10px"><div class="accentbar" style="background:${urgent?'var(--rose)':'var(--amber)'}"></div>
     <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
       <b>[${esc(t.department)}]</b><span style="font-weight:700">${esc(t.category)}</span>
       <span class="tiny" style="margin-left:auto">${fmt(t.count)} обращений · негатив ${pct(t.neg_share)}</span></div>
     ${sub}
     <div style="display:flex;gap:8px;align-items:center;margin-top:10px;flex-wrap:wrap">
       <span class="pill ${abc}">${ab}</span>
       <span class="tiny">${urgent?'Срок 24–48ч · по каждому пункту проверить факт и дать публичный ответ':'Срок: эта неделя · отработать адреса и подготовить разъяснение'}</span></div></div>`;}
 b.innerHTML=`<h3 style="color:var(--rose);margin:4px 0 8px">🔴 Сегодня · первые 24 часа</h3>${D.alarms.slice(0,2).map(t=>block(t,true)).join('')}
   <h3 style="color:var(--amber);margin:16px 0 8px">🟠 Эта неделя</h3>${D.problems.slice(0,3).map(t=>block(t,false)).join('')}
   <h3 style="color:#a16207;margin:16px 0 8px">🟡 Следующие 30 дней</h3>
   <div class="card"><div class="accentbar" style="background:var(--indigo)"></div><b>[Аналитика + Цифровизация]</b> Перевести мониторинг соцсетей в постоянный режим (автообновление).
     <div class="tiny" style="margin-top:5px">Метрика: дашборд обновляется автоматически, среднее время реакции < 48ч.</div></div>`;
})();

/* 8. ЧЕРНОВИКИ ОТВЕТОВ */
(function(){const b=sec(8,'Черновики официальных ответов','сформировано автоматически — проверьте перед публикацией','actions','green','✅');
 b.innerHTML=D.alarms.slice(0,3).map(a=>{const d=a.district?(' в '+a.district+' районе'):'';const resp=(a.draft||'').replace('{d}',d);
   return `<div class="card" style="margin-bottom:14px"><div class="accentbar" style="background:var(--indigo)"></div>
     <h3>${esc(a.category)}${a.district?' · '+esc(a.district):''}</h3>
     ${a.samples[0]?`<div class="muted tiny">Что пишут жители:</div><div class="quote neg" style="margin-top:4px">${ptext(a.samples[0].text)}</div>`:''}
     <div class="muted tiny">Ответ от лица города (черновик):</div>
     <div class="quote" style="border-left-color:var(--green);background:var(--ok-bg)">${esc(resp)}</div>
     <button class="btn copy">📋 Скопировать ответ</button></div>`;}).join('');
 b.querySelectorAll('.copy').forEach(x=>x.onclick=()=>{const q=x.previousElementSibling;navigator.clipboard&&navigator.clipboard.writeText(q.textContent);x.textContent='✓ Скопировано';setTimeout(()=>x.textContent='📋 Скопировать ответ',1500);});
})();

/* 9. КАРТА */
(function(){const b=sec(9,'География проблем по районам',`плотность обращений · за ${esc(M.period)}`,'map');
 if(!GEO){b.innerHTML='<div class="muted">Карта недоступна</div>';return;}
 b.innerHTML=`<div class="card"><div id="map"></div></div>`;
 const dc={};D.districts.forEach(d=>dc[d.name]=d.count);
 const md=n=>{for(const k in dc){if(n&&n.indexOf(k.replace(/ район.*/,''))>=0)return dc[k];}return 0;};
 setTimeout(()=>{const map=L.map('map',{scrollWheelZoom:false}).setView([43.245,76.92],11);
  (window._maps=window._maps||[]).push(map);
  const _dark=document.documentElement.dataset.theme==='dark';
  L.tileLayer(`https://{s}.basemaps.cartocdn.com/${_dark?'dark_all':'light_all'}/{z}/{x}/{y}{r}.png`,{attribution:'© OSM, © CARTO',maxZoom:18}).addTo(map);
  const counts=GEO.features.map(f=>md(f.properties.nameRu)),mxD=Math.max(...counts,1);
  const col=c=>c?`rgba(99,102,241,${0.20+0.6*c/mxD})`:(_dark?'rgba(255,255,255,.06)':'#e8edf6');
  const layer=L.geoJSON(GEO,{style:f=>({color:_dark?'#3a4865':'#b9c4da',weight:1,fillColor:col(md(f.properties.nameRu)),fillOpacity:.85}),
    onEachFeature:(f,l)=>{const c=md(f.properties.nameRu);l.bindPopup(`<b>${esc(f.properties.nameRu||f.properties.name)}</b><br>Обращений: ${c}`);
      l.on('mouseover',()=>l.setStyle({weight:2.5,color:'#4f46e5'}));l.on('mouseout',()=>layer.resetStyle(l));}}).addTo(map);
  try{map.fitBounds(layer.getBounds(),{padding:[12,12]});}catch(e){}},80);
})();

/* 20. ИЮНЬ: ОБЗОР МЕСЯЦА — игровая карта районов + ИИ-сводка */
(function(){const R=D.month_review;if(!R)return;
 const b=sec(20,R.title+': обзор месяца',`исторический срез · ${esc(R.period)} · ${fmt(R.n)} проверенных обращений`,'month','indigo','🗓️');
 const EMO={'Дороги и транспорт':'🚗','ЖКХ и инфраструктура':'🔧','Вода и канализация':'🚱','Электроснабжение':'⚡','Экология и воздух':'🌫️','Благоустройство и мусор':'🗑️','Строительство и застройка':'🏗️','Безопасность и правопорядок':'🚨','Здравоохранение':'🏥','Образование':'🎓','Госуслуги и бюрократия':'📄','Цены и социальные вопросы':'💸','Прочее':'💬'};
 const topCat=R.categories[0];
 const chips=[
  ['📨','Обращений',fmt(R.n)],
  ['📢','Суммарный охват',fmt(R.reach)],
  ['😠','Негативных',Math.round(R.neg*100)+'%'],
  ['🔥','Острых (4–5)',fmt(R.acute)],
  topCat?[EMO[topCat.category]||'💬','Тема месяца',esc(topCat.category)]:null
 ].filter(Boolean).map(c=>`<div class="mr-chip"><span class="ic">${c[0]}</span><span>${c[1]}<br><b>${c[2]}</b></span></div>`).join('');
 const mx=Math.max(...R.categories.map(c=>c.count),1);
 const quests=R.categories.filter(c=>c.category!=='Прочее').slice(0,6).map((c,i)=>`<div class="card quest">
   <div class="q-rank">#${i+1}</div>
   <div class="q-ic">${EMO[c.category]||'💬'}</div>
   <h3>${esc(c.category)}</h3>
   <div class="tiny">${fmt(c.count)} обращений · ${pct(c.share)} корпуса · охват ${fmt(c.eng)}</div>
   <div class="bar7 ${c.neg>=.5?'neg':''}"><i style="width:${Math.max(6,Math.round(c.count/mx*100))}%"></i></div>
   ${c.top_post?`<div class="quote ${c.neg>=.5?'neg':''}" style="margin:8px 0 0">${ptext(c.top_post.text)}</div>
   <div style="margin-top:8px"><span class="pill ind">охват ${fmt(c.top_post.eng)}</span>${c.top_post.url?`<a class="pill" href="${esc(c.top_post.url)}" target="_blank">${linkLabel(c.top_post)}</a>`:''}</div>`:''}
  </div>`).join('');
 b.innerHTML=`<div class="mr-hud">${chips}</div>
  <div class="mr-grid">
   <div class="card">
    <h3>🗺️ Карта районов · что волновало жителей</h3>
    <div class="tiny">нажмите на маркер или район — главная тема и самое резонансное обращение июня</div>
    <div id="mrmap"></div>
    <div class="cf" style="margin:10px 0 0"><b>⚠</b>&nbsp;Район удалось определить у ${fmt(R.district_tagged)} из ${fmt(R.n)} обращений — маркер «❔» означает «недостаточно данных за месяц», а не отсутствие проблем в районе.</div>
   </div>
   <div class="card ai-sum">
    <div class="ai-head"><span class="ai-badge">🤖 ИИ-сводка</span><b style="font-family:var(--disp)">${esc(R.title)}</b></div>
    ${R.ai_summary.map(p=>`<p>${esc(p)}</p>`).join('')}
    <div class="tiny" style="margin-top:4px">Сводка сформирована ИИ по ${fmt(R.n)} AI-проверенным обращениям за ${esc(R.period)} · проверьте факты перед использованием</div>
   </div>
  </div>
  <div class="card" style="margin-top:16px"><h3>🏆 Топ-темы месяца</h3>
   <div class="tiny" style="margin-bottom:10px">категории по объёму обращений · в каждой — самый резонансный пост</div>
   <div class="grid g3">${quests}</div></div>`;
 setTimeout(()=>{try{
  if(!GEO)return;
  const _dark=document.documentElement.dataset.theme==='dark';
  const m=L.map('mrmap',{scrollWheelZoom:false}).setView([43.245,76.92],10);
  (window._maps=window._maps||[]).push(m);
  L.tileLayer(`https://{s}.basemaps.cartocdn.com/${_dark?'dark_all':'light_all'}/{z}/{x}/{y}{r}.png`,{attribution:'© OSM, © CARTO',maxZoom:18}).addTo(m);
  const dm={};R.districts.forEach(d=>dm[d.name]=d);
  const md=n=>{for(const k in dm){if(n&&n.indexOf(k)>=0)return dm[k];}return null;};
  const layer=L.geoJSON(GEO,{style:f=>{const d=md(f.properties.nameRu),has=d&&d.count>0;
    return{color:_dark?'#3a4865':'#b9c4da',weight:1.2,dashArray:has?null:'4 4',
     fillColor:has?heatColor(Math.min(1,d.neg||0)):(_dark?'rgba(255,255,255,.05)':'#e8edf6'),fillOpacity:has?.5:.35};},
   onEachFeature:(f,l)=>{const d=md(f.properties.nameRu),has=d&&d.count>0;
    const top=has?d.posts[0]:null;
    const pop=has?`<div class="mr-pop"><b>${esc(f.properties.nameRu)}</b><br>Главная тема: <b>${EMO[d.top_category]||'💬'} ${esc(d.top_category)}</b> · обращений: ${d.count}
      ${top?`<div class="mr-popq">«${esc(top.text.slice(0,180))}${top.text.length>180?'…':''}»</div>${top.url?`<a href="${esc(top.url)}" target="_blank">${linkLabel(top)}</a>`:''}`:''}</div>`
     :`<div class="mr-pop"><b>${esc(f.properties.nameRu)}</b><br><span style="color:var(--ink3)">Недостаточно данных за месяц: ни в одном обращении район не был определён.</span></div>`;
    l.bindPopup(pop);
    const icon=L.divIcon({className:'',html:`<div class="mr-pin${has?'':' ghost'}">${has?(EMO[d.top_category]||'💬'):'❔'}${has?`<span class="mr-cnt">${d.count}</span>`:''}</div>`,iconSize:[46,46],iconAnchor:[23,23]});
    L.marker(l.getBounds().getCenter(),{icon}).addTo(m).bindPopup(pop);
    l.on('mouseover',()=>l.setStyle({weight:2.6,color:'#4f46e5'}));l.on('mouseout',()=>layer.resetStyle(l));}}).addTo(m);
  const fit=()=>{try{m.invalidateSize();m.fitBounds(layer.getBounds(),{padding:[10,10]});}catch(e){}};
  fit();
  // карта создаётся в скрытой вкладке (контейнер нулевого размера) — переподгоняем при первом показе
  new IntersectionObserver((es,o)=>{es.forEach(e=>{if(e.isIntersecting){setTimeout(fit,90);o.disconnect();}});}).observe(document.getElementById('mrmap'));
 }catch(e){}},120);
})();

/* 10. ИНДЕКС НАПРЯЖЁННОСТИ + ТОНАЛЬНОСТЬ */
(function(){const b=sec(10,'Эмоциональный профиль города','напряжённость и тональность по темам','analytics');
 const v=D.tension.value,ang=-90+v/100*180,col=v<25?'var(--green)':v<50?'#eab308':v<75?'var(--amber)':'var(--rose)';
 const gauge=`<div class="card" style="text-align:center"><h3>Индекс управляемой напряжённости</h3>
   <svg viewBox="0 0 300 165" style="width:280px;max-width:100%">
   <path d="M30 150 A120 120 0 0 1 270 150" fill="none" stroke="var(--track)" stroke-width="18" stroke-linecap="round"/>
   <path d="M30 150 A120 120 0 0 1 270 150" fill="none" stroke="${col}" stroke-width="18" stroke-linecap="round" stroke-dasharray="${v/100*377} 377"/>
   <line x1="150" y1="150" x2="${150+92*Math.cos(ang*Math.PI/180)}" y2="${150+92*Math.sin(ang*Math.PI/180)}" stroke="var(--ink)" stroke-width="3"/>
   <circle cx="150" cy="150" r="6" fill="var(--ink)"/><text x="150" y="120" text-anchor="middle" fill="var(--ink)" font-size="34" font-weight="800" font-family="Manrope">${v}</text></svg>
   <div style="font-weight:700;color:${col}">${esc(D.tension.label)}</div></div>`;
 const senti=`<div class="card"><h3>Тональность по темам</h3>`+D.senti_by_cat.map(r=>{const t=r.neg+r.neu+r.pos||1;
   return `<div style="margin-bottom:9px"><div style="display:flex;justify-content:space-between;font-size:13px"><b>${esc(r.category)}</b><span class="tiny mono">▼${r.neg} ▬${r.neu} ▲${r.pos}</span></div>
     <div class="stack"><i style="width:${r.neg/t*100}%;background:var(--rose)"></i><i style="width:${r.neu/t*100}%;background:#cbd5e7"></i><i style="width:${r.pos/t*100}%;background:var(--green)"></i></div></div>`;}).join('')+
   `<div class="legend"><span><i style="background:var(--rose)"></i>негатив</span><span><i style="background:#cbd5e7"></i>нейтрально</span><span><i style="background:var(--green)"></i>позитив</span></div></div>`;
 b.innerHTML=`<div class="grid g2">${gauge}${senti}</div>`;
})();

/* 11. ДИНАМИКА + СТРУКТУРА */
(function(){const b=sec(11,'Динамика и структура','объём по неделям · доли категорий','analytics');
 const wdCard=(D.weekday_topics||[]).map(w=>`<div class="card" style="padding:10px 12px">
    <div class="tiny" style="font-weight:700;margin-bottom:6px">${esc(w.day)}</div>
    ${w.top.length?w.top.map(t=>`<div class="tiny" style="display:flex;justify-content:space-between;gap:8px;margin:2px 0"><span>${esc(t.category)}</span><b>${fmt(t.count)}</b></div>`).join(''):'<div class="tiny" style="opacity:.5">нет данных</div>'}
  </div>`).join('');
 b.innerHTML=`<div class="grid g2"><div class="card"><h3>Динамика обращений по неделям</h3><canvas id="tl" height="150"></canvas></div>
   <div class="card"><h3>Распределение по категориям</h3><canvas id="ct" height="150"></canvas></div></div>
   <div class="card" style="margin-top:14px"><h3>Темы по дням недели</h3><div class="tiny" style="margin-bottom:8px">топ-3 категории по объёму обращений в этот день недели, за весь период</div>
     <div class="grid" style="grid-template-columns:repeat(7,1fr);gap:8px">${wdCard}</div></div>`;
 setTimeout(()=>{const _cs=getComputedStyle(document.documentElement),cv=n=>_cs.getPropertyValue(n).trim();
  Chart.defaults.color=cv('--ink2')||'#5c6b86';Chart.defaults.borderColor=cv('--line')||'#e9edf6';Chart.defaults.font.family='Inter';
  const ind=cv('--indigo')||'#6366f1';
  new Chart(document.getElementById('tl'),{type:'line',data:{labels:D.timeline.map(t=>t.week.replace(/^\d+-/,'')),
    datasets:[{data:D.timeline.map(t=>t.count),borderColor:ind,backgroundColor:'rgba(99,102,241,.14)',fill:true,tension:.35,pointRadius:2}]},
    options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}});
  const pal=['#6366f1','#38bdf8','#2dd4bf','#f6b756','#fb7185','#a78bfa','#f472b6','#34d399','#fbbf24','#94a3b8','#fda4b4','#7dd3fc'];
  new Chart(document.getElementById('ct'),{type:'doughnut',data:{labels:D.problems.map(p=>p.category),datasets:[{data:D.problems.map(p=>p.count),backgroundColor:pal,borderColor:cv('--surface')||'#fff',borderWidth:2}]},
    options:{plugins:{legend:{position:'right',labels:{boxWidth:11,font:{size:10}}}}}});},60);
})();

/* 12. ПЛАТФОРМЫ / ЯЗЫКИ / ИСТОЧНИКИ */
(function(){const b=sec(12,'Платформы, языки и источники','откуда идут сигналы','analytics');
 const LN={ru:'Русский',kk:'Қазақша',en:'English','—':'без языка'};
 const plat=D.platforms.map(p=>`<div class="card"><h3 style="display:flex;align-items:center;gap:9px"><span class="picon">${platIcon(p.platform)}</span>${esc(p.platform)}</h3><div class="lead-num">${fmt(p.n)}</div>
   <div class="tiny">постов · охват ${fmt(p.eng)}</div><div style="margin-top:6px"><span class="pill ${p.neg>.22?'neg':''}">негатив ${pct(p.neg)}</span><span class="pill ind">${esc(p.toptheme)}</span></div></div>`).join('');
 const langs=D.langs.map(l=>`<span class="pill">${esc(LN[l.lang]||l.lang)}: ${fmt(l.n)}</span>`).join('');
 const tiers=D.tiers.map(t=>`<span class="pill ind">${esc(t.tier)}: ${fmt(t.n)}</span>`).join('');
 b.innerHTML=`<div class="grid g2">${plat}</div>
   <div class="card" style="margin-top:14px"><h3>Языки обращений</h3><div style="margin:8px 0">${langs}</div>
     <div class="tiny">Двуязычная аудитория — официальные ответы дублировать на казахском и русском.</div></div>
   <div class="card" style="margin-top:14px"><h3>Кто пишет</h3><div style="margin-top:8px">${tiers}</div></div>`;
})();

/* 13. ТОП-ПОСТЫ (фильтр по дате) */
(function(){const b=sec(13,'Топ обращений по охвату','топ по охвату за выбранный период · «Развернуть» — полный текст','posts');
 const pool=(D.feed_posts||[]).filter(p=>p.created_at&&!isNaN(+new Date(p.created_at)));
 const aday=iso=>{const a=new Date((+new Date(iso))+5*3600*1000);return a.getUTCFullYear()+'-'+String(a.getUTCMonth()+1).padStart(2,'0')+'-'+String(a.getUTCDate()).padStart(2,'0');};
 const maxT=pool.reduce((m,p)=>Math.max(m,+new Date(p.created_at)),0);
 const refKey=aday(maxT),yestKey=aday(maxT-864e5);
 const FILT={
   today:{label:'Сегодня',fn:p=>aday(p.created_at)===refKey},
   yest:{label:'Вчера',fn:p=>aday(p.created_at)===yestKey},
   d3:{label:'3 дня',fn:p=>(maxT-+new Date(p.created_at))<=3*864e5},
   d7:{label:'Неделя',fn:p=>(maxT-+new Date(p.created_at))<=7*864e5},
   all:{label:'Всё время',fn:()=>true}};
 const order=['today','yest','d3','d7','all'];
 let cur=order.find(k=>pool.some(FILT[k].fn))||'all';
 b.innerHTML=`<div class="datefilter">`+order.map(k=>`<button class="df-btn" data-k="${k}">${FILT[k].label}</button>`).join('')+`</div>
   <div id="topgrid" class="grid g2"></div>`;
 const grid=b.querySelector('#topgrid');
 function draw(){b.querySelectorAll('.df-btn').forEach(x=>x.classList.toggle('act',x.dataset.k===cur));
   const rows=pool.filter(FILT[cur].fn).sort((x,y)=>(y.eng||0)-(x.eng||0)).slice(0,10);
   grid.innerHTML=rows.length?rows.map(p=>postCard(p)).join(''):`<div class="card quiet-card muted" style="grid-column:1/-1">За этот период обращений нет — выберите другой период.</div>`;}
 b.querySelectorAll('.df-btn').forEach(x=>x.onclick=()=>{cur=x.dataset.k;draw();});
 draw();
})();

/* 14. СЛОВА-ТРИГГЕРЫ */
(function(){const b=sec(14,'Слова, о которых говорит город','частотность тем','posts');
 b.innerHTML=`<div class="grid g2">
   <div class="card"><h3>Самые частые слова</h3><div style="margin-top:8px">${D.triggers.map(t=>`<span class="pill ind">${esc(t[0])} <b>×${t[1]}</b></span>`).join('')}</div></div>
   <div class="card"><h3>Чаще всего в негативных обращениях</h3><div style="margin-top:8px">${D.negwords.map(t=>`<span class="pill neg">${esc(t[0])} <b>×${t[1]}</b></span>`).join('')}</div></div></div>`;
})();

/* 15. СПРАВКА ПРЕСС-СЛУЖБЫ */
(function(){const b=sec(15,'Справка для пресс-службы','черновик — сформирован автоматически','actions','green','📣');
 const t0=D.problems[0],t1=D.problems[1],dd=[...D.districts].sort((a,b)=>b.neg-a.neg)[0];
 b.innerHTML=`<div class="card"><div class="accentbar" style="background:var(--indigo)"></div>
   <p>За период (${esc(M.period)}) внимание горожан в соцсетях сосредоточено вокруг темы «${esc((t0?t0.category:'').toLowerCase())}» — около ${t0?pct(t0.count/M.total_kept):'—'} всех городских обращений${t1?`, заметно также «${esc(t1.category.toLowerCase())}»`:''}.</p>
   <p>Индекс настроения ${M.sent_index}/100, индекс управляемой напряжённости ${D.tension.value}/100 («${esc(D.tension.label.toLowerCase())}»).${dd?` Наиболее напряжённый профиль — в районе ${esc(dd.name)}.`:''} Аудитория двуязычная (рус/каз).</p>
   <p>Рекомендуемая линия: оперативные адресные разъяснения по конкретным локациям, открытая публикация сроков и результатов, опора на верифицированные данные.</p>
   <button class="btn copy2">📋 Скопировать справку</button></div>`;
 const bt=b.querySelector('.copy2');bt.onclick=()=>{navigator.clipboard&&navigator.clipboard.writeText(b.querySelector('.card').innerText.replace('📋 Скопировать справку',''));bt.textContent='✓ Скопировано';setTimeout(()=>bt.textContent='📋 Скопировать справку',1500);};
})();

/* 16. ВСЕ ОБРАЩЕНИЯ */
(function(){const b=sec(16,'Все обращения','поиск · фильтры · полный текст','posts');const posts=D.all_posts.slice();
 b.innerHTML=`<div class="card"><div class="toolbar">
   <input id="q" placeholder="🔎 Поиск по тексту, категории, автору…">
   <select id="fcat"><option value="">Все категории</option></select>
   <select id="fdist"><option value="">Все районы</option></select>
   <select id="fplat"><option value="">Все платформы</option><option>Facebook</option><option>Instagram</option></select>
   <select id="fsev"><option value="0">Любая острота</option><option value="4">≥ 4</option><option value="5">5</option></select>
   <button class="btn" id="expandall">Развернуть все ▾</button>
   <span class="pill ind" id="cnt"></span></div>
   <div style="max-height:680px;overflow:auto"><table id="tbl"><thead><tr>
   <th data-k="severity">Острота</th><th data-k="category">Категория</th><th data-k="text">Текст обращения</th>
   <th data-k="district">Район</th><th data-k="platform">Платформа</th><th data-k="eng">Охват</th><th>↗</th></tr></thead><tbody></tbody></table></div></div>`;
 const fcat=b.querySelector('#fcat'),fdist=b.querySelector('#fdist');
 [...new Set(posts.map(p=>p.category))].sort().forEach(c=>fcat.add(new Option(c,c)));
 [...new Set(posts.map(p=>p.district).filter(Boolean))].sort().forEach(d=>fdist.add(new Option(d,d)));
 let sk='severity',sd=-1,allExpanded=false;
 function draw(){const q=b.querySelector('#q').value.toLowerCase().trim(),c=fcat.value,dd=fdist.value,pl=b.querySelector('#fplat').value,sv=+b.querySelector('#fsev').value;
   let rows=posts.filter(p=>{if(c&&p.category!==c)return false;if(dd&&p.district!==dd)return false;if(pl&&p.platform!==pl)return false;if(sv&&p.severity<sv)return false;
     if(q&&!(p.text+' '+p.category+' '+p.owner).toLowerCase().includes(q))return false;return true;});
   rows.sort((a,bb)=>{let va=sk==='eng'?a.eng:a[sk],vb=sk==='eng'?bb.eng:bb[sk];if(typeof va==='string')return sd*(va||'').localeCompare(vb||'','ru');return sd*((va||0)-(vb||0));});
   b.querySelector('#cnt').textContent=fmt(rows.length)+' обращений';
   b.querySelector('#tbl tbody').innerHTML=rows.slice(0,400).map(p=>`<tr>
     <td><span class="sevtag ${sc(p.severity)}">${p.severity}</span></td><td><span class="pill ind">${esc(p.category)}</span></td>
     <td style="max-width:560px">${ptext(p.text,allExpanded)}<div class="tiny" style="margin-top:4px">${esc(mefmt(p))}</div></td>
     <td>${esc(p.district||'—')}</td><td>${esc(p.platform)}</td>
     <td class="mono">👍${fmt(p.likes)} 💬${fmt(p.comments)} 🔁${fmt(p.shares)}<br><span title="суммарная вовлечённость">охват ${fmt(p.eng)}</span></td>
     <td>${p.url?`<a href="${esc(p.url)}" target="_blank" title="${esc(linkLabel(p))}">↗</a>`:''}</td></tr>`).join('')
     +(rows.length>400?`<tr><td colspan="7" class="tiny" style="text-align:center">Показаны первые 400 из ${fmt(rows.length)}. Уточните фильтры.</td></tr>`:'');}
 b.querySelectorAll('#tbl th[data-k]').forEach(th=>th.onclick=()=>{const k=th.dataset.k;if(sk===k)sd*=-1;else{sk=k;sd=-1;}draw();});
 b.querySelector('#expandall').onclick=()=>{allExpanded=!allExpanded;b.querySelector('#expandall').textContent=allExpanded?'Свернуть все ▴':'Развернуть все ▾';draw();};
 ['q','fcat','fdist','fplat','fsev'].forEach(id=>b.querySelector('#'+id).addEventListener('input',draw));draw();
 // глобальный поиск из верхней панели управляет этой таблицей
 const sectionEl=b.closest('section');
 window.__search=(q,scroll)=>{const qq=b.querySelector('#q');qq.value=q;draw();if(scroll){showPage('posts');sectionEl.scrollIntoView({behavior:'smooth'});}};
})();

/* 17. МЕТОДОЛОГИЯ */
(function(){const b=sec(17,'Методология','как это посчитано','methodology');const r=M.removed;
 b.innerHTML=`<details class="method" open><summary>Раскрыть методологию и оговорки</summary>
   <div style="font-size:13.5px;line-height:1.7;padding-bottom:14px">
   <p><b>Источник.</b> Публичные посты Facebook и Instagram (Meta Content Library) по тематике Алматы за ${esc(M.period)}. Собрано <b>${fmt(M.total_raw)}</b>, после очистки осталось <b>${fmt(M.total_kept)}</b> релевантных (${M.kept_pct}%).</p>
   <p><b>Очистка (жёсткая).</b> Удалено: реклама/коммерция — ${fmt(r.junk)}; оффтоп (не городские темы) — ${fmt(r.offtopic||0)}; дубликаты — ${fmt(r.dup)}; короткие/ссылки — ${fmt(r.short)}; не про Алматы — ${fmt(r.not_almaty)}; брендированный контент — ${fmt(r.branded)}. Правила покрывают русский и казахский (телефоны, прайсы, «жазыңыз», промо). Оставлены только гражданские темы и явные жалобы.</p>
   <p><b>Тональность.</b> Для Facebook используются реальные реакции (😡 angry + 😢 sad → негатив, ❤ love/care → позитив) и словари ru/kk; для Instagram — словарный метод. Категории и районы — по ключевым словам и упоминаниям локаций.</p>
   <p><b>Метрики достоверны:</b> лайки/комментарии/репосты/реакции берутся напрямую из Meta Content Library (без «фантомных» чисел).</p>
   ${M.ai_verified?`<p><b>AI-проверка (xAI Grok).</b> Каждый показанный пост подтверждён моделью как реальная городская тема Алматы; реклама, заказные/проплаченные и нерелевантные посты удалены, категория и острота выставлены ИИ. Поэтому в дашборде только проверенные обращения.</p>`:''}
   <p><b>Ссылки на посты.</b> Для Facebook — прямой permalink на публикацию; для Instagram публичной ссылки в выгрузке нет, поэтому ведёт в Meta Content Library (требует доступа).</p>
   <p><b>Оговорка.</b> Метрики и классификация могут содержать ошибки; перед управленческими решениями рекомендуется верификация. Прогнозы иллюстративны.</p>
   </div></details>`;
})();

/* САЙДБАР-НАВИГАЦИЯ + СТРАНИЦЫ */
(function(){
 const NAVIC={overview:'▣',month:'🗓',analytics:'📊',map:'🗺',actions:'✔',posts:'✉',voice:'💬',methodology:'⚙'};
 const sbnav=document.getElementById('sbnav');
 PAGE_DEFS.forEach(([id,label])=>{const t=document.createElement('button');t.type='button';t.className='sb-item';t.dataset.page=id;
  t.innerHTML=`<span class="sb-ic">${NAVIC[id]||'•'}</span><span>${esc(label)}</span>`;
  t.onclick=()=>{showPage(id);const sb=document.getElementById('sidebar');if(sb)sb.classList.remove('open');};sbnav.appendChild(t);});
 const heroEl=document.getElementById('s1');
 window.showPage=function(id,opts){opts=opts||{};if(!PAGES[id])return;
  Object.entries(PAGES).forEach(([k,v])=>v.el.classList.toggle('active',k===id));
  document.querySelectorAll('.sb-item[data-page]').forEach(t=>t.classList.toggle('active',t.dataset.page===id));
  if(heroEl)heroEl.style.display=(id==='overview')?'':'none';
  try{sessionStorage.setItem('activePage',id);}catch(e){}
  setTimeout(()=>{(window._maps||[]).forEach(m=>{try{m.invalidateSize();}catch(e){}});},70);
  if(opts.scroll!==false)window.scrollTo(0,0);};
 // при загрузке — восстановить вкладку и позицию (не выкидывать на «Обзор» после автообновления)
 let _saved=null;try{_saved=sessionStorage.getItem('activePage');}catch(e){}
 showPage(_saved&&PAGES[_saved]?_saved:PAGE_DEFS[0][0],{scroll:false});
 try{const _sy=+sessionStorage.getItem('scrollY')||0;if(_sy){setTimeout(()=>window.scrollTo(0,_sy),160);sessionStorage.removeItem('scrollY');}}catch(e){}
})();
document.getElementById('foot').insertAdjacentHTML('beforebegin', scraperStatusFooter());
document.getElementById('foot').innerHTML=`Data-driven аналитика соцсетей · Акимат г. Алматы · ${esc(M.period)} · обновлено ${esc(M.generated_at)} · черновик для верификации`;
window._sendFeedback=async function(btn,verdict){
 const wrap=btn.closest('.fb-btns');if(!wrap)return;
 let meta;try{meta=JSON.parse(wrap.dataset.fb);}catch{return;}
 wrap.querySelectorAll('.fb-btn').forEach(b=>b.disabled=true);
 try{
  const r=await fetch('/api/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...meta,verdict})});
  if(!r.ok){throw new Error('HTTP '+r.status);}
  localStorage.setItem('fb_'+meta.id,verdict);
  _paintFeedback(wrap,verdict);
 }catch(e){wrap.querySelectorAll('.fb-btn').forEach(b=>b.disabled=false);}
};
function _paintFeedback(wrap,verdict){
 wrap.querySelectorAll('.fb-btn').forEach(b=>{b.disabled=true;b.classList.toggle('voted',b.classList.contains(verdict));});
 const note=wrap.querySelector('.fb-note');if(note)note.textContent=verdict==='up'?'Спасибо, учтено ✓':'Принято, больше таких не будет ✓';
}
document.querySelectorAll('.fb-btns').forEach(wrap=>{
 let meta;try{meta=JSON.parse(wrap.dataset.fb);}catch{return;}
 const v=localStorage.getItem('fb_'+meta.id);if(v)_paintFeedback(wrap,v);
});
const ao=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in');}),{threshold:.08});
document.querySelectorAll('section').forEach(s=>{s.classList.add('fade');ao.observe(s);});
function counters(){document.querySelectorAll('[data-c]').forEach(el=>{const tgt=+el.dataset.c;if(!tgt)return;let st=null;
 function step(t){if(!st)st=t;const p=Math.min((t-st)/1000,1);el.textContent=fmt(Math.round(tgt*(1-Math.pow(1-p,3))));if(p<1)requestAnimationFrame(step);}requestAnimationFrame(step);});}
window.addEventListener('load',counters);
// верхний поиск: фильтрует по вводу, прокручивает к таблице по Enter
(function(){const gs=document.getElementById('gs');if(!gs)return;
 gs.addEventListener('input',e=>window.__search&&window.__search(e.target.value,false));
 gs.addEventListener('keydown',e=>{if(e.key==='Enter')window.__search&&window.__search(e.target.value,true);});})();

/* ПОП-АП «Проактивное управление» — всплывает поверх страницы после анимаций */
(function(){const alarms=(D.alarms||[]).slice(0,4);if(!alarms.length)return;
 const dl=new Date(Date.now()+3*864e5).toLocaleDateString('ru-RU',{day:'2-digit',month:'long'});
 const items=alarms.map((a,i)=>{const p=(a.samples&&a.samples[0])||{};
   return `<div class="pm-item"><div class="pm-rank">${i+1}</div>
     <div class="pm-body"><h4>${a.status||'🔴'} ${esc(a.category)}</h4>
       <div class="pm-meta">${fmt(a.count)} обращений · негатив ${pct(a.neg_share)} · за 3 дня ${a.recent} · острота ${a.avg_severity} · ${esc(a.department||'')}</div>
       <div class="pm-reco"><b>Упреждающее действие:</b> ${postReco(p,a)}</div></div></div>`;}).join('');
 const bg=$('div','modal-bg');bg.id='pmodal';
 bg.innerHTML=`<div class="modal" role="dialog" aria-modal="true" aria-label="Проактивное управление">
   <div class="modal-top"><button class="modal-x" aria-label="закрыть">✕</button>
     <div class="mt-tag">🛡 Проактивное управление</div>
     <h2>Что требует упреждающих действий</h2>
     <p>Топ-${alarms.length} тем с наибольшим риском роста. Реакция до <b>${dl}</b> снижает эскалацию и негатив.</p></div>
   <div class="modal-body">${items}</div>
   <div class="modal-foot"><button class="btn-primary" id="pm-go">Перейти к задачам акимата →</button>
     <button class="btn-ghost" id="pm-close">Понятно, закрыть</button></div></div>`;
 document.body.appendChild(bg);
 const fab=$('button','pm-fab');fab.id='pmfab';fab.innerHTML='🛡 <span>Проактивное управление</span>';fab.title='Открыть проактивное управление';
 document.body.appendChild(fab);
 const open=()=>bg.classList.add('show'),close=()=>bg.classList.remove('show');
 bg.querySelector('.modal-x').onclick=close;bg.querySelector('#pm-close').onclick=close;fab.onclick=open;
 bg.querySelector('#pm-go').onclick=()=>{close();if(window.showPage)showPage('actions');
   const s7=document.getElementById('s7');if(s7)setTimeout(()=>s7.scrollIntoView({behavior:'smooth'}),80);};
 bg.addEventListener('click',e=>{if(e.target===bg)close();});
 document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
 if(!sessionStorage.getItem('pm_seen'))setTimeout(()=>{open();sessionStorage.setItem('pm_seen','1');},2200);
})();
setTimeout(()=>{try{sessionStorage.setItem('scrollY',String(window.scrollY||window.pageYOffset||0));}catch(e){}location.reload();},300000);
</script>
</body>
</html>"""
