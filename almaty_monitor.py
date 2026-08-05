#!/usr/bin/env python3
"""
almaty_monitor.py  —  Мониторинг Threads (threads.com) по теме г. Алматы.
Период по умолчанию: с начала 2026 года по текущий запуск.
Извлекает данные из DOM (браузерная автоматизация через Playwright).
Исключает: мусор (реклама, недвижка, вакансии), ботов.
Оставляет только: жалобы, проблемы, возмущения (через регулярки).
Экспорт: CSV + JSON в папку output/.
"""

import os
import re
import sys
import json
import time
import logging
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

# ── Период ────────────────────────────────────────────────────────────────────
START_DATE = datetime(2026, 1, 1, tzinfo=timezone.utc)
END_DATE   = datetime.now(timezone.utc)

# ── Цель по числу постов ──────────────────────────────────────────────────────
# Настраивается через .env: THREADS_TARGET (для быстрых авто-циклов ставь меньше).
TARGET_POSTS = int(os.getenv("THREADS_TARGET", "2500"))
SEARCH_SCROLL_LIMIT = int(os.getenv("THREADS_SCROLL_SEARCH", "140"))
TAG_SCROLL_LIMIT = int(os.getenv("THREADS_SCROLL_TAG", "150"))

# ── Хэштеги ───────────────────────────────────────────────────────────────────
ALMATY_TAGS = [
    "алматы", "almaty", "алмата",
    "алматы_новости", "алматы_события", "алматы_жизнь",
    "алматыбезцензуры", "almaty_city", "алматы2026",
    "алматыкультура", "алматыспорт", "алматыафиша",
    "казахстаналматы", "almatykz", "almatycity", "алматыкз",
    "алматыпробки", "алматытранспорт", "алматыэкология",
    "алматыжкх", "алматыдороги", "алматыпроблемы", "almaty_kazakhstan",
]

# ── Ключевые слова для поиска по тексту постов ────────────────────────────────
ALMATY_KEYWORDS = [
    "алматы",
    "almaty",
    "алмата",
    "алматы новости",
    "алматы события",
    "алматы проблемы",
    "алматы город",
    "алматы транспорт",
    "алматы экология",
    "алматы культура",
    "алматы спорт",
    "алматы медицина",
    "алматы политика",
    "алматы бизнес",
    "алматы образование",
    "алматы происшествия",
    "алматы криминал",
    "алматы строительство",
    "алматы туризм",
    "almaty kazakhstan",
    "almaty city",
    "алматы 2026",
    "алматы пробки",
    "алматы дороги",
    "алматы вода",
    "алматы свет",
    "алматы мусор",
    "алматы воздух",
    "алматы аким",
    "алматы жкх",
    "акимат алматы",
    "open almaty",
]

# ── Мусор (Реклама, Недвижимость, Вакансии, Услуги) ───────────────────────────
JUNK_PATTERNS = [
    # Классическая реклама
    r'\bреклам[аеуи]?\b', r'\bспонсор\b', r'\bпартнер[ыа]?\b',
    r'#реклама', r'#ad\b', r'#sponsored', r'#промо', 
    r'\bпромокод\b', r'\bскидк[аиу]\b', r'\bраспродаж', r'\bакци[яию]\b',
    # Недвижимость
    r'\bпродам\b', r'\bсдам\b', r'\bсниму\b', r'\bаренда\b', 
    r'\bквартир[ауеы]\b', r'\bжк\b', r'\bэтаж\b', r'\bм2\b', r'\bквадратных метров\b',
    # Вакансии и поиск
    r'\bищем\b', r'\bваканси[яи]\b', r'\bтребуется\b', r'\bмобилограф', r'\bвидеограф',
    # Коммерция и услуги
    r'\bмалый бизнес\b', r'\bпрайс\b', r'\bдоставка\b', r'\bв наличии\b', r'\bзапись открыта\b'
]

# ── Маркеры жалоб и обращений ─────────────────────────────────────────────────
COMPLAINT_PATTERNS = [
    r'жалоб', r'проблем', r'почему', r'досаев', r'акимат', r'когда сделают',
    r'нет воды', r'нет света', r'отключили', r'ямы', r'пробки', r'мусор',
    r'беспредел', r'обратите внимание', r'требуем', r'невозможно', r'ужас',
    r'воняет', r'дышать нечем', r'помогите', r'бардак'
]

# ── Боты ──────────────────────────────────────────────────────────────────────
BOT_USERNAME_RE = [
    re.compile(r'^[a-z]{1,3}\d{7,}$', re.I),
    re.compile(r'^(user|bot|account|profile)\d+$', re.I),
    re.compile(r'^\d{8,}$'),
]

# ── Категории ─────────────────────────────────────────────────────────────────
CATEGORIES = [
    # Безопасность/происшествия — до Экологии (чтобы суицид/буллинг не попал в "воздух")
    ("Происшествия",    ["авари", "пожар", "ДТП", "криминал", "полиц", "задержан", "арест",
                         "суицид", "самоубийств", "буллинг", "кибербуллинг", "травля",
                         "суицид", "өзін-өзі өлтір", "өлімге", "трагед"]),
    ("Новости",         ["новост", "сообщ", "произошло", "случилось"]),
    ("Культура",        ["культур", "театр", "концерт", "выставк", "кино", "фильм", "музей"]),
    ("Спорт",           ["спорт", "футбол", "хоккей", "теннис", "матч", "турнир", "чемпионат"]),
    ("Транспорт",       ["транспорт", "автобус", "метро", "троллейбус", "дорог", "пробк", "BRT"]),
    # Образование — до Экологии; добавлены казахские слова (мектеп = школа, оқушы = ученик)
    ("Образование",     ["образовани", "школ", "мектеп", "универ", "студент", "оқушы",
                         "жатақхана", "ЕНТ", "ЖОО", "колледж", "институт", "вуз"]),
    # Экология — после Образования (чтобы "воздух" не перехватывал школьные темы)
    ("Экология",        ["экологи", "загрязнени", "воздух", "смог", "мусор", "зелен", "парк"]),
    ("Строительство",   ["строительств", "новострой", "ЖК", "снос", "реконструкц"]),
    ("Медицина",        ["медицин", "здоровь", "больниц", "врач", "клиник",
                         "психолог", "психиатр", "ментальн"]),
    ("Политика",        ["политик", "акимат", "аким", "депутат", "закон", "выбор"]),
    ("Бизнес",          ["бизнес", "стартап", "инвестиц", "экономик", "рынок"]),
    ("Еда",             ["ресторан", "кафе", "еда", "кухня", "меню", "кофейн"]),
    ("Туризм",          ["туризм", "путешест", "отдых", "достопримечательн", "гостиниц"]),
    ("Технологии",      ["технологи", "IT", "ИИ", "программист", "цифровизац"]),
    ("Развлечения",     ["развлечени", "клуб", "мероприяти", "праздник", "вечеринк"]),
    ("Общество",        ["общество", "жители", "горожане", "петиция", "волонтер"]),
]

_junk_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in JUNK_PATTERNS]
_complaint_re = [re.compile(p, re.IGNORECASE | re.UNICODE) for p in COMPLAINT_PATTERNS]
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


def is_junk(text: str) -> bool:
    return any(rx.search(text) for rx in _junk_re)


def is_complaint(text: str) -> bool:
    return any(rx.search(text) for rx in _complaint_re)


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


# ── DOM-парсинг страницы тега ─────────────────────────────────────────────────
EXTRACT_JS = r"""() => {
    const posts = [];
    const containers = document.querySelectorAll('[data-pressable-container]');

    // Парсер компактных чисел Threads: "1.2K", "1,2 тыс.", "3млн", "245"
    const parseNum = (s) => {
        if (s == null) return null;
        let t = String(s).trim().toLowerCase().replace(/\s+/g, '');
        if (!/^[\d.,]+(k|к|m|м|тыс|млн)?\.?$/.test(t)) return null;
        const hasUnit = /(k|к|m|м|тыс|млн)/.test(t);
        let mult = 1;
        if (/(^|[\d])(k|к|тыс)/.test(t)) mult = 1000;
        if (/(^|[\d])(m|м|млн)/.test(t)) mult = 1000000;
        const num = parseFloat(t.replace(',', '.').replace(/[^\d.]/g, ''));
        if (isNaN(num)) return null;
        // Без суффикса Threads всегда показывает голое число < 100 000 (иначе сокращает до "K"/"M").
        // Более длинные "голые" числа — не счётчики (обрывки ID/дат/текста), это шум — отбрасываем.
        if (!hasUnit && num >= 100000) return null;
        return Math.round(num * mult);
    };
    const isCount = (s) => parseNum(s) !== null;

    containers.forEach(c => {
        const timeEl = c.querySelector('time[datetime]');
        if (!timeEl) return;

        const datetime = timeEl.getAttribute('datetime') || '';
        const innerLines = c.innerText.split('\n').map(l => l.trim()).filter(l => l.length > 0);

        const username = innerLines[0] || '';
        const timeText = timeEl.innerText || '';
        const textLines = [];
        let pastTime = false;

        for (let i = 1; i < innerLines.length; i++) {
            const line = innerLines[i];
            if (!pastTime && (line === timeText || /^\d{2}\.\d{2}\.\d{4}$/.test(line) || /^\d+\s*(дн|ч|мин|нед|мес|сек|д|h|m|s|w)/.test(line))) {
                pastTime = true;
                continue;
            }
            if (pastTime) textLines.push(line);
        }

        // ── ИСПРАВЛЕНИЕ ФАНТОМНЫХ МЕТРИК ───────────────────────────────────
        // Счётчики (лайки/ответы/репосты/шер) — это ХВОСТОВОЙ блок чисел внизу
        // карточки (панель действий), а НЕ числа из тела поста. Берём только
        // подряд идущие числовые строки с конца контейнера.
        const trailing = [];
        for (let i = innerLines.length - 1; i >= 0; i--) {
            if (isCount(innerLines[i])) trailing.unshift(parseNum(innerLines[i]));
            else break;
        }
        // Эти же хвостовые числа убираем из текста, чтобы они туда не попали.
        let cut = textLines.length;
        while (cut > 0 && isCount(textLines[cut - 1])) cut--;
        const text = textLines.slice(0, cut).join(' ').trim();

        // Лайки дополнительно подтверждаем через aria-label кнопки «Нравится».
        const likes   = ariaLikes(c, parseNum) ?? trailing[0] ?? 0;
        const replies = trailing[1] ?? 0;
        const reposts = trailing[2] ?? 0;

        const postLinks = Array.from(c.querySelectorAll('a[href*="/post/"]')).map(a => a.href);
        const userLinks = Array.from(c.querySelectorAll('a[href*="/@"]')).map(a => a.href);

        posts.push({
            username: username,
            text: text,
            datetime: datetime,
            likes: likes || 0,
            replies: replies || 0,
            reposts: reposts || 0,
            post_url: postLinks[0] || '',
            user_url: userLinks[0] || '',
        });
    });

    function ariaLikes(c, parseNum) {
        const el = Array.from(c.querySelectorAll('[aria-label]'))
            .find(e => /нрав|like|лайк/i.test(e.getAttribute('aria-label') || ''));
        if (!el) return null;
        const m = (el.getAttribute('aria-label') || '').match(/([\d.,]+\s*(?:k|к|m|м|тыс|млн)?)/i);
        return m ? parseNum(m[1]) : null;
    }

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

    # Отсекаем ботов
    if is_bot(username, text):
        stats["bot"] += 1
        collected[uid] = None
        return False

    # Отсекаем явную рекламу/недвижку (грубый пред-фильтр для экономии вызовов Grok).
    # Тонкую релевантность («городская проблема Алматы или нет») решает уже Grok
    # на этапе grok_filter.py — поэтому жёсткий гейт is_complaint здесь убран.
    if is_junk(text):
        stats["junk"] += 1
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


def scrape_search(page: Page, keyword: str, collected: dict, stats: dict,
                  scroll_limit: int = SEARCH_SCROLL_LIMIT, click_recent: bool = True):
    from urllib.parse import quote
    url = f"{BASE}/search?q={quote(keyword)}&serp_type=default"
    log.info(f"[поиск] «{keyword}» → {url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        if click_recent:
            click_recent_tab(page)
            page.wait_for_timeout(3000)
    except Exception as e:
        log.warning(f"  [поиск «{keyword}»] Ошибка загрузки: {e}")
        return

    prev_count = 0
    stale_scrolls = 0
    for scroll_n in range(scroll_limit):
        try:
            posts_raw = extract_posts_from_page(page)
        except Exception as e:
            log.warning(f"  [поиск «{keyword}»] Браузер упал на прокрутке {scroll_n+1}: {e}")
            raise

        added = 0
        old_seen = 0
        for p in posts_raw:
            dt = parse_dt(p.get("datetime", ""))
            if dt and dt < START_DATE:
                old_seen += 1
            if process_raw_post(p, source=f"поиск:{keyword}", collected=collected, stats=stats):
                added += 1

        if (scroll_n + 1) % 10 == 0:
            clean = len([v for v in collected.values() if v is not None])
            log.info(f"  [поиск «{keyword}»] Прокрутка {scroll_n+1} | +{added} | итого: {clean}")

        # Дата-стоп надёжен только в хронологическом режиме (вкладка Recent),
        # где посты монотонно стареют. В TOP (по охвату) старые посты идут вперемешку —
        # их просто фильтруем, но скролл НЕ обрываем, чтобы добрать максимум за год.
        if click_recent and old_seen:
            log.info(f"  [поиск «{keyword}»] Достигли постов до {START_DATE.date()}")
            break

        # «Нет роста» — стоп только после нескольких пустых прокруток подряд
        if len(posts_raw) == prev_count:
            stale_scrolls += 1
            if stale_scrolls >= 6 and scroll_n > 8:
                log.info(f"  [поиск «{keyword}»] Новых постов нет {stale_scrolls} прокрутки подряд, стоп")
                break
        else:
            stale_scrolls = 0
        prev_count = len(posts_raw)

        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2800)
        except Exception as e:
            log.warning(f"  [поиск «{keyword}»] Браузер упал на прокрутке {scroll_n+1}: {e}")
            raise

    clean = len([v for v in collected.values() if v is not None])
    log.info(f"  [поиск «{keyword}»] Завершено. Чистых постов всего: {clean}")


def scrape_tag(page: Page, tag: str, collected: dict, stats: dict, scroll_limit: int = TAG_SCROLL_LIMIT):
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
    stale_scrolls = 0
    for scroll_n in range(scroll_limit):
        try:
            posts_raw = extract_posts_from_page(page)
        except Exception as e:
            log.warning(f"  [#{tag}] Браузер упал на прокрутке {scroll_n+1}: {e}")
            raise

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
        if len(posts_raw) == prev_count:
            stale_scrolls += 1
            if stale_scrolls >= 5 and scroll_n > 8:
                log.info(f"  [#{tag}] Новых постов нет {stale_scrolls} прокруток подряд, стоп")
                break
        else:
            stale_scrolls = 0
        prev_count = len(posts_raw)

        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2800)
        except Exception as e:
            log.warning(f"  [#{tag}] Браузер упал на прокрутке {scroll_n+1}: {e}")
            raise

    final = len([v for v in collected.values() if v is not None])
    log.info(f"  [#{tag}] Завершено. Чистых постов всего: {final}")


STATE_FILE = Path(__file__).parent / "auth_state.json"


def _build_context(pw, launch_kwargs: dict):
    """Создаёт браузерный контекст: сначала из auth_state.json, потом из .env THREADS_COOKIE."""
    browser = pw.chromium.launch(**launch_kwargs)

    if STATE_FILE.exists():
        log.info(f"Авторизация: auth_state.json ({STATE_FILE})")
        ctx = browser.new_context(
            storage_state=str(STATE_FILE),
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Asia/Almaty",
        )
        return browser, ctx

    cookie_str = os.getenv("THREADS_COOKIE", "").strip()
    if cookie_str:
        log.info("Авторизация: THREADS_COOKIE из .env")
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Asia/Almaty",
        )
        ctx.add_cookies(build_cookies(cookie_str))
        return browser, ctx

    raise RuntimeError(
        "Нет авторизации: запусти threads_login.py или задай THREADS_COOKIE в .env"
    )


def run_scraper() -> List[dict]:
    collected: Dict[str, Optional[dict]] = {}

    # Статистика с учетом регулярных выражений
    stats = {"kept": 0, "junk": 0, "bot": 0, "out_of_range": 0, "not_complaint": 0}

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
        browser, ctx = _build_context(pw, launch_kwargs)
        page = ctx.new_page()

        try:
            page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)
            log.info("Сессия активирована")
        except Exception as e:
            log.warning(f"Прогрев: {e}")

        def clean_count():
            return len([v for v in collected.values() if v is not None])

        # ── Фаза 1: ПОИСК по ключевым словам — ловит посты БЕЗ хэштегов
        # (любой текст со словом «Алматы»), это основная масса обычных горожан.
        log.info(f"\n--- Фаза 1: Поиск по ключевым словам ({len(ALMATY_KEYWORDS)}) — посты без хэштегов ---")
        for keyword in ALMATY_KEYWORDS:
            scrape_search(page, keyword, collected, stats)
            time.sleep(2)
            if clean_count() >= TARGET_POSTS:
                log.info(f"Достигнута цель {TARGET_POSTS} постов — останавливаю сбор.")
                break

        # ── Фаза 2: ХЭШТЕГИ — добираем тематические посты
        if clean_count() < TARGET_POSTS:
            log.info(f"\n--- Фаза 2: Хэштеги ({len(ALMATY_TAGS)}) ---")
            for tag in ALMATY_TAGS:
                scrape_tag(page, tag, collected, stats)
                time.sleep(2)
                if clean_count() >= TARGET_POSTS:
                    log.info(f"Достигнута цель {TARGET_POSTS} постов — останавливаю сбор.")
                    break

        browser.close()

    results = [v for v in collected.values() if v is not None]

    log.info("\n=== Итоговая статистика ===")
    log.info(f"Чистых жалоб:    {stats['kept']}")
    log.info(f"Мусор/Реклама:   {stats['junk']}")
    log.info(f"Не жалобы:       {stats['not_complaint']}")
    log.info(f"Боты:            {stats['bot']}")
    log.info(f"Вне периода:     {stats['out_of_range']}")
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
    log.info(f"Мониторинг Алматы (Фильтр жалоб) | {START_DATE.date()} → {END_DATE.date()}")
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
