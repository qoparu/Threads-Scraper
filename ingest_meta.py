#!/usr/bin/env python3
"""
ingest_meta.py — Приём и ОЧИСТКА данных Meta Content Library (Facebook + Instagram).

Читает CSV из data/raw/meta/, приводит к единой схеме, ЖЁСТКО чистит мусор:
  • реклама/коммерция (ru+kk), брендированный контент, телефоны/прайсы/«жазыңыз»;
  • не про Алматы (нет упоминания города/районов/локаций);
  • дубликаты, пустые/слишком короткие, чисто ссылочные посты.
Затем лексически размечает категорию, тональность (через реакции FB + словари),
остроту, район; считает охват; и помечает топ-N постов для уточнения через Grok.

Выход: data/meta_clean.json  (релевантные посты с лексической разметкой и полным текстом).
"""

import re
import csv
import sys
import json
import glob
import logging
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
csv.field_size_limit(10 ** 7)
log = logging.getLogger("ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S", stream=sys.stdout)

HERE = Path(__file__).parent
RAW = HERE / "data" / "raw" / "meta"
OUT = HERE / "data" / "meta_clean.json"
GROK_TOP_N = 2500  # сколько релевантных постов отдать на уточнение Grok (гибрид с лимитом)

# ── Релевантность Алматы ──────────────────────────────────────────────────────
ALMATY_RE = re.compile(
    r"алмат|almaty|алма-?ата|медеу|бостандык|ауэзов|алатау|наурызбай|турксиб|жетысу|"
    r"алмалы|шымбулак|шымбұлақ|көк[-\s]?жайляу|кок[-\s]?жайляу|аль[-\s]?фараби|әл[-\s]?фараби|"
    r"достык|достық|абая|сайран|ремизовк|капшагай|қапшағай|алматинск", re.I)
ALMATY_CITY_RE = re.compile(
    r"\u0430\u043b\u043c\u0430\u0442\u044b\u0434\u0430|\u0430\u043b\u043c\u0430\u0442\u044b\u0434\u0435|\u0432\s*\u0430\u043b\u043c\u0430\u0442\u044b|"
    r"\u0433\u043e\u0440\u043e\u0434\s*\u0430\u043b\u043c\u0430\u0442\u044b|\u0430\u043b\u043c\u0430\u0442\u044b\s*\u049b\u0430\u043b\u0430|"
    r"\u043c\u0435\u0434\u0435\u0443|\u0431\u043e\u0441\u0442\u0430\u043d\u0434\u044b\u049b|\u0430\u0443\u044d\u0437\u043e\u0432|\u0430\u043b\u0430\u0442\u0430\u0443|\u043d\u0430\u0443\u0440\u044b\u0437\u0431\u0430\u0439|\u0442\u04af\u0440\u043a\u0441\u0456\u0431|\u0436\u0435\u0442\u0456\u0441\u0443|\u0430\u043b\u043c\u0430\u043b\u044b",
    re.I,
)
ALMATY_OBLAST_RE = re.compile(
    r"\u0430\u043b\u043c\u0430\u0442\u044b\s+\u043e\u0431\u043b\u044b\u0441|\u0430\u043b\u043c\u0430\u0442\u0438\u043d\u0441\u043a\w*\s+\u043e\u0431\u043b\u0430\u0441\u0442",
    re.I,
)
# ── Мусор: реклама/коммерция (ru + kk) ────────────────────────────────────────
JUNK_RE = re.compile(
    r"под заказ|в наличии|рассрочк|кредит|скидк|акци[яи]|промокод|прайс|"
    r"доставка по|бесплатн[аы][яе] консульт|запис(ь|ывайт|аться)|жазыңыз|жазылыңыз|"
    r"нөмірге|номер[ау]? для связи|whats[\s]?app|ватсап|ватсап|телеграм|@[\w.]+ пиши|"
    r"бизнес[\s-]?центр|куплю|продам|сдам|сниму|аренда|арендуй|"
    r"обучени[ея]|вебинар|марафон|розыгрыш|разыгрыва|giveaway|промо[\s-]?код|"
    r"подпишись|переходи по ссылк|успей купить|ограниченн[оа]е предложени|"
    r"бағасы|сатыл|тапсырыс|жеткіз|курс[ыа]?\b|тренинг|коучинг|"
    r"кіру тегін|тегін кіру|вход свободн|вход бесплатн|қолдаңыздар|қолдап жіберіңіз|"
    r"билет.*сатыл|концерт.*билет|сізді күтеміз|күтеміз сізді|розыгрыш|"
    r"₸|тг\b|тенге|теңге|\bкзт\b", re.I)

PHONE_RE = re.compile(r"(?:\+?7|8)[\s\-(]*7\d{2}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")
URLONLY_RE = re.compile(r"^\s*(https?://\S+\s*)+$")

# ── Признаки именно ГОРОДСКОГО сигнала, а не просто упоминания Алматы ────────
ISSUE_RE = re.compile(
    r"жалоб|шағым|проблем|мәселе|нет воды|без воды|су жоқ|суы жоқ|нет света|отключ|"
    r"жарық жоқ|авари|дтп|пожар|өрт|нападени|задержан|полиц|қауіпсіз|"
    r"пробк|затор|ям[аы]|шұңқыр|ремонт|перекры|снос|застрой|стройк|"
    r"мусор|қоқыс|грязь|воняет|смог|загрязн|ауа|выброс|"
    r"очеред|цон|open almaty|тариф|подорожа|цены|пособи|"
    r"больниц|поликлин|скор[аяо]|врач|дәрігер|емхана|"
    r"школ|мектеп|детсад|садик|учител|автобус|метро|троллейбус|остановк|"
    r"доступн\w+ сред|лиф[т]|подъезд|двор|тротуар|светофор|канализац|водоснабж",
    re.I,
)

COMPLAINT_RE = re.compile(
    r"\u0436\u0430\u043b\u043e\u0431|\u0448\u0430\u0493\u044b\u043c|\u0442\u0430\u043b\u0430\u043f|\u0442\u0440\u0435\u0431\u0443|\u043f\u0440\u043e\u0441\u0438\u043c|"
    r"\u043f\u043e\u0447\u0435\u043c\u0443|\u043a\u043e\u0433\u0434\u0430|\u0434\u043e\u043a\u043e\u043b\u0435|\u043d\u0435\s*\u0440\u0430\u0431\u043e\u0442\u0430\u0435\u0442|"
    r"\u043d\u0435\u0442\b|\u0431\u0435\u0437\b|\u0436\u043e\u049b|\u043c\u0430\u0441\u049b\u0430\u0440\u0430|\u0431\u0430\u0440\u0434\u0430\u043a|\u0448\u0435\u0448\u0456\u043c",
    re.I,
)

MUNICIPAL_SERVICE_RE = re.compile(
    r"\u0434\u043e\u0440\u043e\u0433|\u0430\u0432\u0442\u043e\u0431\u0443\u0441|\u043c\u0435\u0442\u0440\u043e|\u0442\u0440\u043e\u043b\u043b\u0435\u0439\u0431\u0443\u0441|\u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043a|"
    r"\u0441\u0432\u0435\u0442\u043e\u0444\u043e\u0440|\u043f\u0430\u0440\u043a\u043e\u0432\u043a|\u0432\u043e\u0434\u0430|\u043a\u0430\u043d\u0430\u043b\u0438\u0437\u0430\u0446|\u0441\u0432\u0435\u0442|\u044d\u043b\u0435\u043a\u0442\u0440|"
    r"\u043e\u0442\u043e\u043f\u043b\u0435\u043d|\u0436\u043a\u0445|\u043a\u043e\u043c\u043c\u0443\u043d\u0430\u043b|\u043b\u0438\u0444\u0442|\u043f\u043e\u0434\u044a\u0435\u0437\u0434|\u0434\u0432\u043e\u0440|"
    r"\u0441\u043c\u043e\u0433|\u0432\u043e\u0437\u0434\u0443\u0445|\u0432\u044b\u0431\u0440\u043e\u0441|\u043c\u0443\u0441\u043e\u0440|\u0443\u0431\u043e\u0440\u043a|\u0441\u0432\u0430\u043b\u043a|\u0437\u0430\u0441\u0442\u0440\u043e\u0439|"
    r"\u0441\u043d\u043e\u0441|\u0441\u0442\u0440\u043e\u0439\u043a|\u0431\u043e\u043b\u044c\u043d\u0438\u0446|\u043f\u043e\u043b\u0438\u043a\u043b\u0438\u043d|\u0432\u0440\u0430\u0447|\u0441\u043a\u043e\u0440\u0430\u044f|"
    r"\u0448\u043a\u043e\u043b|\u043c\u0435\u043a\u0442\u0435\u043f|\u0434\u0435\u0442\u0441\u0430\u0434|\u0446\u043e\u043d|open almaty|\u0442\u0430\u0440\u0438\u0444|\u0446\u0435\u043d\u044b|\u043f\u043e\u0441\u043e\u0431\u0438|"
    r"\u043f\u043e\u043b\u0438\u0446|\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d|\u0430\u0432\u0430\u0440\u0438|\u043f\u043e\u0436\u0430\u0440",
    re.I,
)

POLITICS_RE = re.compile(
    r"\u043f\u043e\u043b\u0438\u0442|\u0430\u043a\u0442\u0438\u0432\u0438\u0441\u0442|\u043c\u0438\u0442\u0438\u043d\u0433|\u043f\u0438\u043a\u0435\u0442|\u043c\u0435\u043c\u043e\u0440\u0438\u0430\u043b|"
    r"\u0441\u0443\u0434|\u0430\u043f\u0435\u043b\u043b\u044f\u0446|\u0431\u043b\u043e\u0433\u0435\u0440|\u0437\u0430\u04a3\u0441\u044b\u0437|\u04d9\u043a\u0456\u043c\u0448\u0456\u043b\u0456\u043a|\u049b\u044b\u043b\u043c\u044b\u0441\u0442\u044b\u049b",
    re.I,
)

FOREIGN_PLACE_RE = re.compile(
    r"belarus|беларус|минск|uruchye|украин|росси[ия]|рф\b|одесс|сидни|sydney",
    re.I,
)
ENTERTAINMENT_RE = re.compile(
    r"әнші|актрис|певиц|шо[уы][-\s]?бизнес|жұлдыз|бортсерік|бортсеріктер|ұшақта|самолет.*скандал",
    re.I,
)

NON_CIVIC_RE = re.compile(
    r"симпозиум|kongress|конгресс|форум|выставк|премьер|концерт|той\b|"
    r"театр|музей|фильм|сериал|пастор|церков|шіркеу|намаз|дін|религи|"
    r"истори|тарих|мероприят|мереке|фестиваль|петици[яи].*переимен|"
    r"есімін.*өзгерт|имя.*измен|блогер.*есім|поздрав|құттықт|"
    r"открытие арт|арт-нысан|арт-объект|юбиле|тур|путешеств|Olymp|олимпиад",
    re.I,
)

# ── Категории (ru + kk ключевые слова) ────────────────────────────────────────
CATS = [
    ("Дороги и транспорт", r"\bдорог[аиуе]\b|дорожн|автодорог|пробк|затор|общественн\w+ транспорт|"
                           r"автобус|троллейбус|\bметро\b|такси|тротуар|перекрёст|перекрест|"
                           r"көлік|разворот|парковк|светофор|развязк|\bмаршрут|\bbrt\b|\bлрт\b|остановк|"
                           r"әуежай|аэропорт|\bавиа|ұшу-қону|рейс\b|самолёт|самолет"),
    ("ЖКХ и инфраструктура", r"жкх|отоплени|батаре|подъезд|лифт|труб[аы]|прорыв|коммуналь|"
                             r"кск|опс|тепло|канализац(?!.*вода)|жек"),
    ("Вода и канализация", r"водоснабж|водопровод|канализац|нет воды|без воды|прорыв.*вод|"
                           r"питьев\w+ вод|сточн\w+ вод|ауыз\s*су|таза\s*су|су\s*жоқ|суы\s*жоқ|"
                           r"су\s*тапшыл|сумен\s*жабды|кәріз"),
    ("Безопасность и правопорядок", r"полиц|кримин|кража|грабёж|\bдрак|стрельб|нападени|дтп|авари|"
                                    r"пожар|чп\b|задержа|мошенн|қауіпсіз|ұрлық|төбелес|"
                                    r"суицид|самоубийств|өзін-өзі өлтір|"
                                    r"электрошокер|\bшокер|тазер|репресс|қуғын|саяси аштық|"
                                    r"мемориал.*жертв|\bмитинг|\bпикет|протест(?!ир)|демонстрац(?!ир|ионн)|"
                                    r"аштық.*саяси|жоғалт.*адам|саяси тұтқын"),
    ("Электроснабжение", r"электроснаб|электроэнерг|электросет|электр\w* отключ|отключ\w* электр|"
                         r"подстанц|энергоснаб|обесточ|перепад\w* напряж|напряжени в сет|"
                         r"свет отключ|отключ\w* свет|нет света|света нет|свет погас|свет пропал|"
                         r"перебо\w* (?:с )?(?:электр|свет)|жарық жоқ|жарық өш|ток кет|электр қуат|қуатсыз"),
    ("Экология и воздух", r"эколог|воздух|смог|выброс|загрязн|пыль|\bауа\b|экологи|зелён|деревь|вырубк"),
    ("Благоустройство и мусор", r"мусор|свалк|урн[аы]|убор[ккн]|грязь|тазалық|тазалык|қоқыс|"
                                r"благоустрой|газон|клумб|освещени"),
    ("Строительство и застройка", r"стройк|строительств|застрой|снос|新|долёвк|дольщ|жилой комплекс|"
                                   r"\bжк\b|реконструкц|самострой|многоэтаж|құрылыс"),
    ("Здравоохранение", r"больниц|поликлин|врач|медиц|скорая|аптек|вакцин|денсаулық|дәрігер|емхана"),
    ("Образование", r"школ|детсад|садик|гимназ|универ|студент|ент\b|учител|білім|мектеп|оқушы|колледж"),
    ("Госуслуги и бюрократия", r"open almaty|цон\b|егов|госуслуг|акимат|әкімдік|әкім|чиновник|"
                               r"бюрократ|очеред[ьи]|справк[аи]|отписк"),
    ("Цены и социальные вопросы", r"цены|подорожа|тариф|инфляц|пособи|пенси|зарплат|бедност|"
                                  r"баspirit|әлеумет|жәрдемақы|бағаны"),
]
CAT_RE = [(name, re.compile(p, re.I)) for name, p in CATS]

# ── Негатив (ru + kk) ─────────────────────────────────────────────────────────
NEG_RE = re.compile(
    r"проблем|жалоб|безобраз|беспредел|ужас|отврат|кошмар|возмут|требуем|почему|доколе|"
    r"опасн|авари|погиб|пострада|мусор|грязь|вон[яи]|невозможн|бардак|хуже|плохо|"
    r"недовол|игнор|отписк|обман|разруш|разочаров|стыд|позор|"
    r"мәселе|шағым|нашар|қорқыныш|жаман|ұят|аварии", re.I)
POS_RE = re.compile(r"спасибо|благодар|рахмет|рақмет|отличн|прекрасн|молодц|красив|"
                    r"супер|раду|восхищ|жақсы|керемет|тамаша|ұнады", re.I)

DISTRICTS = [
    ("Алмалинский", r"алмалинск|алмалы"),
    ("Ауэзовский", r"ауэзов|ауезов|әуезов"),
    ("Бостандыкский", r"бостандык|бостандық|орбита|ремизовк|сайран"),
    ("Жетысуский", r"жетысу|жетісу"),
    ("Медеуский", r"медеу|медео|шымбулак|шымбұлақ|көк[-\s]?жайляу|кок[-\s]?жайляу|достык|достық"),
    ("Наурызбайский", r"наурызбай|наурызбайск"),
    ("Турксибский", r"турксиб|түрксіб"),
    ("Алатауский", r"алатау|алатаус"),
]
DIST_RE = [(n, re.compile(p, re.I)) for n, p in DISTRICTS]

MEDIA_HINT = re.compile(r"news|новост|media|медиа|tv\b|tengri|nur\.|zakon|kz\b|газет|press|жаңалық|"
                        r"informburo|orda|vlast|kursiv|inform", re.I)


def to_int(v):
    try:
        return int(float(v))
    except Exception:
        return 0


def parse_dt(s):
    if not s:
        return None
    s = s.strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T", 1))
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:len(fmt) + 2], fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue
    return None


def owner_tier(platform, otype, name):
    name = name or ""
    if MEDIA_HINT.search(name):
        return "Медиа/СМИ"
    if platform == "Facebook":
        return "Организация/страница" if otype == "page" else "Гражданин"
    # Instagram
    return {"business": "Бизнес/бренд", "creator": "Блогер/креатор",
            "personal": "Гражданин"}.get(otype, "Гражданин")


def classify(text):
    for name, rx in CAT_RE:
        if rx.search(text):
            return name
    return "Прочее"


def district_of(text):
    for name, rx in DIST_RE:
        if rx.search(text):
            return name
    return ""


def sentiment_fb(text, reac):
    ang = reac["angry"] + reac["sad"]
    good = reac["love"] + reac["care"]
    neg_lex = len(NEG_RE.findall(text))
    pos_lex = len(POS_RE.findall(text))
    if ang > good and ang >= 1:
        return "негатив"
    if neg_lex > pos_lex and neg_lex >= 1:
        return "негатив"
    if good > ang * 2 or pos_lex > neg_lex:
        return "позитив"
    return "нейтрально"


def sentiment_lex(text):
    n, p = len(NEG_RE.findall(text)), len(POS_RE.findall(text))
    return "негатив" if n > p and n >= 1 else "позитив" if p > n and p >= 1 else "нейтрально"


def severity(text, sentiment, eng):
    s = 2
    if sentiment == "негатив":
        s = 3
    strong = len(re.findall(r"беспредел|ужас|невозможн|требуем|опасн|погиб|авари|бардак|позор|доколе", text, re.I))
    if strong >= 1:
        s = 4
    if strong >= 2 or (sentiment == "негатив" and eng > 500):
        s = 5
    return s


def is_junk(text):
    if JUNK_RE.search(text):
        return True
    if PHONE_RE.search(text):
        return True
    if URLONLY_RE.match(text):
        return True
    return False


def read_csv(path):
    plat = "Facebook" if "facebook" in path.name else "Instagram"
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(fh):
            yield plat, row


def post_link(plat, row):
    """Возвращает ссылку на пост. Для Facebook строим публичный permalink из id владельца
    и id поста; для Instagram публичного permalink в выгрузке нет — используем ссылку
    Content Library (mcl_url)."""
    mcl = (row.get("mcl_url") or "").strip()
    owner_id = (row.get("post_owner.id") or "").strip()
    post_id = (row.get("id") or "").strip()
    if plat == "Facebook" and owner_id and post_id:
        return f"https://www.facebook.com/permalink.php?story_fbid={post_id}&id={owner_id}", mcl
    return mcl, mcl


def normalize(plat, row):
    text = (row.get("text") or "").strip()
    url, mcl = post_link(plat, row)
    reac = {k: to_int(row.get(f"statistics.{k}_count")) for k in
            ("angry", "sad", "love", "care", "haha", "wow")}
    likes = to_int(row.get("statistics.like_count"))
    comments = to_int(row.get("statistics.comment_count"))
    shares = to_int(row.get("statistics.share_count"))
    views = to_int(row.get("statistics.views"))
    dt = parse_dt(row.get("creation_time"))
    return {
        "id": f"{plat[:2]}_{row.get('id','')}",
        "platform": plat,
        "lang": (row.get("lang") or "").strip() or "—",
        "owner_name": (row.get("post_owner.name") or row.get("surface.name") or "").strip(),
        "owner_type": (row.get("post_owner.type") or "").strip(),
        "created_at": dt.isoformat() if dt else "",
        "likes": likes, "comments": comments, "shares": shares,
        "reactions": reac, "views": views,
        "hashtags": (row.get("hashtags") or "").strip(),
        "url": url, "mcl_url": mcl,
        "text": text,
        "is_branded": str(row.get("is_branded_content", "")).lower() in ("true", "1"),
    }


def engagement(p):
    return p["likes"] + p["comments"] + p["shares"] + sum(p["reactions"].values())


CORE_CIVIC_CATEGORIES = {name for name, _ in CATS}


def is_oblast_only(text):
    return bool(ALMATY_OBLAST_RE.search(text) and not ALMATY_CITY_RE.search(text))


def has_complaint_signal(text):
    return bool(COMPLAINT_RE.search(text) or ISSUE_RE.search(text))


def is_nonlocal_or_media_noise(text, owner_name=""):
    if FOREIGN_PLACE_RE.search(text) and not ALMATY_CITY_RE.search(text):
        return True
    if ENTERTAINMENT_RE.search(text) and not (ALMATY_CITY_RE.search(text) or MUNICIPAL_SERVICE_RE.search(text)):
        return True
    if (owner_name or "").lower() in {"zerkalo_io"} and not ALMATY_CITY_RE.search(text):
        return True
    return False


def is_civic_issue(text, category, issue_signal, complaint_signal):
    if is_oblast_only(text):
        return False
    if issue_signal:
        return True
    if category in CORE_CIVIC_CATEGORIES and complaint_signal:
        return True
    if category in CORE_CIVIC_CATEGORIES and MUNICIPAL_SERVICE_RE.search(text):
        return True
    return False


def accept(p, plat, kept, seen, stats, require_almaty=True, min_len=60):
    """Единый фильтр+разметка для одного нормализованного поста (Meta или Threads)."""
    text = p["text"]
    if p.get("is_branded"):
        stats["branded"] += 1; return False
    if len(text) < min_len or URLONLY_RE.match(text):
        stats["short"] += 1; return False
    if require_almaty and not (ALMATY_RE.search(text) or ALMATY_RE.search(p.get("hashtags", ""))):
        stats["not_almaty"] += 1; return False
    if is_oblast_only(text):
        stats["not_almaty"] += 1; return False
    if is_junk(text):
        stats["junk"] += 1; return False
    if is_nonlocal_or_media_noise(text, p.get("owner_name", "")):
        stats["offtopic"] += 1; return False
    key = (p["owner_name"][:40] + "|" + re.sub(r"\s+", " ", text).lower()[:140])
    if key in seen:
        stats["dup"] += 1; return False
    seen.add(key)
    eng = engagement(p)
    sentiment = sentiment_fb(text, p["reactions"]) if plat == "Facebook" else sentiment_lex(text)
    cat = classify(text)
    issue_signal = bool(ISSUE_RE.search(text))
    complaint_signal = has_complaint_signal(text)
    is_complaint = complaint_signal and (issue_signal or bool(NEG_RE.search(text)))
    civic_issue = is_civic_issue(text, cat, issue_signal, complaint_signal)
    if POLITICS_RE.search(text) and not MUNICIPAL_SERVICE_RE.search(text):
        stats["offtopic"] += 1; return False
    # ?? ?????????????? ?????????????????? ???? ?????????? ???????????? ??????????????/??????????????/????????????????/??????????????,
    # ???????? ?? ???????????? ?????? ???????????? ???????????????????? ??????????????, ???????????????? ?????? service issue.
    if NON_CIVIC_RE.search(text) and not MUNICIPAL_SERVICE_RE.search(text):
        stats["offtopic"] += 1; return False
    # ???????? ??????????????????????????: ???????????? ?????????????????? ????????????/????????????, ?? ???? ?????????? ???????????????????? ????????????.
    if not civic_issue:
        stats["offtopic"] += 1; return False
    if not is_complaint and p.get("owner_type") in {"page", "business", "creator"} and not issue_signal:
        stats["offtopic"] += 1; return False
    p["category"] = cat
    p["sentiment"] = sentiment
    p["severity"] = severity(text, sentiment, eng)
    p["district"] = district_of(text)
    p["tier"] = owner_tier(plat, p.get("owner_type", ""), p["owner_name"])
    p["is_complaint"] = is_complaint and p["severity"] >= 3
    p["theme"] = ""
    p["summary"] = ""
    p["engagement"] = eng
    p["grok_done"] = False
    kept.append(p)
    return True


def normalize_threads(tp):
    text = (tp.get("text") or "").strip()
    url = (tp.get("url") or "").strip()
    dt = parse_dt(tp.get("created_at"))
    likes = int(tp.get("like_count") or 0)
    comments = int(tp.get("reply_count") or 0)
    shares = int(tp.get("repost_count") or 0)
    # На Threads иногда проскальзывают фантомные DOM-счётчики.
    # Для городских обращений значения в десятки миллионов нереалистичны, поэтому
    # такие выбросы режем до 0, чтобы не ломать ранжирование и "охват".
    if likes > 1_000_000:
        likes = 0
    if comments > 1_000_000:
        comments = 0
    if shares > 1_000_000:
        shares = 0
    return {
        "id": "TH_" + str(tp.get("id", "")), "platform": "Threads",
        "lang": "kk" if len(re.findall(r"[әғқңөұүһі]", text.lower())) > 3 else "ru",
        "owner_name": (tp.get("username") or "").strip(), "owner_type": "",
        "created_at": dt.isoformat() if dt else (tp.get("created_at") or ""),
        "likes": likes, "comments": comments, "shares": shares,
        "reactions": {k: 0 for k in ("angry", "sad", "love", "care", "haha", "wow")},
        "views": 0, "hashtags": "", "url": url, "mcl_url": url, "text": text, "is_branded": False,
    }


def ingest_threads(kept, seen, stats):
    """Подмешивает свежие посты Threads (output/almaty_threads_*.json) в общий корпус.
    Threads уже собран по тематике Алматы → не требуем повторного упоминания города."""
    outs = sorted(glob.glob(str(HERE / "output" / "almaty_threads_*.json")))
    if not outs:
        log.info("Threads: свежих выгрузок нет (output/almaty_threads_*.json) — пропускаю.")
        return
    data = json.loads(Path(outs[-1]).read_text(encoding="utf-8"))
    n = 0
    for tp in data:
        stats["total"] += 1
        if accept(normalize_threads(tp), "Threads", kept, seen, stats,
                  require_almaty=False, min_len=30):
            n += 1
    log.info(f"  Threads ({Path(outs[-1]).name}): прочитано {len(data)}, принято {n}")


def main():
    files = sorted(glob.glob(str(RAW / "*.csv")))
    log.info(f"CSV-файлов Meta: {len(files)}")

    kept, seen = [], set()
    stats = Counter()
    for path in files:
        path = Path(path)
        cnt = 0
        for plat, row in read_csv(path):
            cnt += 1
            stats["total"] += 1
            accept(normalize(plat, row), plat, kept, seen, stats)
        log.info(f"  {path.name}: прочитано {cnt}")

    # Threads — свежие посты из скрапера
    ingest_threads(kept, seen, stats)

    # На AI-проверку (Grok): ВСЕ посты Threads (свежий гражданский сигнал) + топ-N Meta
    # по остроте/охвату. Остальной длинный хвост Meta остаётся на лексике.
    ranked = sorted(kept, key=lambda x: (x["severity"], x["engagement"]), reverse=True)
    for i, p in enumerate(ranked):
        p["grok_todo"] = (i < GROK_TOP_N) or (p["platform"] == "Threads")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(kept, ensure_ascii=False), encoding="utf-8")
    (OUT.parent / "meta_stats.json").write_text(
        json.dumps({k: stats[k] for k in stats} | {"kept": len(kept),
                   "grok_planned": min(GROK_TOP_N, len(kept))}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    log.info("─" * 50)
    log.info(f"Всего постов:        {stats['total']}")
    log.info(f"Брендированных:      {stats['branded']}")
    log.info(f"Короткие/ссылки:     {stats['short']}")
    log.info(f"Не про Алматы:       {stats['not_almaty']}")
    log.info(f"Реклама/коммерция:   {stats['junk']}")
    log.info(f"Оффтоп (не гражд.):  {stats['offtopic']}")
    log.info(f"Дубликаты:           {stats['dup']}")
    log.info(f"ОСТАЛОСЬ (чистых):   {len(kept)}")
    log.info(f"На уточнение Grok:   {min(GROK_TOP_N, len(kept))}")
    log.info(f"→ {OUT}")


if __name__ == "__main__":
    main()
