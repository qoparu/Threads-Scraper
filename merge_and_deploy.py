#!/usr/bin/env python3
"""
merge_and_deploy.py — Промежуточный деплой дашборда во время парсинга.

Запускается run_hourly.py как фоновый процесс на каждом чекпоинте.
Не ждёт окончания парсинга — работает параллельно.

Что делает:
  1. Читает текущие Threads-посты из output/threads_live.json
  2. Конвертирует их в схему meta_clean.json
  3. Мёржит с существующими Meta-данными (FB + Instagram)
  4. Пересобирает public/index.html через build_dashboard.py
  5. Деплоит на Vercel

Использование:
    python merge_and_deploy.py                       # берёт output/threads_live.json
    python merge_and_deploy.py output/my_file.json   # явный путь к Threads-данным
"""

import sys
import os
import re
import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE       = Path(__file__).parent
META_CLEAN = HERE / "data" / "meta_clean.json"
LIVE_MERGE = HERE / "data" / "meta_clean_live.json"
THREADS_LIVE = HERE / "output" / "threads_live.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [deploy] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

from dotenv import load_dotenv  # noqa: E402
load_dotenv()


# ── Инференс тональности и остроты из текста ────────────────────────────────

_SEV5 = re.compile(
    r"авари|пожар|взрыв|чп|чрезвычайн|погиб|убит|умер|труп|эвакуац|"
    r"суицид|самоубийств|өзін-өзі өлтір|өлімге|мектеп.*өлім|буллинг.*школ|"
    r"трагед.*школ|трагед.*студент", re.I)
_SEV4 = re.compile(
    r"нет воды|без воды|нет света|отключ|прорыв|дтп|нападени|грабёж|кража|обруш|"
    r"буллинг|кибербуллинг|травля|давлени.*школ|школ.*давлен|мектеп.*қысым", re.I)
_SEV3 = re.compile(r"пробк|затор|мусор|грязь|яма|яму|жалоб|проблем|не работ|невозможно|ужас", re.I)

_NEG = re.compile(
    r"жалоб|беспредел|ужас|безобраз|недовол|проблем|нет воды|нет света|не работ|"
    r"плохо|грязь|мусор|бардак|шокировал|возмущ|стыд|кошмар|невозможно|отключ", re.I
)
_POS = re.compile(r"спасибо|молодц|хорошо|отлично|улучш|благодар|рад\b|класс", re.I)

_COMPLAINT = re.compile(
    r"жалоб|шағым|проблем|нет воды|нет света|отключ|яма|пробк|мусор|"
    r"беспредел|требу|почему|когда сделают|помогите|акимат", re.I
)


def _hard_drop(text: str, owner: str = "") -> bool:
    try:
        from ingest_meta import is_nonlocal_or_media_noise  # noqa: WPS433
        return is_nonlocal_or_media_noise(text, owner)
    except Exception:
        return bool(re.search(r"belarus|беларус|минск|әнші|актрис|певиц|бортсерік", text, re.I))


def _severity(text: str) -> int:
    if _SEV5.search(text): return 5
    if _SEV4.search(text): return 4
    if _SEV3.search(text): return 3
    return 2


def _sentiment(text: str) -> str:
    if _NEG.search(text): return "негатив"
    if _POS.search(text): return "позитив"
    return "нейтрально"


# ── Конвертация Threads-поста в схему meta_clean ────────────────────────────

# Даже вирусный локальный пост про Алматы не наберёт сотни миллионов лайков/репостов —
# такие значения означают баг парсинга (в счётчик попал обрывок ID/даты вместо реального числа).
_MAX_SANE_COUNT = 5_000_000


def _sane_count(n) -> int:
    try:
        n = int(n)
    except (TypeError, ValueError):
        return 0
    return n if 0 <= n <= _MAX_SANE_COUNT else 0


def threads_to_meta(p: dict) -> dict:
    text = p.get("text", "")
    owner = p.get("username", "")
    likes   = _sane_count(p.get("like_count", 0))
    replies = _sane_count(p.get("reply_count", 0))
    reposts = _sane_count(p.get("repost_count", 0))
    return {
        "id":          f"Th_{p.get('id', '')}",
        "platform":    "Threads",
        "lang":        "ru",
        "owner_name":  owner,
        "owner_type":  "person",
        "created_at":  p.get("created_at", ""),
        "likes":       likes,
        "comments":    replies,
        "shares":      reposts,
        "reactions":   {},
        "views":       0,
        "hashtags":    "",
        "url":         p.get("url", ""),
        "mcl_url":     "",
        "text":        text,
        "is_branded":  False,
        "category":    p.get("category", "Прочее"),
        "sentiment":   _sentiment(text),
        "severity":    _severity(text),
        "district":    "",
        "tier":        "Горожанин",
        "is_complaint": bool(_COMPLAINT.search(text)),
        "theme":       "",
        "summary":     "",
        "engagement":  likes + replies + reposts,
        "grok_done":   False,
        "grok_todo":   True,
        "drop":        _hard_drop(text, owner),
    }


def apply_live_grok(posts: list) -> list:
    """Classify live Threads posts before they can enter the dashboard feed."""
    if os.getenv("ENABLE_LIVE_GROK", "1").lower() in {"0", "false", "no"}:
        log.info("Live Grok disabled by ENABLE_LIVE_GROK")
        return posts

    api_key = (os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
               or os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY") or "").strip()
    if not api_key:
        log.warning("No LLM_API_KEY — live Threads remain unverified")
        return posts

    try:
        import grok_filter as gf  # noqa: WPS433
    except Exception as e:
        log.warning(f"Live Grok unavailable: {e}")
        return posts

    cache = gf.load_cache()
    todo = [p for p in posts if not p.get("drop") and p["id"] not in cache]
    if todo:
        log.info(f"Live Grok: classifying {len(todo)} Threads posts")
    system_prompt = gf.SYSTEM_PROMPT + gf._fetch_feedback_examples()
    for i in range(0, len(todo), gf.BATCH_SIZE):
        batch = todo[i:i + gf.BATCH_SIZE]
        res = gf.classify_batch(batch, api_key, system_prompt)
        for p in batch:
            cache[p["id"]] = res.get(p["id"], {})
        gf.save_cache(cache)

    for p in posts:
        if p.get("drop"):
            continue
        g = cache.get(p["id"], {})
        if not g:
            continue
        p["grok_done"] = True
        if g.get("is_paid_promo") or g.get("is_spam_or_ad") or (g.get("is_almaty") is False) or (g.get("relevant") is False):
            p["drop"] = True
            continue
        if g.get("category") in gf.CAT_CANON:
            p["category"] = g["category"]
        if g.get("severity"):
            p["severity"] = int(g["severity"])
        if g.get("sentiment"):
            p["sentiment"] = g["sentiment"]
        if g.get("district"):
            p["district"] = g["district"]
        if g.get("theme"):
            p["theme"] = g["theme"]
        if g.get("summary"):
            p["summary"] = g["summary"]
        p["is_complaint"] = bool(g.get("is_complaint", p.get("is_complaint")))
    kept = sum(1 for p in posts if p.get("grok_done") and not p.get("drop"))
    dropped = sum(1 for p in posts if p.get("drop"))
    log.info(f"Live Grok: verified {kept}, dropped {dropped}")
    return posts


# ── Загрузка данных ──────────────────────────────────────────────────────────

def load_threads(path: Path) -> list:
    if not path.exists():
        log.warning(f"Threads file not found: {path}")
        return []
    try:
        posts = json.loads(path.read_text(encoding="utf-8"))
        log.info(f"Threads posts loaded: {len(posts)}  ({path.name})")
        return posts
    except Exception as e:
        log.error(f"Failed to load Threads data: {e}")
        return []


def load_meta() -> list:
    if not META_CLEAN.exists():
        log.warning("meta_clean.json not found — will use Threads-only data")
        return []
    try:
        posts = json.loads(META_CLEAN.read_text(encoding="utf-8"))
        log.info(f"Meta posts loaded: {len(posts)}")
        return posts
    except Exception as e:
        log.error(f"Failed to load meta_clean.json: {e}")
        return []


# ── Мёрж ────────────────────────────────────────────────────────────────────

def merge(meta_posts: list, threads_posts: list) -> list:
    converted = apply_live_grok([threads_to_meta(p) for p in threads_posts])

    # Дедупликация по id: Threads перезаписывает если уже есть
    by_id = {p["id"]: p for p in meta_posts}
    for p in converted:
        by_id[p["id"]] = p

    result = list(by_id.values())
    log.info(f"Merged: {len(result)} posts total ({len(meta_posts)} Meta + {len(converted)} Threads)")
    return result


# ── Билд дашборда ────────────────────────────────────────────────────────────

def build_dashboard(merged_posts: list) -> bool:
    # Пишем мёрженные данные в временный файл
    LIVE_MERGE.parent.mkdir(exist_ok=True)
    LIVE_MERGE.write_text(json.dumps(merged_posts, ensure_ascii=False), encoding="utf-8")
    log.info(f"Live merged data written: {LIVE_MERGE}")

    # Персистим мёрж обратно в META_CLEAN — иначе он никогда не растёт между
    # запусками (каждый следующий прогон читал бы ту же исходную базу и терял
    # накопленные Threads-посты прошлых часов).
    META_CLEAN.write_text(json.dumps(merged_posts, ensure_ascii=False), encoding="utf-8")
    log.info(f"Base corpus updated: {META_CLEAN} ({len(merged_posts)} posts)")

    try:
        import build_dashboard as bd
        # Патчим путь к данным — используем live-мёрж вместо meta_clean.json
        bd.CLEAN = LIVE_MERGE
        bd.main()
        log.info("Dashboard built: public/index.html")
        return True
    except Exception as e:
        log.error(f"Dashboard build failed: {e}")
        return False


# ── Деплой на Vercel ─────────────────────────────────────────────────────────

def deploy_vercel() -> bool:
    token = os.getenv("VERCEL_TOKEN", "")
    scope = os.getenv("VERCEL_SCOPE", "")
    pub   = HERE / "public"

    if not (pub / "index.html").exists():
        log.error("public/index.html not found — skipping deploy")
        return False

    # На Windows «npx» — это npx.cmd; subprocess без shell его не находит (WinError 2).
    # Запускаем через cmd /c, чтобы cmd.exe сам нашёл npx в PATH.
    base = ["cmd", "/c", "npx"] if sys.platform == "win32" else ["npx"]
    cmd = base + ["--yes", "vercel@latest", "deploy", "--prod", "--yes"]
    if token: cmd += ["--token", token]
    if scope: cmd += ["--scope", scope]

    log.info(f"Deploying to Vercel...")
    try:
        result = subprocess.run(
            cmd, cwd=str(pub),
            capture_output=True, text=True, timeout=180
        )
        if result.returncode == 0:
            # Вытащить URL из вывода
            url = next(
                (line.strip() for line in result.stdout.splitlines() if "vercel.app" in line or "https://" in line),
                "deployed"
            )
            log.info(f"Vercel deploy OK: {url}")
            return True
        else:
            # У Vercel CLI сама ошибка часто уходит в stdout, а не в stderr —
            # раньше логировали только куцый stderr[:500] и реальную причину
            # никогда не было видно (только шум от npm-варнингов/баннера CLI).
            log.error(f"Vercel deploy failed (exit {result.returncode}):")
            log.error(f"stdout:\n{result.stdout[-2000:]}")
            log.error(f"stderr:\n{result.stderr[-2000:]}")
            return False
    except subprocess.TimeoutExpired:
        log.error("Vercel deploy timed out (120s)")
        return False
    except Exception as e:
        log.error(f"Vercel deploy error: {e}")
        return False


# ── Точка входа ─────────────────────────────────────────────────────────────

def main():
    threads_path = Path(sys.argv[1]) if len(sys.argv) > 1 else THREADS_LIVE

    log.info("=" * 50)
    log.info(f"LIVE DEPLOY  |  {datetime.now().strftime('%H:%M:%S')}")
    log.info(f"Threads src  : {threads_path.name}")
    log.info("=" * 50)

    threads_posts = load_threads(threads_path)
    if not threads_posts:
        log.warning("No Threads data — nothing to deploy")
        return

    meta_posts   = load_meta()
    merged       = merge(meta_posts, threads_posts)

    if not build_dashboard(merged):
        sys.exit(1)

    if not deploy_vercel():
        sys.exit(1)  # иначе GH Actions отчитывается "success" при молча упавшем деплое

    log.info("Done.")


if __name__ == "__main__":
    main()
