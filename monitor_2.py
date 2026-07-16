#!/usr/bin/env python3
"""
almaty_monitor_llm.py  —  Мониторинг Threads (threads.com) по теме г. Алматы.
Период: 2026-01-01 — 2026-06-03.
Извлекает данные из DOM (браузерная автоматизация через Playwright).
Фильтрация: локальная LLM Qwen3.5 (отсекает мусор, оставляет только жалобы).
Экспорт: CSV + JSON в папку output/.
"""

import os
import re
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import unquote

import pandas as pd
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page

# ── UTF-8 вывод ───────────────────────────────────────────────────────────────
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

# ── Настройки LLM ─────────────────────────────────────────────────────────────
LLM_BASE_URL = "http://10.100.200.199:2000/v1"
LLM_MODEL    = "/home/cda/models/Qwen3.5-35B-A3B-FP8"
LLM_API_KEY  = "dummy"

SYSTEM_PROMPT_EN = """
You are a strict urban data analyst filtering social media posts for Almaty city monitoring.
Your task is to classify whether a given text is a valid citizen complaint or an urban problem.

ACCEPT (is_complaint: true) IF the text contains:
- Infrastructure issues (no water, power outages, potholes, broken traffic lights).
- Transport and traffic (severe traffic jams, bad public transport, accidents).
- Ecology and sanitation (smog, bad air quality, uncollected garbage, dirt).
- Social and administrative problems (crime, municipal negligence, appeals to Akimat or Dosayev).
- Explicit complaints, indignation, or requests for help regarding city life.

REJECT (is_complaint: false) IF the text contains:
- Real estate (buying, selling, renting apartments, searching for roommates).
- Job postings or searching for services (e.g., looking for a videographer, promoting a small business).
- Commercial spam, discounts, promotions, or pricing.
- Generic news, event announcements, or beautiful photos of the city without a stated problem.
- Irrelevant content.

Respond STRICTLY in JSON format with no markdown formatting or extra text:
{"is_complaint": true/false, "reason": "short explanation in Russian"}
"""

# ── Период ────────────────────────────────────────────────────────────────────
START_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)
END_DATE   = datetime(2026, 6, 3, 23, 59, 59, tzinfo=timezone.utc)

# ── Хэштеги ───────────────────────────────────────────────────────────────────
ALMATY_TAGS = [
    "алматы", "almaty", "алмата",
    "алматы_новости", "алматы_события", "алматы_жизнь",
    "алматыбезцензуры", "almaty_city", "алматы2026",
    "алматыкультура", "алматыспорт", "алматыафиша",
    "казахстаналматы",
]

# ── Ключевые слова для поиска по тексту постов ────────────────────────────────
ALMATY_KEYWORDS = [
    "алматы",
    "almaty",
    "алмата",
    "алматы новости",
    "алматы проблемы",
    "алматы транспорт",
    "алматы экология",
    "алматы медицина",
    "алматы политика",
    "алматы происшествия",
    "алматы криминал",
    "алматы строительство",
    "almaty city",
]

# ── Быстрый фильтр ботов ──────────────────────────────────────────────────────
BOT_USERNAME_RE = [
    re.compile(r'^[a-z]{1,3}\d{7,}$', re.I),
    re.compile(r'^(user|bot|account|profile)\d+$', re.I),
    re.compile(r'^\d{8,}$'),
]

# ── Категории (оставляем для базовой разметки прошедших постов) ───────────────
CATEGORIES = [
    ("Новости",         ["новост", "сообщ", "произошло", "случилось"]),
    ("Происшествия",    ["авари", "пожар", "ДТП", "криминал", "полиц", "задержан", "арест"]),
    ("Культура",        ["культур", "театр", "концерт", "выставк", "кино", "фильм", "музей"]),
    ("Спорт",           ["спорт", "футбол", "хоккей", "теннис", "матч", "турнир", "чемпионат"]),
    ("Транспорт",       ["транспорт", "автобус", "метро", "троллейбус", "дорог", "пробк", "BRT"]),
    ("Экология",        ["экологи", "загрязнени", "воздух", "смог", "мусор", "зелен", "парк"]),
    ("Строительство",   ["строительств", "новострой", "ЖК", "снос", "реконструкц"]),
    ("Образование",     ["образовани", "школ", "универ", "студент", "ЕНТ"]),
    ("Медицина",        ["медицин", "здоровь", "больниц", "врач", "клиник"]),
    ("Политика",        ["политик", "акимат", "аким", "депутат", "закон", "выбор"]),
    ("Бизнес",          ["бизнес", "стартап", "инвестиц", "экономик", "рынок"]),
    ("Еда",             ["ресторан", "кафе", "еда", "кухня", "меню", "кофейн"]),
    ("Туризм",          ["туризм", "путешест", "отдых", "достопримечательн", "гостиниц"]),
    ("Технологии",      ["технологи", "IT", "ИИ", "программист", "цифровизац"]),
    ("Развлечения",     ["развлечени", "клуб", "мероприяти", "праздник", "вечеринк"]),
    ("Общество",        ["общество", "жители", "горожане", "петиция", "волонтер"]),
]

_cat_re = [(lbl, [re.compile(kw, re.IGNORECASE) for kw in kws]) for lbl, kws in CATEGORIES]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE   = "https://www.threads.com"


# ── Вспомогательные функции ───────────────────────────────────────────────────
def build_cookies(s: str) -> List[dict]:
    cookies = []
    for part in s.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        name, _, value = part.partition("=")
        for domain in [".threads.com", ".threads.net"]:
            cookies.append({
                "name": name.strip(),
                "value": unquote(value.strip()),
                "domain": domain,
                "path": "/",
            })
    return cookies


def parse_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def in_range(dt: Optional[datetime]) -> bool:
    return dt is not None and START_DATE <= dt <= END_DATE


def is_bot(username: str, text: str) -> bool:
    if any(rx.match(username) for rx in BOT_USERNAME_RE):
        return True
    if len(re.findall(r"#\w+", text)) > 15:
        return True
    return False


def classify(text: str) -> str:
    for label, patterns in _cat_re:
        if any(rx.search(text) for rx in patterns):
            return label
    return "Прочее"


def check_post_with_llm(text: str) -> bool:
    """
    Отправляет текст в локальную LLM. Возвращает True, если это жалоба, и False во всех остальных случаях.
    """
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_EN},
            {"role": "user", "content": f"Text to analyze:\n{text}"}
        ],
        "temperature": 0.0,
        "max_tokens": 100,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(f"{LLM_BASE_URL}/chat/completions", headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        
        result_text = response.json()["choices"][0]["message"]["content"]
        
        # Очищаем от возможных маркдаун-блоков
        result_text = result_text.strip().removeprefix("```json").removesuffix("```").strip()
        parsed_result = json.loads(result_text)
        
        return bool(parsed_result.get("is_complaint", False))
        
    except Exception as e:
        log.error(f"Ошибка LLM при проверке текста: {e}")
        return False


# ── DOM-парсинг страницы тега ─────────────────────────────────────────────────
EXTRACT_JS = """() => {
    const posts = [];
    const containers = document.querySelectorAll('[data-pressable-container]');
    containers.forEach(c => {
        const timeEl = c.querySelector('time[datetime]');
        if (!timeEl) return;

        const datetime = timeEl.getAttribute('datetime') || '';
        const innerLines = c.innerText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);

        const username = innerLines[0] || '';
        const timeText = timeEl.innerText || '';
        const textLines = [];
        let pastTime = false;
        
        for (let i = 1; i < innerLines.length; i++) {
            const line = innerLines[i];
            if (!pastTime && (line === timeText || /^\\d{2}\\.\\d{2}\\.\\d{4}$/.test(line) || /^\\d+ (дн|ч|мин|нед|мес)/.test(line))) {
                pastTime = true;
                continue;
            }
            if (pastTime) {
                textLines.push(line);
            }
        }

        while (textLines.length > 0 && /^\\d+$/.test(textLines[textLines.length - 1])) {
            textLines.pop();
        }

        const text = textLines.join(' ').trim();
        const nums = innerLines.filter(l => /^\\d+$/.test(l)).map(Number);
        const postLinks = Array.from(c.querySelectorAll('a[href*="/post/"]')).map(a => a.href);
        const userLinks = Array.from(c.querySelectorAll('a[href*="/@"]')).map(a => a.href);

        posts.push({
            username: username,
            text: text,
            datetime: datetime,
            likes: nums[0] || 0,
            replies: nums[1] || 0,
            reposts: nums[2] || 0,
            post_url: postLinks[0] || '',
            user_url: userLinks[0] || '',
        });
    });
    return posts;
}"""


def click_recent_tab(page: Page):
    for sel in [
        'span:has-text("Недавние")',
        'span:has-text("Latest")',
        'span:has-text("Recent")',
        'a:has-text("Недавние")',
        '[role="tab"]:has-text("Недавние")',
    ]:
        try:
            el = page.locator(sel)
            if el.count() > 0:
                el.first.click()
                page.wait_for_timeout(3000)
                log.info(f"  Кликнул 'Recent' через '{sel}'")
                return
        except Exception:
            pass


def extract_posts_from_page(page: Page) -> List[dict]:
    return page.evaluate(EXTRACT_JS)


def process_raw_post(p: dict, source: str, collected: dict, stats: dict) -> bool:
    uid = f"{p['username']}_{p['datetime']}"
    if uid in collected:
        return False

    dt = parse_dt(p["datetime"])

    if dt and dt < START_DATE:
        collected[uid] = None
        return False

    if not in_range(dt):
        stats["out_of_range"] += 1
        collected[uid] = None
        return False

    text = p["text"]
    username = p["username"]

    # Быстрый фильтр: отсекаем ботов по юзернейму
    if is_bot(username, text):
        stats["bot"] += 1
        collected[uid] = None
        return False

    # Медленный фильтр: пропускаем текст через локальную LLM
    if not check_post_with_llm(text):
        stats["not_complaint"] += 1 
        collected[uid] = None
        return False

    collected[uid] = {
        "id": uid,
        "username": username,
        "text": text,
        "category": classify(text),
        "like_count": p.get("likes", 0),
        "reply_count": p.get("replies", 0),
        "repost_count": p.get("reposts", 0),
        "created_at": p["datetime"],
        "url": p.get("post_url", "") or f"{BASE}/@{username}",
        "source": source,
    }
    stats["kept"] += 1
    return True


def scrape_search(page: Page, keyword: str, collected: dict, stats: dict, scroll_limit: int = 50):
    from urllib.parse import quote
    url = f"{BASE}/search?q={quote(keyword)}&serp_type=default"
    log.info(f"[поиск] «{keyword}» → {url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        click_recent_tab(page)
        page.wait_for_timeout(3000)
    except Exception as e:
        log.warning(f"  [поиск «{keyword}»] Ошибка загрузки: {e}")
        return

    prev_count = 0
    for scroll_n in range(scroll_limit):
        posts_raw = extract_posts_from_page(page)

        added = 0
        stop = False
        for p in posts_raw:
            dt = parse_dt(p.get("datetime", ""))
            if dt and dt < START_DATE:
                stop = True
            if process_raw_post(p, source=f"поиск:{keyword}", collected=collected, stats=stats):
                added += 1

        if (scroll_n + 1) % 10 == 0:
            clean = len([v for v in collected.values() if v is not None])
            log.info(f"  [поиск «{keyword}»] Прокрутка {scroll_n+1} | +{added} | итого: {clean}")

        if stop:
            log.info(f"  [поиск «{keyword}»] Достигли постов до {START_DATE.date()}")
            break
        if len(posts_raw) == prev_count and scroll_n > 5:
            log.info(f"  [поиск «{keyword}»] Новых постов нет, стоп")
            break
        prev_count = len(posts_raw)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2500)

    clean = len([v for v in collected.values() if v is not None])
    log.info(f"  [поиск «{keyword}»] Завершено. Чистых постов всего: {clean}")


def scrape_tag(page: Page, tag: str, collected: dict, stats: dict, scroll_limit: int = 60):
    url = f"{BASE}/tag/{tag}"
    log.info(f"[#{tag}] → {url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        click_recent_tab(page)
    except Exception as e:
        log.warning(f"  [#{tag}] Ошибка загрузки: {e}")
        return

    prev_count = 0
    for scroll_n in range(scroll_limit):
        posts_raw = extract_posts_from_page(page)

        added = 0
        stop = False
        for p in posts_raw:
            dt = parse_dt(p.get("datetime", ""))
            if dt and dt < START_DATE:
                stop = True
            if process_raw_post(p, source=f"#{tag}", collected=collected, stats=stats):
                added += 1

        current = len([v for v in collected.values() if v is not None])
        if (scroll_n + 1) % 10 == 0:
            log.info(f"  [#{tag}] Прокрутка {scroll_n+1}/{scroll_limit} | +{added} | итого: {current}")

        if stop:
            log.info(f"  [#{tag}] Достигли постов до {START_DATE.date()}")
            break
        if len(posts_raw) == prev_count and scroll_n > 5:
            log.info(f"  [#{tag}] Новых постов нет, стоп")
            break
        prev_count = len(posts_raw)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2500)

    final = len([v for v in collected.values() if v is not None])
    log.info(f"  [#{tag}] Завершено. Чистых постов всего: {final}")


def run_scraper() -> List[dict]:
    cookie_str = os.getenv("THREADS_COOKIE", "").strip()
    if not cookie_str:
        log.error("THREADS_COOKIE не задан в .env")
        return []

    cookies = build_cookies(cookie_str)
    collected: Dict[str, Optional[dict]] = {}
    
    # Статистика с учетом LLM-фильтрации
    stats = {"kept": 0, "bot": 0, "out_of_range": 0, "not_complaint": 0}

    candidates = [
        CHROME,
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    exe = next((p for p in candidates if os.path.exists(p)), None)
    log.info(f"Браузер: {exe or 'Playwright Chromium (по умолчанию)'}")

    launch_kwargs = dict(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )
    if exe:
        launch_kwargs["executable_path"] = exe

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kwargs)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Asia/Almaty",
        )
        ctx.add_cookies(cookies)
        page = ctx.new_page()

        try:
            page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            log.info("Сессия активирована")
        except Exception as e:
            log.warning(f"Прогрев: {e}")

        log.info(f"\n--- Фаза 1: Хэштеги ({len(ALMATY_TAGS)}) ---")
        for tag in ALMATY_TAGS:
            scrape_tag(page, tag, collected, stats)
            time.sleep(2)

        log.info(f"\n--- Фаза 2: Поиск по ключевым словам ({len(ALMATY_KEYWORDS)}) ---")
        for keyword in ALMATY_KEYWORDS:
            scrape_search(page, keyword, collected, stats)
            time.sleep(2)

        browser.close()

    results = [v for v in collected.values() if v is not None]

    log.info("\n=== Итоговая статистика ===")
    log.info(f"Чистых жалоб (LLM): {stats['kept']}")
    log.info(f"Отбраковано LLM:    {stats['not_complaint']}")
    log.info(f"Боты:               {stats['bot']}")
    log.info(f"Вне периода:        {stats['out_of_range']}")
    log.info("==========================\n")
    return results


def export(results: List[dict], out_dir: Path) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cols = ["id", "username", "text", "category",
            "like_count", "reply_count", "repost_count",
            "created_at", "url", "source"]

    json_path = out_dir / f"almaty_threads_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    csv_path = out_dir / f"almaty_threads_{ts}.csv"
    df = pd.DataFrame(results)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df[cols].to_csv(csv_path, index=False, encoding="utf-8-sig")

    if not df.empty and "category" in df.columns:
        log.info("Категории:")
        for cat, cnt in df["category"].value_counts().items():
            log.info(f"  {cat}: {cnt}")

    return json_path, csv_path


def main():
    log.info(f"Мониторинг Алматы (LLM Qwen Фильтр) | {START_DATE.date()} → {END_DATE.date()}")
    log.info(f"Хэштегов: {len(ALMATY_TAGS)}, ключевых слов: {len(ALMATY_KEYWORDS)}")
    log.info("-" * 50)

    results = run_scraper()
    if not results:
        log.warning("Постов не собрано.")
        return

    out_dir = Path(__file__).parent / "output"
    json_path, csv_path = export(results, out_dir)
    log.info(f"JSON → {json_path}")
    log.info(f"CSV  → {csv_path}")
    log.info(f"Готово! {len(results)} постов.")


if __name__ == "__main__":
    main()