#!/usr/bin/env python3
"""
citizen_voice.py — «Мнение жителей»: тянет реплаи к ТОП-N резонансным постам Threads
и прогоняет их через comment_insights (фильтр + локальный ИИ → предложения/саммари).

Изолированный пилот: НЕ трогает основной пайплайн/дашборд. Переиспользует авторизацию
и DOM-экстрактор из almaty_monitor. Ходит только к топ-N постам (мало запросов → низкий
риск бана), с задержками и проверкой на login-challenge.

Запуск:  python citizen_voice.py            # топ-8 постов
         python citizen_voice.py 5          # топ-5
Результат: output/citizen_voice.json
"""
import sys, os, json, time, random
from pathlib import Path
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.sync_api import sync_playwright
import almaty_monitor as am
import comment_insights as ci

HERE = Path(__file__).parent
OUT = HERE / "output" / "citizen_voice.json"
# берём ОЧИЩЕННЫЙ корпус (ИИ-классификация + отсев рекламы), fallback — сырой
_SRC_CANDIDATES = [HERE / "data" / "meta_clean_live.json",
                   HERE / "data" / "meta_clean.json",
                   HERE / "output" / "threads_live.json"]

TOP_N        = int(sys.argv[1]) if len(sys.argv) > 1 else 10
RECENT_DAYS  = 2       # «за сутки»: свежие посты в приоритет (покрыть секцию «Самые обсуждаемые»)
SCROLLS      = 4       # прокруток на страницу поста (подгрузить реплаи)
MAX_REPLIES  = 80      # сколько реплаев максимум брать с поста
MIN_REPLIES  = 3       # меньше — нет смысла суммировать
PER_POST_DELAY = (6, 11)  # пауза между постами, сек (вежливо к Threads)


def _n(p, *keys):
    for k in keys:
        if p.get(k) is not None:
            return p.get(k) or 0
    return 0

def replies_of(p):
    return _n(p, "comments", "reply_count")

def engagement(p):
    l, c, s = _n(p, "likes", "like_count"), replies_of(p), _n(p, "shares", "repost_count")
    if l > 3_000_000 or c > 1_000_000 or s > 1_000_000:  # фантомные метрики — пропускаем
        return -1
    return l + c + s

def _recent_days(p):
    try:
        d = datetime.fromisoformat((p.get("created_at") or "").replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - d).days
    except Exception:
        return 999

def is_civic(p):
    cat = (p.get("category") or "")
    if cat in ("", "Прочее"):
        return False
    if p.get("drop"):
        return False
    plat = p.get("platform")
    if plat and plat != "Threads":   # реплаи тянем только с Threads
        return False
    return True


def looks_like_login(page) -> bool:
    try:
        if "/login" in (page.url or ""):
            return True
        if page.locator('input[name="username"], input[autocomplete="username"]').count() > 0:
            return True
    except Exception:
        pass
    return False


def scrape_replies(page, url, main_text):
    """Открывает страницу поста, подгружает и извлекает реплаи (без самого поста)."""
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2500)
    if looks_like_login(page):
        raise RuntimeError("login-challenge — Threads просит вход, останавливаюсь")
    for _ in range(SCROLLS):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2200)
    items = am.extract_posts_from_page(page)  # тот же EXTRACT_JS
    mainkey = " ".join((main_text or "").lower().split())[:50]
    replies, seen = [], set()
    for it in items:
        t = (it.get("text") or "").strip()
        if not t:
            continue
        k = " ".join(t.lower().split())[:50]
        if k == mainkey:      # это сам пост, а не реплай
            continue
        if k in seen:
            continue
        seen.add(k)
        replies.append({"username": it.get("username", ""), "text": t})
        if len(replies) >= MAX_REPLIES:
            break
    return replies


def main():
    src = next((s for s in _SRC_CANDIDATES if s.exists()), None)
    if not src:
        print("Нет исходных данных (meta_clean_live.json / threads_live.json).")
        return
    posts = json.loads(src.read_text(encoding="utf-8"))
    # гражданские посты Threads с реплаями и без фантомных метрик
    cand = [p for p in posts if is_civic(p) and p.get("url")
            and replies_of(p) >= MIN_REPLIES and engagement(p) > 0]
    # два ведра: СВЕЖИЕ (за RECENT_DAYS — для «Самые обсуждаемые за сутки») + резонансные за всё время
    recent = sorted([p for p in cand if _recent_days(p) <= RECENT_DAYS], key=engagement, reverse=True)
    allt   = sorted(cand, key=engagement, reverse=True)
    seen, targets = set(), []
    for p in recent + allt:            # свежие в приоритете, затем резонансные
        i = p.get("id")
        if i in seen:
            continue
        seen.add(i); targets.append(p)
        if len(targets) >= TOP_N:
            break
    print(f"Источник: {src.name} · всего {len(posts)} · кандидатов с реплаями: {len(cand)} "
          f"(свежих ≤{RECENT_DAYS}д: {len(recent)}) · беру топ-{len(targets)}")

    candidates = [
        am.CHROME,
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    exe = next((p for p in candidates if p and os.path.exists(p)), None)
    launch_kwargs = dict(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"])
    if exe:
        launch_kwargs["executable_path"] = exe

    results = []
    with sync_playwright() as pw:
        browser, ctx = am._build_context(pw, launch_kwargs)
        page = ctx.new_page()
        try:
            page.goto(f"{am.BASE}/", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)
        except Exception:
            pass

        for i, p in enumerate(targets, 1):
            try:
                print(f"[{i}/{len(targets)}] {engagement(p)} вовл. · {p['url']}")
                replies = scrape_replies(page, p["url"], p.get("text", ""))
                print(f"    реплаев собрано: {len(replies)}")
                if len(replies) < MIN_REPLIES:
                    continue
                voice = ci.insights(p.get("text", ""), replies)
                results.append({
                    "post_id": p.get("id"), "url": p["url"],
                    "post_text": p.get("text", "")[:400], "category": p.get("category", ""),
                    "engagement": engagement(p), "replies_total": len(replies),
                    "kept": voice["kept"], "dropped": voice["dropped"],
                    "insights": voice["insights"],
                })
                print(f"    ✓ саммари готово (осталось после фильтра: {voice['kept']})")
            except RuntimeError as e:
                print("    ⚠", e, "— прекращаю обход (риск бана).")
                break
            except Exception as e:
                print(f"    ⚠ пропуск поста: {e}")
            time.sleep(random.uniform(*PER_POST_DELAY))

        browser.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nГотово: {len(results)} постов с «мнением жителей» → {OUT}")

    # Сводим все предложения в ТОП городских решений (один вызов модели)
    all_sugg = []
    for r in results:
        all_sugg += [s for s in (r["insights"].get("suggestions") or []) if isinstance(s, str)]
    tops = ci.synthesize_top_solutions(all_sugg) if all_sugg else []
    TOPS = HERE / "output" / "top_solutions.json"
    TOPS.write_text(json.dumps(tops, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Топ решений для города: {len(tops)} → {TOPS}")


if __name__ == "__main__":
    main()
