#!/usr/bin/env python3
"""
run_hourly.py — Полный часовой парсинг Threads по теме Алматы.

Два прохода:
  ФАЗА 0 — TOP-посты (виральные, высокий охват)
            Threads сортирует по умолчанию по вовлечённости.
            Окно: последние 7 дней.  Скроллинг: до упора.

  ФАЗА 1 — ВСЕ СВЕЖИЕ (последние 2 часа, вкладка Recent)
            Скроллинг: до упора — пока не кончатся новые посты.

Чекпоинты (стриминг на Vercel):
  - После фазы 0: сохраняет и деплоит в фоне
  - Каждые DEPLOY_EVERY_SOURCES источников в фазе 1: деплоит в фоне
  - Не чаще одного деплоя в DEPLOY_MIN_INTERVAL секунд
  - Финальный деплой после всего (ждёт завершения)

Результат: посты отсортированы по охвату (топ — первым).
  output/threads_live.json   — текущие посты (обновляется на каждом чекпоинте)
  output/hourly_TIMESTAMP.json  — финальный снимок всех постов
  output/top_TIMESTAMP.json     — топ-50 по охвату
  logs/hourly_stats.json        — история запусков
  logs/hourly_TIMESTAMP.log     — подробный лог
"""

import sys
import os
import json
import time
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter

# ── Логирование до импорта almaty_monitor ────────────────────────────────────
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE       = Path(__file__).parent
LOG_DIR    = HERE / "logs"
OUT_DIR    = HERE / "output"
LIVE_JSON  = OUT_DIR / "threads_live.json"   # перезаписывается на каждом чекпоинте
STATS_FILE = LOG_DIR / "hourly_stats.json"
LOG_DIR.mkdir(exist_ok=True)

NOW  = datetime.now(timezone.utc)
_ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"hourly_{_ts}.log"

_root = logging.getLogger()
_root.setLevel(logging.INFO)
_fmt  = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
_fh   = logging.FileHandler(log_file, encoding="utf-8")
_fh.setFormatter(_fmt)
_sh   = logging.StreamHandler(sys.stdout)
_sh.setFormatter(_fmt)
_root.addHandler(_fh)
_root.addHandler(_sh)

log = logging.getLogger(__name__)


# ── Live tail для дашборда: последние строки лога → logs/live_tail.json ─────
LIVE_TAIL_FILE = LOG_DIR / "live_tail.json"
LIVE_TAIL_MAX  = 80


class _TailHandler(logging.Handler):
    """Пишет последние LIVE_TAIL_MAX строк лога в JSON — дашборд показывает их как live-консоль."""

    def __init__(self):
        super().__init__()
        self._lines = []

    def emit(self, record):
        try:
            self._lines.append(self.format(record))
            if len(self._lines) > LIVE_TAIL_MAX:
                self._lines = self._lines[-LIVE_TAIL_MAX:]
            LIVE_TAIL_FILE.write_text(
                json.dumps(
                    {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "run_started": NOW.isoformat(),
                        "lines": self._lines,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass


_th = _TailHandler()
_th.setFormatter(_fmt)
_root.addHandler(_th)

from dotenv import load_dotenv   # noqa: E402
load_dotenv()
import almaty_monitor as am      # noqa: E402

# ── Параметры ────────────────────────────────────────────────────────────────
# ФАЗА 0 (TOP) собирает посты С НАЧАЛА ГОДА — глубокий охват «всего, что было».
# START_OF_YEAR вычисляется в run(); WINDOW_RECENT — окно «свежего» прохода.
WINDOW_RECENT = timedelta(hours=24)   # окно для свежих постов (было 2ч — мало)
SCROLL_MAX    = 320                    # глубина скролла на слово: берем шире, чтобы добирать годовые посты
                                       # узкие слова останавливаются раньше (исчерпание выдачи)

# Стриминг на Vercel: как часто деплоить во время парсинга
DEPLOY_EVERY_SOURCES  = 3    # деплоить после каждых N источников в фазе 1
DEPLOY_MIN_INTERVAL   = 300  # секунд между деплоями (5 минут — меньше нет смысла)

# ── Ключевые слова ───────────────────────────────────────────────────────────
# Для TOP-фазы берём широкий тематический набор — чтобы за год собрать максимум.
KEYWORDS_TOP = [
    "алматы", "almaty", "алматы проблемы", "акимат алматы", "алматы жкх",
    "алматы дороги", "алматы воздух", "алматы вода", "алматы мусор",
    "алматы свет", "алматы аким", "алматы пробки", "алматы транспорт",
    "алматы происшествия", "алматы строительство", "алматы экология",
    "алматы школа", "алматы студент", "алматы общежитие", "open almaty",
]

KEYWORDS_RECENT = [
    "алматы", "almaty", "алматы проблемы", "акимат алматы",
    "алматы жкх", "алматы дороги", "алматы воздух", "алматы вода",
    "алматы мусор", "алматы свет", "алматы аким", "open almaty",
    "алматы пробки", "алматы транспорт", "алматы происшествия",
    "алматы школа", "алматы студент", "алматы общежитие",
]

TAGS_RECENT = [
    "алматы", "almaty", "алматыпроблемы",
    "алматыдороги", "алматыжкх", "алматытранспорт", "алматыэкология",
    "алматышкола", "алматыстуденты",
]


# ── Охват поста ──────────────────────────────────────────────────────────────
def engagement(post: dict) -> int:
    return (
        post.get("like_count", 0)
        + post.get("reply_count", 0) * 2
        + post.get("repost_count", 0) * 3
    )


# ── Live-сохранение и стриминг на Vercel ─────────────────────────────────────
_last_deploy_time: float = 0.0
_deploy_proc: "subprocess.Popen | None" = None


def _current_results(collected: dict) -> list:
    results = [v for v in collected.values() if v is not None]
    results.sort(key=engagement, reverse=True)
    return results


def save_live(collected: dict) -> int:
    """Сохраняет текущее состояние в threads_live.json. Возвращает кол-во постов."""
    OUT_DIR.mkdir(exist_ok=True)
    results = _current_results(collected)
    LIVE_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(results)


def fire_deploy(collected: dict, *, blocking: bool = False):
    """
    Запускает merge_and_deploy.py в фоне (или синхронно если blocking=True).
    Соблюдает минимальный интервал между деплоями.
    """
    global _last_deploy_time, _deploy_proc

    now_ts = time.time()
    if not blocking and (now_ts - _last_deploy_time) < DEPLOY_MIN_INTERVAL:
        remaining = int(DEPLOY_MIN_INTERVAL - (now_ts - _last_deploy_time))
        log.info(f"[deploy] Skipped — next deploy in {remaining}s")
        return

    # Завершить предыдущий процесс если всё ещё крутится
    if _deploy_proc and _deploy_proc.poll() is None:
        if blocking:
            log.info("[deploy] Waiting for previous deploy to finish...")
            _deploy_proc.wait()
        else:
            log.info("[deploy] Previous deploy still running — skip this checkpoint")
            return

    n = save_live(collected)
    log.info(f"[deploy] Firing merge_and_deploy.py  ({n} posts)  {'(blocking)' if blocking else '(background)'}")

    _last_deploy_time = now_ts
    _deploy_proc = subprocess.Popen(
        [sys.executable, str(HERE / "merge_and_deploy.py"), str(LIVE_JSON)],
        cwd=str(HERE),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if blocking:
        stdout, _ = _deploy_proc.communicate()
        if stdout:
            for line in stdout.decode("utf-8", errors="replace").splitlines():
                log.info(f"  [deploy] {line}")


# ── Основной скрапинг ────────────────────────────────────────────────────────
def run() -> tuple:
    collected: dict = {}
    stats = {"kept": 0, "junk": 0, "bot": 0, "out_of_range": 0, "not_complaint": 0}

    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    exe = next((p for p in candidates if os.path.exists(p)), None)

    from playwright.sync_api import sync_playwright  # noqa: E402
    launch_kw = dict(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    if exe:
        launch_kw["executable_path"] = exe

    with sync_playwright() as pw:
        session = {}

        def _open_session():
            """(Пере)создаёт browser/ctx/page. Закрывает предыдущую сессию, если была жива."""
            old_browser = session.get("browser")
            if old_browser is not None:
                try:
                    old_browser.close()
                except Exception:
                    pass
            browser = ctx = None
            try:
                browser, ctx = am._build_context(pw, launch_kw)
            except RuntimeError as e:
                log.error(str(e))
                session.clear()
                return None
            page = ctx.new_page()
            try:
                page.goto("https://www.threads.com/", wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(2000)
                log.info("Session ready")
            except Exception as e:
                log.warning(f"Warmup: {e}")
            session.update(browser=browser, ctx=ctx, page=page)
            return page

        if _open_session() is None:
            return [], {}, 0

        def _run_step(fn, *args, **kwargs):
            """Запускает шаг скрапинга; при падении браузера пересоздаёт сессию
            и пропускает этот источник — чтобы одно упавшее ключевое слово/тег
            не обрывало весь часовой прогон (было: TargetClosedError убивал run())."""
            try:
                fn(session["page"], *args, **kwargs)
                return True
            except Exception as e:
                log.error(f"Источник упал ({e.__class__.__name__}: {e}) — пересоздаю браузер и продолжаю")
                if _open_session() is None:
                    log.error("Не удалось пересоздать браузерную сессию — прекращаю сбор")
                    return False
                return True

        # ════════════════════════════════════════════════════════════════
        # ФАЗА 0: TOP-посты (default sort = по вовлечённости) — С НАЧАЛА ГОДА
        # ════════════════════════════════════════════════════════════════
        START_OF_YEAR = NOW.replace(month=1, day=1, hour=0, minute=0,
                                    second=0, microsecond=0)
        log.info(f"\n{'='*54}")
        log.info(f"PHASE 0: TOP posts  |  window: since {START_OF_YEAR.date()} (start of year)")
        log.info(f"{'='*54}")
        am.START_DATE = START_OF_YEAR
        am.END_DATE   = NOW

        for kw in KEYWORDS_TOP:
            if not _run_step(am.scrape_search, kw, collected, stats,
                             scroll_limit=SCROLL_MAX, click_recent=False):
                break
            time.sleep(2)
            # Чекпоинт внутри фазы 0 — сразу стримим накопленное на Vercel
            fire_deploy(collected, blocking=False)

        log.info(f"Phase 0 done: {stats['kept']} posts")
        # Чекпоинт 1 — деплоим топ-посты сразу, не ждём фазу 1
        fire_deploy(collected, blocking=False)

        # ════════════════════════════════════════════════════════════════
        # ФАЗА 1: Все свежие (Recent, последние 2 часа)
        # ════════════════════════════════════════════════════════════════
        log.info(f"\n{'='*54}")
        log.info(f"PHASE 1: RECENT posts  |  window: last {int(WINDOW_RECENT.total_seconds()//3600)}h")
        log.info(f"{'='*54}")
        am.START_DATE = NOW - WINDOW_RECENT
        am.END_DATE   = NOW

        for i, kw in enumerate(KEYWORDS_RECENT, 1):
            if not _run_step(am.scrape_search, kw, collected, stats,
                             scroll_limit=SCROLL_MAX, click_recent=True):
                break
            time.sleep(2)
            # Чекпоинт: каждые DEPLOY_EVERY_SOURCES источников
            if i % DEPLOY_EVERY_SOURCES == 0:
                fire_deploy(collected, blocking=False)

        for i, tag in enumerate(TAGS_RECENT, 1):
            if not _run_step(am.scrape_tag, tag, collected, stats, scroll_limit=SCROLL_MAX):
                break
            time.sleep(2)
            if i % DEPLOY_EVERY_SOURCES == 0:
                fire_deploy(collected, blocking=False)

        if session.get("browser") is not None:
            try:
                session["browser"].close()
            except Exception:
                pass

    results = _current_results(collected)
    total_unique = len(collected)
    return results, stats, total_unique


# ── Финальное сохранение ──────────────────────────────────────────────────────
def save_final(results: list):
    OUT_DIR.mkdir(exist_ok=True)

    all_path = OUT_DIR / f"hourly_{_ts}.json"
    all_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    top_path = OUT_DIR / f"top_{_ts}.json"
    top_path.write_text(json.dumps(results[:50], ensure_ascii=False, indent=2), encoding="utf-8")

    # Обновляем live-файл финальной версией
    LIVE_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    return all_path, top_path


# ── Отчёт ────────────────────────────────────────────────────────────────────
def report(results: list, stats: dict, total_unique: int):
    kept  = stats["kept"]
    cats  = dict(Counter(r["category"] for r in results).most_common())
    other = total_unique - kept - stats["junk"] - stats["bot"] - stats["out_of_range"]

    entry = {
        "run_at":   NOW.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "windows":  {"top": "last 7 days", "recent": "last 2h"},
        "total_seen":    total_unique,
        "kept":          kept,
        "pass_rate_pct": round(100 * kept / max(total_unique, 1), 1),
        "filtered":      {
            "junk": stats["junk"], "bot": stats["bot"],
            "out_of_range": stats["out_of_range"] + max(other, 0),
        },
        "categories": cats,
        "top3": [
            {"username": p["username"],
             "text": p["text"][:80],
             "engagement": engagement(p),
             "url": p.get("url", "")}
            for p in results[:3]
        ],
    }

    history: list = []
    if STATS_FILE.exists():
        try:
            history = json.loads(STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    history.append(entry)
    STATS_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info(f"\n{'='*54}")
    log.info(f"  REPORT  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    log.info(f"{'='*54}")
    log.info(f"  Unique seen   : {total_unique}")
    log.info(f"  Passed filter : {kept}  ({entry['pass_rate_pct']}%)")
    log.info(f"  Junk/ads      : {stats['junk']}")
    log.info(f"  Bots          : {stats['bot']}")
    log.info(f"  Out of range  : {entry['filtered']['out_of_range']}")
    log.info(f"  Categories:")
    for cat, n in cats.items():
        log.info(f"    {cat:<26} {n:>4}  {'█' * min(n, 35)}")
    log.info(f"  Top by engagement:")
    for i, p in enumerate(results[:5], 1):
        eng  = engagement(p)
        text = p["text"][:60] + "…" if len(p["text"]) > 60 else p["text"]
        log.info(f"    #{i}  eng={eng:>5}  @{p['username']}")
        log.info(f"         {text}")
    log.info(f"{'='*54}")
    return entry


# ── Точка входа ───────────────────────────────────────────────────────────────
def main():
    log.info(f"{'='*54}")
    log.info(f"  HOURLY SCRAPER  |  {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    log.info(f"  Phase 0: TOP (since start of year)  +  Phase 1: RECENT ({int(WINDOW_RECENT.total_seconds()//3600)}h)")
    log.info(f"  Live Vercel deploy: every {DEPLOY_EVERY_SOURCES} sources / min {DEPLOY_MIN_INTERVAL}s")
    log.info(f"{'='*54}")

    results, stats, total_unique = run()

    if not results:
        log.warning("No posts collected.")
        return

    all_path, top_path = save_final(results)
    report(results, stats, total_unique)

    # Финальный деплой — ждём чтобы убедиться что дашборд обновился
    log.info("\n[deploy] Final deploy (blocking)...")
    fire_deploy({f"_r{i}": r for i, r in enumerate(results)}, blocking=True)

    log.info(f"All posts  : {all_path}  ({len(results)} posts)")
    log.info(f"Top-50     : {top_path}")
    log.info(f"Live JSON  : {LIVE_JSON}")
    log.info(f"Stats      : {STATS_FILE}")
    log.info(f"Log        : {log_file}")


if __name__ == "__main__":
    main()
