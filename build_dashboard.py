#!/usr/bin/env python3
"""
build_dashboard.py — Сборка публичного дашборда акимата Алматы (Meta: FB + Instagram).

Вход:  data/meta_clean.json   (результат ingest_meta.py; grok_filter.py может обогатить топ-N)
       data/meta_stats.json   (статистика очистки — для блока «Методология»)
Выход: public/index.html      (самодостаточная страница, светлый premium-gov дизайн)

Полный текст постов НЕ обрезается (раскрытие на стороне страницы). Тепловая карта убрана.
Метрики Meta достоверны — санитизация «фантомов» не требуется.
"""

import re as _refix
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

# ── Переклассификация категорий «на лету» ───────────────────────────────────────
# Исправляет ошибки в meta_clean.json БЕЗ повторного запуска ingest_meta.py:
# при каждой сборке дашборда категории пересчитываются по актуальным правилам.
from ingest_meta import (
    ALMATY_CITY_RE as _ALMATY_CITY_RE,
    CAT_RE as _CANON_CAT_RE,   # канонические категории (ru+kk)
    ENTERTAINMENT_RE as _ENTERTAINMENT_RE,
    FOREIGN_PLACE_RE as _FOREIGN_PLACE_RE,
    MUNICIPAL_SERVICE_RE as _MUNICIPAL_SERVICE_RE,
    is_nonlocal_or_media_noise as _is_nonlocal_or_media_noise,
)

_CANON_NAMES = {name for name, _ in _CANON_CAT_RE}

# Ирония/шутки/каламбуры — НЕ городские сигналы (высокоточные маркеры, мало ложных).
# Ловит виральные «приколы» вроде «Чисто теоретически я донор на Сатпаева?».
_IRONY_JOKE_RE = _refix.compile(
    r"чисто\s+(?:теоретическ|гипотетическ|по\s+приколу|по\s+фану)|"
    r"\bтеоретическ\w*\s+я\b|\bгипотетическ\w*\s+(?:я|если)\b|"
    r"ради\s+(?:хайпа|лайков|подписчиков|репостов)|\bпо\s+приколу\b|\bна\s+спор\b|"
    r"если\s+что[,\s]+это\s+(?:шутк|сарказм|стёб|стеб|прикол)|"
    r"это\s+был[аи]?\s+(?:шутк|сарказм)|сарказм\s+если\s+что|"
    r"\bстёб\b|\bстеб\b|\bтроллинг\b|\bшутка\s+юмора\b",
    _refix.I)

# Бытовые наблюдения / шутки про природные явления без городской проблемы:
# «нафига нам рассвет в 3 часа ночи 🤪», «закат в 21:00, ура» и т.п.
# Такие посты набирают охват как мем, а не как городская жалоба — в hot_signals не берём.
_CASUAL_NATURE_RE = _refix.compile(
    r"\bнафига\s+нам\s+(?:рассвет|закат|восход|луна|солнц\w*)\b|"
    r"(?:рассвет|закат|восход\s+солнца)\s+в\s+\d{1,2}\s+час|"
    r"(?:светл|темн|солнечн)\w+\s+(?:уже\s+в|до)\s+\d{1,2}[:\s]\d{0,2}\s*(?:час|ночи|утра)|"
    r"(?:🤪|😂|😜|🙃|😅)[^а-яёa-z]{0,15}(?:алматы|almaty)\s*[.!]?\s*$",
    _refix.I)

# Приоритетные переопределения (срабатывают ДО канонических правил).
# Содержат ТОЛЬКО то, чего нет в каноническом списке (суицид → Безопасность,
# буллинг/школьные ЧП → Образование). Политику/криминал ловит канонический список.
_OVERRIDE_RULES = [
    ("Безопасность и правопорядок", _refix.compile(
        r"свёл счёты|свел счёты|мектеп.*өлім|оқушы.*(?:өлім|қаза)", _refix.I)),
    ("Образование", _refix.compile(
        r"буллинг|кибербуллинг|травл[яею]|"
        r"мектеп.*(?:қысым|зорлық)|оқушы.*мәсел|"
        r"школ\w*.*(?:трагед|давлен|насил|конфликт|избил)|"
        r"студент.*скандал|жатақхана", _refix.I)),
]

_CANON_MAP = dict(_CANON_CAT_RE)

def _canon_classify(text: str) -> str:
    for cat, rx in _CANON_CAT_RE:
        if rx.search(text):
            return cat
    return "Прочее"

def reclassify(p: dict) -> dict:
    """Консервативная коррекция категории: трогаем только явные ошибки,
    остальное оставляем как есть (без массовой перетасовки).
    AI-проверенные посты (grok_done) не меняем вовсе."""
    if p.get("grok_done") and p.get("category"):
        return p
    text = p.get("text", "")
    cur  = p.get("category")

    # 1) Приоритетные переопределения (суицид → Безопасность, буллинг/школа → Образование)
    for cat, rx in _OVERRIDE_RULES:
        if rx.search(text):
            if cur != cat:
                p = dict(p); p["category"] = cat
            return p

    # 2) Баг «электро-»: пост в Электроснабжении, но текст НЕ про электроснабжение
    #    (электромобиль, электротакси, электромотор и т.п.) — переклассифицируем.
    if cur == "Электроснабжение":
        el_rx = _CANON_MAP.get("Электроснабжение")
        if el_rx and not el_rx.search(text):
            new = _canon_classify(text)
            p = dict(p); p["category"] = new
            return p

    # 3) Прочие посты — оставляем категорию как есть (только нормализуем неизвестные имена)
    if cur not in _CANON_NAMES:
        p = dict(p); p["category"] = "Прочее"
    return p


def local_drop_reason(p: dict) -> str:
    """Final safety net for posts already present in cached/merged data."""
    text = p.get("text", "")
    owner = p.get("owner_name") or p.get("owner") or ""
    if p.get("drop"):
        return "marked_drop"
    if _is_nonlocal_or_media_noise(text, owner):
        return "nonlocal_or_media_noise"
    if _FOREIGN_PLACE_RE.search(text) and not _ALMATY_CITY_RE.search(text):
        return "foreign_place"
    if _ENTERTAINMENT_RE.search(text) and not (_ALMATY_CITY_RE.search(text) or _MUNICIPAL_SERVICE_RE.search(text)):
        return "entertainment_offtopic"
    if _IRONY_JOKE_RE.search(text):
        return "irony_joke"
    if _CASUAL_NATURE_RE.search(text) and not _MUNICIPAL_SERVICE_RE.search(text):
        return "casual_nature_joke"
    if _MEDIA_DISCUSSION_RE.search(text):
        return "media_discussion"
    return ""

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
log = logging.getLogger("dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S", stream=sys.stdout)

HERE = Path(__file__).parent
CLEAN = HERE / "data" / "meta_clean.json"
STATS = HERE / "data" / "meta_stats.json"
GEO_CANDIDATES = [HERE.parent / "almaty-districts.geo (3).json", HERE / "almaty-districts.geo.json"]
OUT = HERE / "public" / "index.html"
LIVE_TAIL = HERE / "logs" / "live_tail.json"
HOURLY_STATS = HERE / "logs" / "hourly_stats.json"
ALMATY_TZ = timezone(timedelta(hours=5))

DEPT = {
    "Дороги и транспорт": "Управление городской мобильности",
    "ЖКХ и инфраструктура": "Управление энергетики и ЖКХ",
    "Вода и канализация": "ГКП «Алматы Су» / Управление ЖКХ",
    "Электроснабжение": "АЖК / Управление энергетики",
    "Экология и воздух": "Управление экологии и окружающей среды",
    "Благоустройство и мусор": "ГКП «Алматы Тазалық» / Управление зелёной экономики",
    "Строительство и застройка": "Управление градостроительства",
    "Безопасность и правопорядок": "ДП + ДЧС + пресс-служба",
    "Здравоохранение": "Управление общественного здоровья",
    "Образование": "Управление образования",
    "Госуслуги и бюрократия": "Аппарат акима / ЦОН / Open Almaty",
    "Цены и социальные вопросы": "Управление предпринимательства / соцзащиты",
    "Прочее": "Профильное управление",
}
RECO = {
    "Дороги и транспорт": "Картировать аварийные участки и заторы из обращений, дать публичный график ремонта и разъяснения по маршрутам.",
    "ЖКХ и инфраструктура": "Проверить адресные жалобы по отключениям/прорывам, опубликовать график восстановления.",
    "Вода и канализация": "Проверить адреса перебоев с водой/канализацией, дать сроки устранения.",
    "Электроснабжение": "Сверить жалобы на отключения и перепады с графиком АЖК, опубликовать причины и сроки.",
    "Экология и воздух": "Подготовить разъяснение по качеству воздуха и зелёным зонам, опередить негативную волну.",
    "Благоустройство и мусор": "Отработать адреса по мусору/уборке через Тазалық, показать результат.",
    "Строительство и застройка": "Опубликовать статус по упомянутым объектам застройки/сноса, ответить на спорные стройки.",
    "Безопасность и правопорядок": "Скоординировать пресс-сопровождение резонансных инцидентов с ДП/ДЧС.",
    "Здравоохранение": "Дать ответ по конкретным поликлиникам/больницам, упомянутым в постах.",
    "Образование": "Ответить по конкретным школам/детсадам, разъяснить ситуацию родителям.",
    "Госуслуги и бюрократия": "Устранить сбои в Open Almaty/ЦОН, упростить процедуры, ответить адресно.",
    "Цены и социальные вопросы": "Разъяснить тарифы/цены, дать информацию о мерах поддержки.",
    "Прочее": "Мониторинг и подготовка разъяснительной коммуникации.",
}
DRAFT = {
    "Дороги и транспорт": "Акимат фиксирует обращения по дорожной ситуации{d} и аварийным участкам. Профильное управление проверяет; по итогам будет опубликован план мер и сроки. Просим направлять конкретные адреса.",
    "ЖКХ и инфраструктура": "По обращениям, связанным с инженерными сетями{d}, формируется график восстановления. Адресные жалобы отрабатываются в приоритетном порядке.",
    "Вода и канализация": "Вопрос перебоев с водоснабжением{d} взят на контроль. ГКП «Алматы Су» проверяет участок; о сроках восстановления сообщим дополнительно.",
    "Электроснабжение": "Обращения по отключениям электроэнергии{d} переданы в АЖК. Готовится разъяснение по причинам и графику восстановления.",
    "Экология и воздух": "Вопросы качества городской среды{d} на постоянном контроле. Данные мониторинга публикуются открыто; готовится отдельное разъяснение.",
    "Благоустройство и мусор": "Сигналы по уборке и состоянию территорий{d} переданы в ГКП «Алматы Тазалық». Участки берутся в работу.",
    "Строительство и застройка": "По упомянутым объектам застройки{d} запрошена информация в Управлении градостроительства. Ответ будет дан адресно.",
    "Безопасность и правопорядок": "Городские службы держат ситуацию на контроле. По резонансному инциденту{d} работают профильные органы; информация будет обновляться.",
    "Здравоохранение": "По упомянутым медучреждениям{d} запрошена информация у Управления общественного здоровья. Ответ будет дан адресно.",
    "Образование": "По обращениям, связанным со школами/детсадами{d}, проводится проверка. Управление образования даст ответ по каждому случаю.",
    "Госуслуги и бюрократия": "Сбои в работе госсервисов{d} зафиксированы. Ведётся устранение технических проблем; приносим извинения за неудобства.",
    "Цены и социальные вопросы": "Вопрос принят к рассмотрению{d}. Готовится разъяснение по тарифам и действующим мерам поддержки.",
    "Прочее": "Акимат принял сигнал{d} и готовит разъяснение. Конкретные обращения отрабатываются профильным управлением.",
}

STOP = set("""и в во не на я с со как а то все она так его но да ты к у же вы за бы по только ее мне было
вот от меня еще нет о из ему теперь когда даже ну вдруг ли если уже или ни быть был него до вас нибудь
опять уж вам ведь там потом себя ничего ей может они тут где есть надо ней для мы тебя их чем была сам
чтоб без будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой совсем ним здесь
этом один почти мой тем чтобы нее сейчас были куда зачем всех никогда можно при наконец два об другой
хоть после над больше тот через эти нас про всего них какая много разве три эту моя впрочем хорошо свою
этой перед иногда лучше чуть том нельзя такой им более всегда конечно всю между это что эта алматы almaty
город года году также свои нашваш более менее очень просто этому всё ещё который которые которых свой бар
города году жыл жылы күн күні уақыт орны болады едік
және бар бұл деп үшін мен біз ол бір осы сол қала бойынша туралы барысында сонымен жатыр дейін болып
керек кейін арналған ретінде деген қатысты болған еткен етіп сондай осындай тағы яғни жайлы жөнінде
сияқты арқылы кезінде менен пенен бенен барлық оның бұл анау мынау""".split())


def parse_dt(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def engagement(p):
    return p.get("engagement") or (p["likes"] + p["comments"] + p["shares"] + sum(p["reactions"].values()))


def load():
    if not CLEAN.exists():
        raise SystemExit(f"Нет {CLEAN}. Сначала: python ingest_meta.py")
    raw = json.loads(CLEAN.read_text(encoding="utf-8"))

    # Переклассифицируем категории по актуальным правилам (до фильтрации)
    raw = [reclassify(p) for p in raw]
    # Саркастичная «похвала» властей (издёвка с положительной оболочкой) — это КРИТИКА.
    # Снимаем ложный позитив и помечаем негативом (чтобы не накручивал индекс настроения).
    for p in raw:
        if p.get("sentiment") == "позитив" and has_sarcasm(p.get("text", "")):
            p["sentiment"] = "негатив"
    raw = [p for p in raw if not local_drop_reason(p)]

    verified = [p for p in raw if p.get("grok_done") and not p.get("drop")]

    if verified:
        # Grok отработал → аналитика и лента только по AI-проверенным релевантным постам.
        analysis = verified
        all_feed = verified
        log.info(f"Режим: AI-проверенный корпус ({len(analysis)} постов, лента: {len(all_feed)})")
    else:
        # Без AI: аналитика по жалобам, но лента — все непроспамленные
        all_feed = [p for p in raw if not p.get("drop")]
        analysis = [p for p in all_feed if p.get("is_complaint")]
        log.info(f"Режим: лексический ({len(analysis)} обращений, лента: {len(all_feed)} постов)")

    stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {}
    stats["ai_verified"] = bool(verified)
    return analysis, all_feed, stats


def neg_share(items):
    n = len(items) or 1
    return round(sum(1 for i in items if i["severity"] >= 4 or i["sentiment"] == "негатив") / n, 3)


def _attach_district_summaries(rows, posts_by_district):
    """Дописывает row['summary'] — короткую ИИ-сводку «чем волновали жители» —
    по уже классифицированным постам района (без нового вызова на каждый пост).
    Без ключа или при ошибке молча оставляет summary='' — карта просто не
    покажет блок сводки."""
    import os as _os
    api_key = (_os.getenv("LLM_API_KEY") or _os.getenv("DEEPSEEK_API_KEY")
               or _os.getenv("GROQ_API_KEY") or _os.getenv("GROK_API_KEY") or "").strip()
    summaries = {}
    if api_key and posts_by_district:
        try:
            import grok_filter as gf
            summaries = gf.summarize_districts(posts_by_district, api_key)
        except Exception as e:
            log.warning(f"Сводка по районам недоступна: {e}")
    for row in rows:
        row["summary"] = summaries.get(row["name"], "")


def _pick_opinions(items, limit=2):
    """До `limit` показательных постов района для карты-«облачков»: один самый
    резонансный негативный + один самый резонансный позитивный (если есть оба),
    чтобы бабблы честно отражали разброс мнений, а не только жалобы."""
    if not items:
        return []
    pos = [p for p in items if p.get("sentiment") == "позитив"]
    neg = [p for p in items if p.get("sentiment") == "негатив" or p.get("severity", 0) >= 4]
    picks, seen = [], set()
    for pool in (neg, pos):
        if pool:
            top = max(pool, key=engagement)
            if top["id"] not in seen:
                picks.append(top)
                seen.add(top["id"])
    if not picks:
        picks.append(max(items, key=engagement))
    return [sample(p) for p in picks[:limit]]


def daily_spark(items, days_back=8, end=None):
    end = end or datetime.now(timezone.utc)
    b = [0] * days_back
    for i in items:
        d = parse_dt(i["created_at"])
        if d:
            delta = (end.date() - d.date()).days
            if 0 <= delta < days_back:
                b[days_back - 1 - delta] += 1
    return b


def status_color(neg, trend):
    if neg >= 0.30:
        return "🔴"
    if neg >= 0.18 or trend > 2:
        return "🟠"
    if trend > 0:
        return "🟡"
    return "🟢"


def sample(p):
    return {
        "id": p["id"],
        "platform": p["platform"], "lang": p["lang"], "owner": p["owner_name"], "tier": p.get("tier", ""),
        "text": p["text"], "summary": p.get("summary", ""), "theme": p.get("theme", ""),
        "category": p["category"], "severity": p["severity"], "sentiment": p["sentiment"],
        "ai_verified": bool(p.get("grok_done")),
        "is_complaint": bool(p.get("is_complaint")),
        "district": p.get("district", ""), "created_at": p["created_at"],
        "url": p.get("url", ""), "mcl_url": p.get("mcl_url", ""),
        "likes": p["likes"], "comments": p["comments"], "shares": p["shares"],
        "reactions": p["reactions"], "eng": engagement(p),
    }


# Посты "пропал человек" — для отдельной вкладки
_MISSING_RX = _refix.compile(
    r"пропал[аио]?\b|без вести|в розыске|объявлен\w* в розыск|"
    r"\bжоғалды\b|іздеуде\b|потерял[ас]ся", _refix.I)
_MISSING_PERSON_HINT_RX = _refix.compile(
    r"человек|мужчин|женщин|девушк|парен|ребен|ребён|брат\b|братик|сестр|сын\b|сынок|"
    r"дочь|дочк|дедушк|бабушк|родствен|студент|мальчик|девочк|подросток|пенсионер|"
    r"бала\b|адам\b|ағайын", _refix.I)


def is_missing_person_post(text):
    if not text:
        return False
    return bool(_MISSING_RX.search(text)) and bool(_MISSING_PERSON_HINT_RX.search(text))


# Сигналы позитива и упоминания работы города/акимата
_POS_RX = _refix.compile(
    r"спасибо|благодар|рахмет|рақмет|молодц|красив|отличн|прекрасн|супер|"
    r"радост|ура\b|наконец[\s-]*то|наконец сделал|порадовал|приятно удивил|"
    r"қуант|жақсы болд|керемет|тамаша|ұнады|рахмет", _refix.I)
_AKIMAT_RX = _refix.compile(
    r"акимат|әкімдік|әкім\b|7[\s-]?20[\s-]?25|open almaty|опен алматы|"
    r"городск\w+ служб|коммунальщик|тазалық|программ\w* (?:жиль|капремонт|реновац|субсид)", _refix.I)

# Сарказм: позитивная история с развязкой-отрицанием («…Народ счастлив. Как зовут акима?
# Его не существует.»), издёвка, идиома «положить болт на …» (= забить/пренебречь). Это НЕ позитив.
_SARCASM_RX = _refix.compile(
    r"(?:его|её|их|такого|такой\s+\w+|тако[вй])\s+не\s+существует|"
    r"\bне\s+существует\b|в\s+ро[зс]ов\w+\s+(?:мечт|сн)|в\s+идеальн\w+\s+мир|\bв\s+мечтах\b|"
    r"в\s+параллельн\w+\s+вселенн|в\s+сказк|размечта|\bмечтай\b|"
    r"ага,?\s*конечно|ну[\s-]+ну\b|конечно[\s-]+конечно|так\s+я\s+и\s+поверил|"
    r"свежо\s+предание|верится\s+с\s+трудом|только\s+на\s+бумаге|"
    # идиома «(положить/класть) болт на X» — вульгарное «пренебречь», всегда сарказм/критика
    r"болт\w*[\s\S]{0,60}(?:клал|кладёт|кладут|положи\w*|клад\w+|ложил|ложит|на\s+(?:уборк|закон|снег|город|жите|народ))|"
    r"(?:положил|клал|клад\w+|ложил)\s+болт|"
    r"сарказм|/s\b|\bкек\b|ес[іи]\s+емес\b|болмайды\s+ондай", _refix.I)

# Вопрос/просьба о совете — НЕ похвала города (не пускаем в блок позитива).
_REQUEST_RX = _refix.compile(
    r"посоветуйте|подскажите|кто\s+знает|помогите\s+(?:выбрать|найти)|"
    r"есть\s+(?:ли\s+)?(?:хорошие\s+)?варианты|полезные\s+рекомендации|"
    r"по\s+выбору\s+жилья|порекомендуйте", _refix.I)

# Медиа/бизнес-страницы и репост-обсуждения (не голос горожанина) — отсекаем.
_MEDIA_DISCUSSION_RE = _refix.compile(
    r"#\w*business\b|#inbusiness|#atameken|#tengri|#orda\b|#nur\.?kz|#zakon|"
    r"в\s+соцсет\w+\s+(?:продолжается\s+|идёт\s+|идет\s+)?обсужд|"
    r"@atameken\s*business|inbusiness\.kz", _refix.I)


def has_sarcasm(text: str) -> bool:
    return bool(_SARCASM_RX.search(text or ""))


def is_positive_post(p: dict) -> bool:
    """Строгая проверка «позитива»: негатив, острое (sev>=4), жалобы И САРКАЗМ —
    НИКОГДА не позитив, даже если поверхностно много добрых слов."""
    sent = p.get("sentiment", "нейтрально")
    sev  = int(p.get("severity") or 1)
    text = p.get("text", "")
    if sent == "негатив" or sev >= 4 or p.get("is_complaint"):
        return False
    if has_sarcasm(text):          # «народ счастлив… акима не существует» — это сатира
        return False
    if _REQUEST_RX.search(text):   # «посоветуйте варианты…» — это вопрос, а не похвала
        return False
    # позитив = явная положительная тональность ИЛИ чёткая благодарность в нейтральном посте
    return sent == "позитив" or bool(_POS_RX.search(text))


def ai_post_recommendation(p: dict) -> dict:
    cat = p.get("category", "Прочее")
    sev = int(p.get("severity") or 1)
    sentiment = p.get("sentiment", "нейтрально")
    is_complaint = bool(p.get("is_complaint"))
    text = (p.get("summary") or p.get("theme") or p.get("text") or "").strip()
    hook = text[:120].replace("\n", " ")
    eng = engagement(p)

    # ── 1) ПОЗИТИВ ──────────────────────────────────────────────────────────
    # Похвалу/благодарность НЕ обрабатываем как проблему — фиксируем и усиливаем.
    # ВАЖНО: негатив/острое/жалоба сюда не попадают (is_positive_post это гарантирует).
    if is_positive_post(p):
        about_akimat = bool(_AKIMAT_RX.search(text))
        return {
            "priority": "Позитив",
            "why": f"Положительный отклик ({eng} вовлечённости){' о работе города' if about_akimat else ''}; тема: {hook or cat}.",
            "action": ("Зафиксировать как положительный кейс работы акимата; поблагодарить автора и по возможности масштабировать/показать результат."
                       if about_akimat else
                       "Реагирование как на проблему не требуется. Поддержать автора, отметить позитивный отклик."),
            "comms": "Готовый позитивный контент: репост в истории/канал города, короткая благодарность от первого лица.",
        }

    # ── 2) НЕ ЖАЛОБА ────────────────────────────────────────────────────────
    # Мнение/вопрос/обсуждение без негатива и без остроты — адресной отработки нет.
    if not is_complaint and sev <= 2 and sentiment != "негатив":
        return {
            "priority": "Мониторинг",
            "why": f"Это мнение/вопрос, а не обращение о проблеме ({eng} вовлечённости); тема: {hook or cat}.",
            "action": "Адресной отработки не требуется. При уместности — корректно включиться в диалог или дать справочную информацию (без официального «реагирования на ЧП»).",
            "comms": "Держать на мониторинге; публичный ответ — только если тема перерастёт в волну вопросов.",
        }

    # ── 3) ЖАЛОБА / НЕГАТИВ / ОСТРОЕ — отработка по категории ────────────────
    if cat == "Дороги и транспорт":
        action = "Проверить локацию/маршрут, сверить с текущими работами и дать короткий публичный статус: причина, срок, ответственный."
        comms = "Сделать карточку с картой участка и понятным next step для жителей; отдельно собрать комментарии с адресами."
    elif cat == "Безопасность и правопорядок":
        action = "Запросить подтверждение у ДП/ДЧС и выпустить аккуратное обновление без лишних деталей расследования."
        comms = "Если тема резонансная, закрепить официальный пост и отвечать одной согласованной формулировкой."
    elif cat in {"Вода и канализация", "Электроснабжение", "ЖКХ и инфраструктура"}:
        action = "Сверить аварийные заявки и график восстановления, дать адресный статус по району/улице."
        comms = "Опубликовать короткое обновление в формате: где сбой, что делает служба, когда следующий апдейт."
    elif cat == "Благоустройство и мусор":
        action = "Передать сигнал районной службе, запросить фотофиксацию до/после и срок уборки."
        comms = "Показать результат в Stories/посте: проблема → выезд → устранение, чтобы закрыть негативный цикл."
    elif cat == "Экология и воздух":
        action = "Сверить жалобу с данными мониторинга/выездом, подготовить объяснение источника запаха/дыма/пыли."
        comms = "Дать жителям простой канал для повторных сигналов и карту точки наблюдения."
    elif cat == "Образование":
        action = "Проверить учреждение и связаться с управлением образования; не публиковать персональные данные детей."
        comms = "Коммуникация должна быть спокойной: факт проверки, сроки, куда родителям обращаться."
    else:
        action = "Проверить факт, определить ответственное управление и подготовить короткий ответ в течение суток."
        comms = "Не спорить в комментариях; дать понятный маршрут решения и ссылку на официальный канал."

    priority = "Срочно" if sev >= 5 else "Сегодня" if sev >= 4 else "Планово"
    return {
        "priority": priority,
        "why": f"Пост уже набрал {engagement(p)} вовлечённости; тема: {hook or cat}.",
        "action": action,
        "comms": comms,
    }


def post_with_ai(p: dict) -> dict:
    s = sample(p)
    s["ai_recommendation"] = ai_post_recommendation(p)
    return s


def window_category_posts(posts, now, days, max_cats=6, per_cat=2):
    since = now - timedelta(days=days)
    items = [p for p in posts if (d := parse_dt(p.get("created_at", ""))) and since <= d <= now]
    groups = defaultdict(list)
    for p in items:
        if p.get("category") != "Прочее":
            groups[p["category"]].append(p)
    rows = []
    for cat, pp in groups.items():
        top = sorted(pp, key=lambda x: (engagement(x), x.get("severity", 0)), reverse=True)[:per_cat]
        rows.append({
            "category": cat,
            "count": len(pp),
            "engagement": sum(engagement(x) for x in pp),
            "neg": neg_share(pp),
            "top_posts": [post_with_ai(x) for x in top],
            "recommendation": RECO.get(cat, RECO["Прочее"]),
        })
    rows.sort(key=lambda r: (r["count"], r["engagement"]), reverse=True)
    return rows[:max_cats]


def spirit_case():
    return {
        "title": "🔮 Предиктивный кейс: Spirit of Tengri",
        "subtitle": "позитивная тема, но мало участников — что прогноз говорит о следующем запуске",
        "signal": "Тональность в соцсетях тёплая и позитивная: международный этно-фестиваль на площади Абая "
                  "при поддержке акимата восприняли как «хорошее городское событие». Но охват публикаций и явка "
                  "заметно ниже потенциала события такого уровня — позитив есть, людей мало.",
        "prediction": "Если формат анонсирования не изменить, следующий выпуск с высокой вероятностью снова недоберёт "
                      "аудиторию — при той же качественной программе. Главный управляемый фактор здесь не сам контент "
                      "события, а его информационная подготовка: заранее и системно усилить анонсирование (хабарландыру).",
        "diagnosis": [
            "Тема позитивная, но подана нишево: этно/world music понятен лояльной аудитории, а массовому горожанину не объяснили «почему стоит прийти».",
            "Коммуникация была скорее справочной (когда и где), чем мотивирующей (зачем именно мне).",
            "Мало поводов для пользовательского контента ДО события — люди идут, когда уже видят эмоцию, маршрут и компанию.",
            "Вероятно, поздний или узкий по каналам анонс — не добрали молодёжные и семейные аудитории."
        ],
        "would_help": "Ключевой вывод — усилить именно анонсирование (информирование), а не саму программу: не просто чаще постить, а заранее и креативно «упаковать» событие.",
        "moves": [
            "Сделать серию коротких Reels/TikTok: «звучание степи за 15 секунд», «что надеть», «с кем идти», «3 причины зайти после работы».",
            "Подключить микроинфлюенсеров Алматы: музыка, urban lifestyle, родители, студенты, туристические страницы, локальные кофейни.",
            "Запустить городской челлендж: снять звук города/домбры/улицы и собрать UGC-плейлист Spirit of Almaty.",
            "Упаковать фестиваль как бесплатный/доступный городской маршрут: музыка + еда + ремесленники + вечерняя прогулка + фотозоны.",
            "Дать понятную логистику: карта входов, транспорт, парковки, тайминг хэдлайнеров, что делать с детьми.",
            "Сделать афиши не только с артистами, а с эмоцией: крупный визуал толпы, сцены, света, национальных мотивов в современном стиле."
        ],
        "next_time": [
            "За 21 день: teaser-креативы и партнёрские анонсы.",
            "За 10 дней: ежедневные короткие видео артистов и сценарии посещения для разных аудиторий.",
            "За 72 часа: countdown, карта, погодный план, подборки «кого послушать».",
            "В день события: live-контент, репосты гостей, push через городские и партнёрские страницы."
        ]
    }


def period_str(posts):
    ds = [d for d in (parse_dt(p["created_at"]) for p in posts) if d]
    return f"{min(ds).strftime('%d.%m.%Y')} — {max(ds).strftime('%d.%m.%Y')}" if ds else ""


# ── Исторический обзор месяца: карта районов + ИИ-сводка ────────────────────
# Первый выпуск — июнь 2026, сводка написана вручную по данным корпуса.
# TODO: автоматизировать генерацию помесячных сводок через Groq
# (тот же GROQ_API_KEY/паттерн, что в grok_filter.py), когда появится ключ.
REVIEW_MONTH = "2026-06"
REVIEW_TITLE = "Июнь 2026"

# 8 городских районов Алматы — как в almaty-districts.geo.json (nameRu без «район»).
# Районы Алматинской ОБЛАСТИ (напр. Уйгурский) на карту города не попадают.
CITY_DISTRICTS = ["Алатауский", "Алмалинский", "Ауэзовский", "Бостандыкский",
                  "Жетысуский", "Медеуский", "Наурызбайский", "Турксибский"]

# Живые снимки скрапера Threads (см. run_hourly.py) — НЕ прошли AI-проверку,
# но честно показывают реальный объём собранного за месяц (в отличие от
# meta_clean.json, который отражает только уже AI-верифицированную часть).
# Оба файла держим: data/threads_live.json — более ранний снимок, output/ —
# более свежий; вместе (объединённые по id) они покрывают месяц почти без пропусков.
THREADS_ARCHIVE_PATHS = [HERE / "data" / "threads_live.json", HERE / "output" / "threads_live.json"]


def _archive_month_total(month: str) -> int:
    """Сколько постов про Алматы реально собрано в Threads за месяц —
    по объединению живых снимков скрапера (см. THREADS_ARCHIVE_PATHS).
    Не подменяет AI-верифицированный корпус, только честная цифра объёма."""
    seen = {}
    for path in THREADS_ARCHIVE_PATHS:
        if not path.exists():
            continue
        try:
            for p in json.loads(path.read_text(encoding="utf-8")):
                if str(p.get("created_at", ""))[:7] == month:
                    seen[p.get("id")] = True
        except Exception:
            continue
    return len(seen)


REVIEW_AI_SUMMARY = [
    "Автоматический сбор в Threads поймал за июнь {archive_total} упоминаний Алматы; строгую "
    "антиспам- и AI-проверку (категория, острота, район) на момент этой сводки прошли только "
    "{n} обращений — на них построены карта и разбор тем ниже, остальные ждут очереди на "
    "AI-верификацию. Даже на этой выборке фон напряжённый: 62% обращений негативные, 34 (44%) "
    "— повышенной остроты (4–5).",
    "Главная тема AI-проверенной выборки — «Дороги и транспорт» (21 обращение, 27%). Горожане "
    "писали о разбитом Кульджинском тракте, где обещанный ещё в 2024 году ремонт так и не "
    "завершён, об опасной велодорожке на Тимирязева, о свежей дороге на Ремизовке, где уже "
    "латают люки, о работе общественного транспорта и грубости таксистов. Отдельный резонанс "
    "— транспортный коллапс на выезде из города на концерт в Конаеве.",
    "Второй план — безопасность и застройка (по 10 обращений). Самый обсуждаемый инцидент — "
    "видео с избиением подростка на футбольном поле в 8-м микрорайоне. В застройке звучит "
    "контраст: «строим Смарт Сити и говорим о высоких технологиях», а в Алатауском районе у "
    "людей нет водоснабжения, отключают свет и отсутствует интернет. В образовании (8) — "
    "старт подачи документов в 1-й класс: родители жалуются на нехватку мест и отказы, в том "
    "числе в НИШ «Медеу» и РФМШ.",
    "Позитивная повестка тоже есть (12 постов, 15%): запуск зоны низких выбросов LEZ, анонс "
    "надземного метро SkyTrain, 100 тысяч поездок на кикшеринговых самокатах в сутки, "
    "бесплатная летняя резиденция для учителей и восторженные отзывы гостей города.",
    "Ограничение карты: район удалось определить только у 5 городских обращений (Алатауский, "
    "Жетысуский, Алмалинский, Медеуский) — район распознаёт только AI-проверка, а её прошла "
    "малая часть месяца. По остальным районам данных недостаточно для честной детализации, "
    "это помечено на карте знаком «❔».",
]


def month_review(posts):
    """Агрегат для вкладки «Обзор месяца»: срез по REVIEW_MONTH — статистика,
    категории с самым резонансным постом и разбивка по городским районам
    (честно, без выдумывания: районы без данных получают count=0).
    Категории/цитаты берутся из AI-верифицированного корпуса (posts); архивный
    объём (archive_total) — отдельная честная цифра «сколько всего собрано»."""
    mp = [p for p in posts if str(p.get("created_at", ""))[:7] == REVIEW_MONTH]
    if len(mp) < 10:
        return None
    n = len(mp)
    archive_total = max(_archive_month_total(REVIEW_MONTH), n)
    days = sorted({str(p["created_at"])[:10] for p in mp})
    period = f"{int(days[0][8:10])}–{int(days[-1][8:10])} июня 2026"

    cats = defaultdict(list)
    for p in mp:
        cats[p["category"]].append(p)
    categories = []
    for cat, items in sorted(cats.items(), key=lambda kv: -len(kv[1])):
        top = max(items, key=engagement)
        categories.append({"category": cat, "count": len(items),
                           "share": round(len(items) / n, 3), "neg": neg_share(items),
                           "eng": sum(engagement(x) for x in items),
                           "top_post": sample(top)})

    districts, tagged, dist_items = [], 0, {}
    for name in CITY_DISTRICTS:
        items = [p for p in mp if (p.get("district") or "").strip() == name]
        dist_items[name] = items
        tagged += len(items)
        top_cat = Counter(x["category"] for x in items).most_common(1)[0][0] if items else ""
        districts.append({"name": name, "count": len(items), "top_category": top_cat,
                          "neg": neg_share(items) if items else 0,
                          "posts": [sample(x) for x in
                                    sorted(items, key=engagement, reverse=True)[:3]],
                          "opinions": _pick_opinions(items)})
    _attach_district_summaries(districts, dist_items)

    return {
        "month": REVIEW_MONTH, "title": REVIEW_TITLE, "period": period,
        "n": n, "archive_total": archive_total, "reach": sum(engagement(p) for p in mp),
        # доля именно негативных по тональности (для чипа «негатив» — согласуется со сводкой)
        "neg": round(sum(1 for p in mp if p["sentiment"] == "негатив") / n, 3),
        "acute": sum(1 for p in mp if p.get("severity", 0) >= 4),
        "district_tagged": tagged,
        "categories": categories, "districts": districts,
        "ai_summary": [p.format(archive_total=archive_total, n=n) for p in REVIEW_AI_SUMMARY],
    }


def build(posts, all_feed, stats):
    dts = [d for d in (parse_dt(p["created_at"]) for p in posts) if d]
    # Реальное текущее время, а не дата самого свежего поста в корпусе — иначе
    # если корпус отстаёт (например, свежие данные ещё не собрались), "за сутки"
    # молча считается от старой даты и в него попадают посты недельной/месячной
    # давности, подписанные как "сегодня".
    now = datetime.now(timezone.utc)

    cats = defaultdict(list)
    for p in posts:
        cats[p["category"]].append(p)

    problems = []
    for cat, items in cats.items():
        if cat == "Прочее":
            continue
        n = len(items)
        # Цитаты-образцы предпочитают СВЕЖИЕ посты (старые уже отработаны службами)
        def _sample_key(x):
            d = parse_dt(x["created_at"]); age = (now - d).days if d else 999
            return (1 if age <= 7 else 0, x["severity"], engagement(x))
        items_sorted = sorted(items, key=_sample_key, reverse=True)
        avg_sev = sum(i["severity"] for i in items) / n
        eng = sum(engagement(i) for i in items)
        recent = sum(1 for i in items if (d := parse_dt(i["created_at"])) and (now - d).days <= 3)
        prev = sum(1 for i in items if (d := parse_dt(i["created_at"])) and 3 < (now - d).days <= 6)
        ns = neg_share(items)
        trend = recent - prev
        themes = [t for t, _ in Counter(i["theme"] for i in items if i["theme"]).most_common(5)]
        if not themes:  # лексический фолбэк: частые слова категории
            themes = top_terms(items, 4)
        district = Counter(i["district"] for i in items if i["district"]).most_common(1)
        problems.append({
            "category": cat, "count": n, "avg_severity": round(avg_sev, 1), "neg_share": ns,
            "engagement": eng, "recent": recent, "prev": prev, "trend": trend,
            "score": round(n * 3 + avg_sev * 5 + eng ** 0.5 + ns * 25, 1),
            "growth": round(max(-1.0, min(1.0, (recent - prev) / max(prev, 1))), 2),
            "status": status_color(ns, trend), "top_themes": themes,
            "spark": daily_spark(items, 8, now), "district": district[0][0] if district else "",
            "department": DEPT.get(cat, DEPT["Прочее"]), "recommendation": RECO.get(cat, RECO["Прочее"]),
            "draft": DRAFT.get(cat, DRAFT["Прочее"]), "samples": [sample(i) for i in items_sorted[:3]],
        })
    problems.sort(key=lambda x: x["score"], reverse=True)
    alarms = sorted(problems, key=lambda p: (p["neg_share"] + 0.1) * (p["recent"] + 1) * p["avg_severity"],
                    reverse=True)[:4]

    # Слайдер «Сигналы тревоги»: до 12 свежих/острых постов по каждой теме (без дублей).
    def _alarm_key(x):
        d = parse_dt(x["created_at"]); age = (now - d).days if d else 999
        return (1 if age <= 7 else 0, x["severity"], engagement(x))
    for a in alarms:
        seen, rich = set(), []
        for i in sorted(cats.get(a["category"], []), key=_alarm_key, reverse=True):
            key = " ".join((i.get("text", "")[:70]).lower().split())
            if key in seen:
                continue
            seen.add(key)
            rich.append(sample(i))
            if len(rich) >= 12:
                break
        a["samples"] = rich

    # ── СВЕЖИЕ РЕЗОНАНСНЫЕ СИГНАЛЫ (раздел «Сигналы тревоги») ───────────────────
    # Только свежие посты — старые (>недели) уже отработаны службами.
    # Приоритет: набирает охват ИЛИ резонансный по тексту (острота/негатив).
    def _fresh_pool(days):
        return [p for p in posts
                if (d := parse_dt(p["created_at"])) and 0 <= (now - d).days <= days
                and p.get("category") != "Прочее"
                and not is_positive_post(p)]   # позитив — в свой блок, не в «тревоги»
    fresh_pool = _fresh_pool(7) or _fresh_pool(14) or _fresh_pool(30)
    _engs = sorted((engagement(p) for p in fresh_pool), reverse=True)
    eng_hi = _engs[max(0, len(_engs) // 4 - 1)] if _engs else 0   # ~75-й перцентиль охвата

    def _resonance(p):
        d = parse_dt(p["created_at"]); age = (now - d).days if d else 999
        eng = engagement(p); sev = int(p.get("severity") or 1)
        neg = p.get("sentiment") == "негатив" or sev >= 4
        recency = max(0.0, (7 - min(age, 7)) / 7)          # 1.0 сегодня → 0 на 7-й день
        return (eng ** 0.4) * 1.1 + sev * 1.4 + (2 if neg else 0) \
               + (1 if p.get("is_complaint") else 0) + recency * 3.0

    hot_signals = []
    _per_cat = Counter()
    for p in sorted(fresh_pool, key=_resonance, reverse=True):
        cat = p["category"]
        if _per_cat[cat] >= 2:               # не более 2 на категорию — для разнообразия
            continue
        # Дополнительный фильтр: шутки/мемы про природные явления не попадают в «Тревоги»
        _txt = p.get("text", "")
        if _CASUAL_NATURE_RE.search(_txt) and not _MUNICIPAL_SERVICE_RE.search(_txt):
            continue
        d = parse_dt(p["created_at"]); age = (now - d).days if d else 0
        eng = engagement(p); sev = int(p.get("severity") or 1)
        reasons = []
        if eng_hi and eng >= eng_hi: reasons.append(f"набирает охват · {eng}")
        if sev >= 4:                 reasons.append("острый по тексту")
        if p.get("sentiment") == "негатив": reasons.append("негативный резонанс")
        reasons.append("сегодня" if age == 0 else ("вчера" if age == 1 else f"{age} дн. назад"))
        hot_signals.append({
            "post": sample(p), "category": cat,
            "department": DEPT.get(cat, DEPT["Прочее"]),
            "recommendation": RECO.get(cat, RECO["Прочее"]),
            "draft": DRAFT.get(cat, DRAFT["Прочее"]),
            "severity": sev, "engagement": eng, "age_days": age,
            "neg": bool(p.get("sentiment") == "негатив" or sev >= 4),
            "reasons": reasons,
        })
        _per_cat[cat] += 1
        if len(hot_signals) >= 6:
            break

    last24 = [p for p in posts if (d := parse_dt(p["created_at"])) and (now - d) <= timedelta(hours=24)]
    span = max(1, (now - min(dts)).days) if dts else 1
    viral24 = max(last24, key=engagement, default=None)
    # Несколько самых резонансных постов за сутки (по охвату, без дублей-перезаливов)
    _seen_v, viral_list = set(), []
    for p in sorted(last24, key=engagement, reverse=True):
        key = " ".join((p.get("text", "")[:70]).lower().split())
        if key in _seen_v:
            continue
        _seen_v.add(key)
        viral_list.append(p)
        if len(viral_list) >= 12:
            break
    month_window = window_category_posts(posts, now, 30, max_cats=8, per_cat=6)
    day_window   = window_category_posts(posts, now, 1, max_cats=8, per_cat=8)

    # ── Индекс напряжённости: честная формула ───────────────────────────────────
    # Проблема: в корпусе жалоб sentiment="негатив" у 95%+ постов — это норма, не кризис.
    # Поэтому считаем только по severity 4-5 (настоящие инциденты) и динамике роста тем.
    n_posts = max(len(posts), 1)
    sev5_ratio = sum(1 for p in posts if p.get("severity") == 5) / n_posts  # пожары/ЧП/гибели
    sev4_ratio = sum(1 for p in posts if p.get("severity") == 4) / n_posts  # отключения/нападения

    # При разреженных данных (мало постов/день на категорию) сырой счётчик "растущих"
    # категорий — шум: скачок с 0 до 1-2 постов задевает почти все категории разом.
    # Поэтому считаем ДОЛЮ растущих/эскалирующих среди категорий с заметным объёмом (>=5 постов).
    sig_cats = [p for p in problems if p["count"] >= 5]
    n_sig = max(len(sig_cats), 1)
    growth_share    = sum(1 for p in sig_cats if p["trend"] > 0) / n_sig
    escalate_share  = sum(1 for p in sig_cats if p["trend"] > 2) / n_sig

    tension = min(100, round(
        sev5_ratio     * 70 +   # ЧП/гибели/пожары — главный драйвер
        sev4_ratio     * 35 +   # серьёзные инциденты
        growth_share   * 15 +   # доля растущих тем (не сырой счётчик)
        escalate_share * 15     # доля быстро эскалирующих тем
    ))
    tlabel = ("Низкая напряжённость" if tension < 30 else "Умеренная напряжённость"
              if tension < 55 else "Повышенная напряжённость" if tension < 78 else "Высокая напряжённость")

    senti_by_cat = []
    for p in problems[:10]:
        items = cats[p["category"]]
        severe = sum(1 for i in items if i.get("severity", 0) >= 4)
        pos = sum(1 for i in items if i.get("sentiment") == "позитив")
        neu = max(0, len(items) - severe - pos)
        senti_by_cat.append({"category": p["category"], "neg": severe, "neu": neu, "pos": pos})

    triggers = top_terms(posts, 26, with_count=True)
    negitems = [p for p in posts if p["severity"] >= 4 or p["sentiment"] == "негатив"]
    negwords = top_terms(negitems, 16, with_count=True)

    # Только 8 городских районов (см. CITY_DISTRICTS) — иначе редкие варианты
    # написания/комбо-районы/районы области с 1-2 постами (neg часто =100% на
    # таком объёме) забивают топ "самые напряжённые районы" мусором.
    districts = Counter(p["district"] for p in posts if p["district"] in CITY_DISTRICTS)
    dist_rows = [{"name": k, "count": v, "neg": neg_share([p for p in posts if p["district"] == k])}
                 for k, v in districts.most_common()]
    _attach_district_summaries(
        dist_rows, {row["name"]: [p for p in posts if p["district"] == row["name"]] for row in dist_rows})

    weeks = defaultdict(int)
    for p in posts:
        d = parse_dt(p["created_at"])
        if d:
            iso = d.isocalendar()
            weeks[f"{iso[0]}-W{iso[1]:02d}"] += 1
    timeline = [{"week": k, "count": v} for k, v in sorted(weeks.items())]

    # ── Темы по дням недели: что волновало горожан чаще в конкретный день ───────
    WEEKDAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    weekday_cats = defaultdict(Counter)
    for p in posts:
        d = parse_dt(p["created_at"])
        if d and p["category"] != "Прочее":
            weekday_cats[d.weekday()][p["category"]] += 1
    weekday_topics = [
        {
            "day": WEEKDAY_NAMES[wd],
            "top": [{"category": c, "count": n} for c, n in weekday_cats[wd].most_common(3)],
        }
        for wd in range(7)
    ]
    # Полная матрица (все категории, не только топ-3) — для стековой диаграммы
    # "темы по дням недели" на обзорной странице.
    _wd_cats_order = [c for c, _ in Counter(
        p["category"] for p in posts if p["category"] != "Прочее"
    ).most_common()]
    weekday_matrix = {
        "days": WEEKDAY_NAMES,
        "categories": _wd_cats_order,
        "counts": {c: [weekday_cats[wd].get(c, 0) for wd in range(7)] for c in _wd_cats_order},
    }

    # ── Хроника: заметные дни + вероятная причина (самый резонансный пост дня) ──
    # У нас нет ленты новостей — «событие» это реконструкция по самому острому/
    # заметному посту дня, со ссылкой на источник. Дни с 1 постом пропускаем —
    # мало сигнала, чтобы говорить о всплеске.
    daily = defaultdict(list)
    for p in posts:
        d = parse_dt(p["created_at"])
        if d and p["category"] != "Прочее":
            daily[d.date()].append(p)
    day_rows = []
    for day, items in daily.items():
        if len(items) < 2:
            continue
        top_cat = Counter(i["category"] for i in items).most_common(1)[0][0]
        signature = max(items, key=lambda i: (i["severity"], engagement(i)))
        day_rows.append({
            "date": day.isoformat(), "weekday": WEEKDAY_NAMES[day.weekday()],
            "count": len(items), "category": top_cat, "signature": sample(signature),
        })
    day_rows.sort(key=lambda r: r["count"], reverse=True)
    chronicle = sorted(day_rows[:12], key=lambda r: r["date"])

    platforms = []
    for plat in ("Facebook", "Instagram", "Threads"):
        pp = [p for p in posts if p["platform"] == plat]
        if pp:
            platforms.append({"platform": plat, "n": len(pp), "eng": sum(engagement(x) for x in pp),
                              "neg": neg_share(pp),
                              "toptheme": Counter(x["category"] for x in pp).most_common(1)[0][0]})
    langs = [{"lang": k, "n": v} for k, v in Counter(p["lang"] for p in posts).most_common()]
    tiers = [{"tier": k, "n": v, "eng": sum(engagement(x) for x in posts if x["tier"] == k)}
             for k, v in Counter(p["tier"] for p in posts).most_common()]

    spotlight = [p for p in posts if p["is_complaint"] or p["severity"] >= 4 or p["sentiment"] == "негатив"]
    top_posts = sorted((spotlight or posts), key=engagement, reverse=True)[:10]

    # ПОЗИТИВ о работе акимата/города — отдельный блок (что хвалят, что работает).
    # Строгий фильтр: негатив/острое/жалобы исключены (см. is_positive_post).
    positive = [p for p in posts if is_positive_post(p)]
    # Мягкий приоритет постам про работу города (×1.6 к охвату), но яркий позитив
    # с большим охватом (напр. «фасады как в Европе») тоже проходит.
    # Дедуп по началу текста — убираем одинаковые посты (перезаливы, кросс-платформа).
    positive.sort(key=lambda x: engagement(x) * (1.6 if _AKIMAT_RX.search(x.get("text", "")) else 1.0),
                  reverse=True)
    _seen_pos, positive_dedup = set(), []
    for p in positive:
        key = " ".join((p.get("text", "")[:70]).lower().split())
        if key in _seen_pos:
            continue
        _seen_pos.add(key)
        positive_dedup.append(p)
    positive_posts = [post_with_ai(x) for x in positive_dedup[:6]]

    # all_posts для раздела "Все обращения" — аналитическая выборка (жалобы/острые).
    # Таблица показывает максимум 400 строк, фильтрация по 2000 — более чем достаточно.
    TABLE_LIMIT = 2000
    all_sorted = sorted(posts, key=lambda x: (x["severity"], engagement(x)), reverse=True)[:TABLE_LIMIT]

    # feed_posts для "Реальной ленты" и "Аналитики по словам" — ВСЕ посты после антиспама.
    # Больше держим для качества точечного поиска (редкие сигналы: суицид/апатия/буллинг).
    FEED_LIMIT = 3000
    feed_sorted = sorted(
        all_feed,
        key=lambda x: (x.get("created_at", "") or "", engagement(x)),
        reverse=True
    )[:FEED_LIMIT]

    # missing_sorted для вкладки "Пропавшие" — посты о поиске людей, новые первыми.
    missing_sorted = [p for p in feed_sorted if is_missing_person_post(p.get("text", ""))][:40]

    return {
        "meta": {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "updated_iso": datetime.now(timezone.utc).isoformat(),
            "period": period_str(posts),
            "total_raw": stats.get("total", len(all_feed)), "total_kept": len(posts),
            "kept_pct": round(100 * len(posts) / max(stats.get("total", len(all_feed)), 1), 1),
            "removed": {"junk": stats.get("junk", 0), "branded": stats.get("branded", 0),
                        "not_almaty": stats.get("not_almaty", 0), "dup": stats.get("dup", 0),
                        "short": stats.get("short", 0), "offtopic": stats.get("offtopic", 0)},
            "reach": sum(engagement(p) for p in posts),
            "authors": len(set(p["owner_name"] for p in posts)),
            "sent_index": round(100 * sum(1 for p in posts if p["sentiment"] != "негатив") / max(len(posts), 1)),
            "tension_value": tension, "districts": len(districts),
            "complaints": sum(1 for p in posts if p["is_complaint"]),
            "avg_per_day": round(len(posts) / span, 1),
            "platforms_n": len(platforms),
            "ai_verified": bool(stats.get("ai_verified")),
            "feed_total": len(all_feed),
        },
        "problems": problems, "alarms": alarms, "hot_signals": hot_signals,
        "now24": {"n": len(last24), "avg": round(len(posts) / span, 1),
                  "hot": [{"cat": c, "n": k} for c, k in Counter(p["category"] for p in last24).most_common(3)],
                  "viral": post_with_ai(viral24) if viral24 else None,
                  "viral_posts": [post_with_ai(p) for p in viral_list],
                  "by_category": day_window,
                  "month_by_category": month_window},
        "cases": {"spirit_tengri": spirit_case()},
        "positive_posts": positive_posts,
        "tension": {"value": tension, "label": tlabel},
        "senti_by_cat": senti_by_cat, "triggers": triggers, "negwords": negwords,
        "districts": dist_rows, "timeline": timeline, "weekday_topics": weekday_topics,
        "weekday_matrix": weekday_matrix,
        "chronicle": chronicle, "month_review": month_review(posts),
        "platforms": platforms, "langs": langs, "tiers": tiers,
        "top_posts": [sample(p) for p in top_posts],
        **_dedup_post_lists(all_sorted, feed_sorted, missing_sorted),
    }


def _dedup_post_lists(all_sorted, feed_sorted, missing_sorted=None):
    """all_posts и feed_posts сильно пересекаются (часто это одни и те же посты
    в разном порядке) — раньше каждый пост сериализовался в JSON дважды
    с полным текстом, что раздувало index.html в разы. Теперь храним каждый
    пост один раз в posts_by_id, а all_posts/feed_posts — это просто списки id
    в нужном порядке; на клиенте они "разворачиваются" обратно в полные объекты."""
    missing_sorted = missing_sorted or []
    posts_by_id = {}
    for p in all_sorted + feed_sorted + missing_sorted:
        pid = p["id"]
        if pid not in posts_by_id:
            posts_by_id[pid] = sample(p)
    return {
        "posts_by_id": posts_by_id,
        "all_posts": [p["id"] for p in all_sorted],
        "feed_posts": [p["id"] for p in feed_sorted],
        "missing_persons": [p["id"] for p in missing_sorted],
    }


_term_re = None
def top_terms(items, k, with_count=False):
    import re
    global _term_re
    if _term_re is None:
        _term_re = re.compile(r"[а-яёa-zәғқңөұүһі]{4,}")
    freq = Counter()
    for p in items:
        freq.update(set(w for w in _term_re.findall(p["text"].lower()) if w not in STOP))
    if with_count:
        return freq.most_common(k)
    return [w for w, _ in freq.most_common(k)]


def load_geojson():
    for c in GEO_CANDIDATES:
        if c.exists():
            return json.loads(c.read_text(encoding="utf-8"))
    return None


def load_scraper_status():
    """Статус парсера 24/7: live-хвост лога + история запусков (для блока на дашборде)."""
    tail = {}
    if LIVE_TAIL.exists():
        try:
            tail = json.loads(LIVE_TAIL.read_text(encoding="utf-8"))
        except Exception:
            tail = {}

    runs = []
    if HOURLY_STATS.exists():
        try:
            history = json.loads(HOURLY_STATS.read_text(encoding="utf-8"))
            for e in history[-8:]:
                runs.append({
                    "run_at": e.get("run_at", ""),
                    "total_seen": e.get("total_seen", 0),
                    "kept": e.get("kept", 0),
                    "pass_rate_pct": e.get("pass_rate_pct", 0),
                })
            runs.reverse()
        except Exception:
            pass

    updated_at = tail.get("updated_at", "")
    online = False
    if updated_at:
        try:
            last = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            online = (datetime.now(timezone.utc) - last) < timedelta(minutes=20)
        except Exception:
            pass

    return {
        "online": online,
        "updated_at": updated_at,
        "lines": tail.get("lines", []),
        "runs": runs,
    }


CITIZEN_VOICE = HERE / "output" / "citizen_voice.json"
# защита от того, чтобы на дашборд акимата не попали имена частных лиц / токсичные обвинения
_CV_BLOCK = _refix.compile(
    r"врагов народа|гражданк[уиа]\b|привлечь\s+граждан|коррупционер|компромат|чемодан|"
    r"открыть\s+(официальн\w+\s+)?магазин|магазин\w*\s+(lego|лего)|\blego\b|бренд", _refix.I)

def load_citizen_voice(limit=8):
    """«Мнение жителей» (из citizen_voice.py). Отдаём только безопасные поля:
    саммари, настрой, конструктивные предложения. Сырые цитаты НЕ выносим на дашборд."""
    if not CITIZEN_VOICE.exists():
        return []
    try:
        raw = json.loads(CITIZEN_VOICE.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for r in raw[:limit]:
        ins = r.get("insights") or {}
        sugg = [s for s in (ins.get("suggestions") or [])
                if isinstance(s, str) and s.strip() and not _CV_BLOCK.search(s)]
        summary = (ins.get("summary") or "").strip()
        if not summary and not sugg:
            continue
        out.append({
            "post_id": r.get("post_id", ""),
            "post_text": (r.get("post_text") or "")[:220],
            "category": r.get("category", ""),
            "url": r.get("url", ""),
            "replies_total": r.get("replies_total", 0),
            "stance": ins.get("stance", ""),
            "summary": summary,
            "suggestions": sugg[:5],
        })
    return out


TOP_SOLUTIONS = HERE / "output" / "top_solutions.json"

def load_top_solutions(limit=8):
    """Сведённый ИИ топ городских решений (из citizen_voice.py). С тем же скрабом."""
    if not TOP_SOLUTIONS.exists():
        return []
    try:
        raw = json.loads(TOP_SOLUTIONS.read_text(encoding="utf-8"))
    except Exception:
        return []
    out = []
    for t in raw[:limit]:
        title = (t.get("title") if isinstance(t, dict) else str(t)) or ""
        detail = t.get("detail", "") if isinstance(t, dict) else ""
        cat = t.get("category", "") if isinstance(t, dict) else ""
        title = title.strip()
        if not title or _CV_BLOCK.search(title) or _CV_BLOCK.search(detail or ""):
            continue
        out.append({"title": title[:120], "detail": (detail or "")[:160], "category": cat})
    return out


# ── Режим УМП: молодёжь / вузы / общежития / студенты ──────────────────────
_YOUTH_RX = _refix.compile(
    r"университет\w*|\bвуз\w*|институт\w*|академи\w*|колледж\w*|студент\w*|общежит\w*|общаг\w*|кампус\w*|"
    r"стипенди\w*|абитуриент\w*|магистр\w*|бакалавр\w*|деканат\w*|куратор\w*|первокурс\w*|выпускник\w*|"
    r"молод[её]ж\w*|жастар|\bжас\b|жас алматы|школьник\w*|учащ\w*|трудоустрой\w*", _refix.I)

def is_youth(p):
    # в УМП попадают только посты, реально ложащиеся в молодёжную тему
    return ump_category(p.get("text", "") or "") is not None

def _youth_cv(cv):
    out = []
    for c in cv:
        cat = ump_category(c.get("post_text") or "")
        if cat is None:
            continue
        c2 = dict(c); c2["category"] = cat   # молодёжная категория вместо городской
        out.append(c2)
    return out

# ── Молодёжная таксономия (для режима УМП): свой состав категорий ────────────
# Двухступенчатая логика:
#   1) ГЕЙТ: пост вообще про молодёжь/студентов/вузы? (иначе в УМП не попадает)
#   2) Тема внутри молодёжного корпуса.
# Это убирает ложные срабатывания («Карьер Аксай»→карьера, «антистресс»→стресс,
# «учебный год» в посте про пробки, «подача документов в 1 класс»→ЕНТ и т.п.)
_UMP_GATE = _refix.compile(
    r"(?<!трц )студент\w*|университет\w*|\bвуз\w*|колледж\w*|"
    r"общежит\w*|общаг\w*|жатақхан\w*|деканат\w*|первокурс\w*|"
    r"абитуриент\w*|\bент\b|ұбт|магистрант\w*|бакалавр\w*|аспирант\w*|"
    r"молод[её]ж\w*|жастар|жас алматы|старшеклассник\w*|выпускни[кц]\w*|"
    r"студотряд\w*|жасыл ел", _refix.I)

_UMP_RULES = [(c, _refix.compile(r, _refix.I)) for c, r in [
    ("Общежития",                 r"общежит|общаг|жатақхан|заселени|комнат.*общеж"),
    ("Стипендии и гранты",        r"стипенди|\bгрант\w*\b.{0,40}(обучени|студент|образован|вуз)|(обучени|студент|образован).{0,40}\bгрант|оплат[аыу]?\s+.{0,15}обучени|образовательн\w*\s+кредит"),
    ("Поступление и ЕНТ",         r"\bент\b|ұбт|абитуриент|поступ(ать|ить|лени)\w*\s+.{0,25}(вуз|универ|колледж|грант)|(вуз|универ|колледж).{0,25}поступ|проходн\w*\s+балл|приёмн\w*\s+комисси|приемн\w*\s+комисси"),
    ("Трудоустройство молодёжи",  r"трудоустрой|ваканси|стажировк|подработк|карьерн\w*\s+рост|\bрезюме\b|собеседован|\b(работ|найм|наня)\w*.{0,40}\b(студент|молод[её]ж|выпускник)|\b(студент|молод[её]ж|выпускник)\w*.{0,40}\bработ"),
    ("Безопасность и буллинг",    r"буллинг|кибербуллинг|травл[яеию]|издевательств|дедовщин|(насили|домогательств|избиени|нападени|конфликт)\w*.{0,60}(студент|школ|вуз|универ|общежит|подрост)|(студент|школьниц|школьник|подрост)\w*.{0,60}(насили|домогательств|нападени|нападал|избил|угрож)"),
    ("Здоровье и поддержка",      r"психолог|психическ|\bментальн(?!ост)|депресс|\bстресс|выгоран|суицид|тревожн|соцподдержк"),
    ("Учебный процесс и вузы",    r"универ|\bвуз\w*|колледж|деканат|кафедр|преподавател|сесси[яию]|экзамен|зач[её]т|расписани\w*\s+(пар|занят)|качеств\w*\s+.{0,15}образован|аккредитац|диплом\w*|отчислен"),
    ("Досуг и мероприятия",       r"мероприят|фестивал|\bконкурс|волонт[её]р|\bспорт\w*|секци[яию]|кружок|жас алматы|жасыл ел|молод[её]жн\w*\s+(центр|организаци|форум|слёт|слет)|студотряд|\bивент"),
]]

def ump_category(text):
    t = text or ""
    if not _UMP_GATE.search(t):
        return None            # пост не про молодёжь — в УМП не попадает
    for cat, rx in _UMP_RULES:
        if rx.search(t):
            return cat
    return "Молодёжь · общее"  # молодёжный, но без конкретной темы

DEPT.update({
    "Общежития": "УМП / администрации вузов",
    "Трудоустройство молодёжи": "Центр молодёжного трудоустройства · УМП",
    "Стипендии и гранты": "УМП / Управление образования",
    "Поступление и ЕНТ": "Управление образования",
    "Учебный процесс и вузы": "Администрации вузов / Управление образования",
    "Досуг и мероприятия": "УМП / «Жас Алматы»",
    "Безопасность и буллинг": "УМП + Управление образования",
    "Здоровье и поддержка": "Управление общественного здоровья · УМП",
    "Молодёжь · общее": "УМП",
})
RECO.update({
    "Общежития": "Проверить состояние и заселение в упомянутых общежитиях, дать сроки ремонта и ответа жителям.",
    "Трудоустройство молодёжи": "Собрать барьеры трудоустройства, запустить адресные вакансии и стажировки для молодёжи.",
    "Стипендии и гранты": "Разъяснить условия стипендий/грантов и сроки выплат, ответить на конкретные обращения.",
    "Поступление и ЕНТ": "Дать понятную информацию по ЕНТ и поступлению, снять частые вопросы абитуриентов.",
    "Учебный процесс и вузы": "Передать обращения в администрации вузов, проверить упомянутые проблемы учебного процесса.",
    "Досуг и мероприятия": "Учесть запросы молодёжи по мероприятиям и секциям, скоординировать через «Жас Алматы».",
    "Безопасность и буллинг": "Проверить сигналы о буллинге/насилии, подключить психологов и администрацию вуза.",
    "Здоровье и поддержка": "Обеспечить доступ к психологической и социальной поддержке молодёжи.",
    "Молодёжь · общее": "Отработать обращение силами УМП.",
})
DRAFT.update({c: "Обращение{d} принято УМП; профильная служба проверяет ситуацию, о результатах сообщим." for c in
              ["Общежития", "Трудоустройство молодёжи", "Стипендии и гранты", "Поступление и ЕНТ",
               "Учебный процесс и вузы", "Досуг и мероприятия", "Безопасность и буллинг",
               "Здоровье и поддержка", "Молодёжь · общее"]})

# ── LLM-фильтр УМП: локальная Qwen решает, компетенция ли это молодёжной политики ──
# Убирает посты, где «студент/молодёжь» лишь упомянуты, а тема — другая (ДТП, транспорт,
# посольства и т.п.). Кэш: data/ump_cache.json. Модель недоступна → словарный фолбэк.
UMP_CACHE = HERE / "data" / "ump_cache.json"
_UMP_CAT_NAMES = [c for c, _ in _UMP_RULES] + ["Молодёжь · общее"]

_UMP_LLM_SYSTEM = """Ты — фильтр постов для дашборда Управления молодёжной политики (УМП) г. Алматы.
Для каждого поста определи, относится ли его ГЛАВНАЯ ТЕМА к компетенции молодёжной политики.

ump=true, только если главная тема — жизнь и проблемы молодёжи/студентов: общежития; стипендии и
гранты на обучение; поступление и ЕНТ; трудоустройство и стажировки молодёжи; учебный процесс и
вузы; буллинг и безопасность учащихся; ментальное здоровье молодёжи; молодёжные мероприятия,
волонтёрство и досуг.

ump=false, если молодёжь/студенты упомянуты мимоходом, а тема другая: ДТП и происшествия (даже
если пострадали студенты — это полиция, не УМП), транспорт и дороги, международные инциденты и
посольства, общегородские новости и политика, криминальная хроника без школьно-студенческого
контекста, реклама.

Верни строгий JSON {"results":[{"id":"...","ump":true,"category":"..."}]} — по объекту на каждый id.
category выбирай ТОЛЬКО из: Общежития; Стипендии и гранты; Поступление и ЕНТ; Трудоустройство
молодёжи; Безопасность и буллинг; Здоровье и поддержка; Учебный процесс и вузы; Досуг и
мероприятия; Молодёжь · общее. Если ump=false — category=""."""


def _llm_reachable(timeout=4.0):
    import os, socket
    from urllib.parse import urlparse
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    base = os.getenv("LLM_BASE_URL", "")
    if not base:
        return False
    u = urlparse(base)
    host, port = u.hostname, u.port or (443 if u.scheme == "https" else 80)
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ump_llm_filter(all_posts):
    """Прогоняет кандидатов (прошедших гейт) через локальную модель. Возвращает
    {id: {"ump": bool, "category": str}} из кэша+свежих ответов."""
    cache = {}
    if UMP_CACHE.exists():
        try:
            cache = json.loads(UMP_CACHE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    seen, todo = set(), []
    for p in all_posts:
        pid = p.get("id")
        if not pid or pid in seen:
            continue
        seen.add(pid)
        if pid not in cache and _UMP_GATE.search(p.get("text", "") or ""):
            todo.append(p)
    if todo:
        if not _llm_reachable():
            log.warning(f"УМП-LLM: модель недоступна — {len(todo)} новых постов через словарный фолбэк")
        else:
            import os, requests
            try:
                import grok_filter as gf
                api_key = (os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY", "local")).strip() or "local"
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                log.info(f"УМП-LLM: проверяю {len(todo)} постов локальной моделью")
                B = 8
                for i in range(0, len(todo), B):
                    batch = todo[i:i + B]
                    payload = [{"id": p["id"], "text": (p.get("text") or "")[:500]} for p in batch]
                    body = {"model": gf.MODEL,
                            "messages": [{"role": "system", "content": _UMP_LLM_SYSTEM},
                                         {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                            "temperature": 0, "response_format": {"type": "json_object"}}
                    try:
                        r = requests.post(gf.API_URL, headers=headers, json=body, timeout=120)
                        r.raise_for_status()
                        parsed = gf._extract_json(r.json()["choices"][0]["message"]["content"]) or {}
                        for item in parsed.get("results", []):
                            if isinstance(item, dict) and item.get("id"):
                                cat = (item.get("category") or "").strip()
                                cache[item["id"]] = {"ump": bool(item.get("ump")),
                                                     "category": cat if cat in _UMP_CAT_NAMES else ""}
                        UMP_CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
                    except Exception as e:
                        log.warning(f"УМП-LLM: батч {i//B+1} пропущен: {e}")
            except Exception as e:
                log.warning(f"УМП-LLM недоступен: {e}")
    return cache


def _recat_youth(items, llm_map=None):
    out = []
    for p in items:
        rcat = ump_category(p.get("text", "") or "")
        if rcat is None:
            continue                       # не прошёл гейт
        v = (llm_map or {}).get(p.get("id"))
        if v is not None:
            if not v.get("ump"):
                continue                   # LLM: не компетенция УМП
            q = dict(p); q["category"] = v.get("category") or rcat
        else:
            q = dict(p); q["category"] = rcat   # фолбэк: словарные правила
        out.append(q)
    return out

def _render(data, geo, view):
    html = HTML_TEMPLATE.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
    html = html.replace("/*__GEO__*/", json.dumps(geo, ensure_ascii=False) if geo else "null")
    html = html.replace("/*__VIEW__*/", json.dumps(view))
    return html

def _attach(data, cv, tops, scraper):
    data["scraper_status"] = scraper
    data["citizen_voice"] = cv
    data["top_solutions"] = tops
    cvmap = {}
    for c in cv:
        if c.get("post_id"): cvmap[c["post_id"]] = c
        if c.get("url"): cvmap[c["url"]] = c
    for p in (data.get("now24", {}).get("viral_posts") or []):
        v = cvmap.get(p.get("id")) or cvmap.get(p.get("url"))
        if v:
            p["voice"] = {"stance": v["stance"], "summary": v["summary"], "suggestions": v["suggestions"]}
    return data


def main():
    posts, all_feed, stats = load()
    if not posts:
        raise SystemExit("Нет релевантных постов после очистки.")
    log.info(f"Постов для аналитики: {len(posts)}, в ленте: {len(all_feed)}")
    geo = load_geojson()
    scraper = load_scraper_status()
    cv_list = load_citizen_voice()
    tops = load_top_solutions()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # ── УМП (молодёжь / вузы) сначала — чтобы «Город» знал, показывать ли вкладку ──
    has_ump = False
    try:
        llm_map = _ump_llm_filter(list(posts) + list(all_feed))   # локальная Qwen + кэш
        youth = _recat_youth(posts, llm_map)     # молодёжные посты в СВОЕЙ таксономии
        yfeed = _recat_youth(all_feed, llm_map) or youth
        if len(youth) >= 15:
            has_ump = True
            cv_y = _youth_cv(cv_list)
            tops_y = [t for t in tops if _YOUTH_RX.search(t.get("title", "") + " " + t.get("category", ""))]
            ump = _attach(build(youth, yfeed, stats), cv_y, tops_y, scraper)
            # Ручная ИИ-сводка написана по городскому корпусу — для УМП не показываем.
            ump["month_review"] = None
            ump["has_ump"] = True
            (OUT.parent / "ump.html").write_text(_render(ump, geo, "ump"), encoding="utf-8")
            log.info(f"Дашборд (УМП): {OUT.parent / 'ump.html'} — постов молодёжи: {len(youth)}")
        else:
            log.warning(f"УМП: молодёжных постов мало ({len(youth)}) — ump.html пропущен")
    except Exception as e:
        log.error(f"УМП-вариант не собран: {e}")

    # ── ГОРОД (Акимат) → index.html ──
    city = _attach(build(posts, all_feed, stats), cv_list, tops, scraper)
    city["has_ump"] = has_ump
    OUT.write_text(_render(city, geo, "city"), encoding="utf-8")
    log.info(f"Дашборд (город): {OUT}")
    log.info(f"Топ-проблема: {city['problems'][0]['category']} ({city['problems'][0]['count']})"
             if city["problems"] else "нет проблем")


from dashboard_template import HTML_TEMPLATE  # noqa: E402

if __name__ == "__main__":
    main()
