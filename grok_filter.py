#!/usr/bin/env python3
"""
grok_filter.py — Жёсткая фильтрация и классификация постов через LLM
(любой OpenAI-совместимый провайдер — DeepSeek, Groq, локальный vLLM).

Заменяет старую фильтрацию по ключевым словам. Для каждого поста модель решает:
  • относится ли пост к ГОРОДСКИМ ПРОБЛЕМАМ Алматы, важным акимату;
  • это спам/реклама/флуд/оффтоп — или реальный сигнал;
  • категория, тема, острота, район, краткая суть для чиновника.

Использование:
    LLM_API_KEY=sk-...            в Threads-Scraper/.env
    LLM_BASE_URL=https://api.deepseek.com/v1
    LLM_MODEL=deepseek-chat
    python grok_filter.py  output/almaty_threads_XXXX.json

Результат: data/classified.json  (исходные посты + поле grok с классификацией).
Кэш по id поста, чтобы не платить за повторные вызовы.
Названия grok_cache.json/grok_done — историческое (первый провайдер был Grok),
поле хранит результат ЛЮБОГО настроенного через LLM_BASE_URL провайдера.
"""

import os
import re
import sys
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

log = logging.getLogger("grok_filter")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S", stream=sys.stdout)

# Провайдер LLM — OpenAI-совместимый эндпоинт (DeepSeek / Groq / vLLM / любой).
# DeepSeek:  LLM_BASE_URL=https://api.deepseek.com/v1  LLM_MODEL=deepseek-chat
# Groq:      LLM_BASE_URL=https://api.groq.com/openai/v1  LLM_MODEL=llama-3.3-70b-versatile
# Локальный: LLM_BASE_URL=http://10.100.200.199:2000/v1
API_BASE = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
API_URL = API_BASE.rstrip("/") + "/chat/completions"
MODEL = os.getenv("LLM_MODEL", os.getenv("GROK_MODEL", "llama-3.3-70b-versatile"))
# API-ключ: LLM_API_KEY — основное имя; GROQ_API_KEY/GROK_API_KEY — для обратной совместимости.
# Для локального vLLM достаточно "local" или любой строки.
API_KEY_ENV = (os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
               or os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY", "local"))
_IS_LOCAL = "localhost" in API_BASE or "127.0.0.1" in API_BASE or "10." in API_BASE
BATCH_SIZE = 8 if _IS_LOCAL else 12   # меньше батч для локальной модели (32k ctx)
HERE = Path(__file__).parent
CACHE_PATH = HERE / "data" / "grok_cache.json"

# Канонические категории для акимата
CATEGORIES = [
    "Дороги и транспорт",
    "ЖКХ и инфраструктура",
    "Вода и канализация",
    "Электроснабжение",
    "Экология и воздух",
    "Благоустройство и мусор",
    "Строительство и застройка",
    "Безопасность и правопорядок",
    "Здравоохранение",
    "Образование",
    "Госуслуги и бюрократия",
    "Цены и социальные вопросы",
    "Прочее",
]

DISTRICTS = [
    "Алмалинский", "Ауэзовский", "Бостандыкский", "Жетысуский",
    "Медеуский", "Наурызбайский", "Турксибский", "Алатауский",
]

SYSTEM_PROMPT = f"""Ты — аналитик акимата г. Алматы. Классифицируй посты соцсетей. Отвечай только JSON.

relevant=true ТОЛЬКО если пост — реальная городская тема Алматы (дороги, транспорт, ЖКХ, вода,
свет, экология/воздух, мусор, застройка/снос, безопасность, поликлиники/больницы, школы/детсады,
госуслуги Open Almaty/ЦОН, тарифы/цены, аварии, парки, доступная среда).

relevant=false (жёстко): реклама/продажи/услуги/курсы/вакансии; личные объявления (психолог,
визажист, продам/сдам квартиру); похудение/диеты/БАДы/эзотерика/подкасты; питомцы; посты НЕ про
Алматы (Астана, другие страны, общие рассуждения), даже если «Алматы» упомянут вскользь;
иностранный язык, боты, мемы, флуд; новости/религия/философия без привязки к городским службам.

relevant=false ТАКЖЕ (важно!): ирония, сарказм, шутки, каламбуры, игра слов, стёб, троллинг,
риторические вопросы ради хайпа/лайков; развлекательные «приколы» без реального запроса к городу.
Признак: пост набирает охват не как обращение, а как шутка/мем; нет конкретной проблемы, адреса
или просьбы. Пример НЕ берём: «Чисто теоретически я донор на Сатпаева?» — это каламбур, не сигнал.
Если пост не требует реакции городской службы и читается как юмор — relevant=false.

is_paid_promo=true — заказные/проплаченные/накрученные: скрытая реклама под видом мнения/жалобы,
призывы «записывайтесь/в личку/по номеру», прайсы, «2 филиала», «топ-мастер», промо-контакты,
шаблонная заказная критика/похвала. В отчёт акимата такие НЕ берём.

САРКАЗМ/ИЗДЁВКА с положительной оболочкой — это КРИТИКА, а НЕ позитив. Если пост хвалит власти/
город идеализированной историей, а в конце разворачивает её в отрицание/насмешку («…Народ счастлив.
Как зовут акима? Его не существует», «какой прекрасный город… в мечтах», «спасибо, что ничего не
сделали»), то sentiment=негатив (НИКОГДА не позитив). Такая саркастичная критика обычно relevant=true
(реальное недовольство горожан). Позитив ставь ТОЛЬКО при искренней, неироничной благодарности/похвале.

Сомневаешься — relevant=false.

Категории (ровно одна): {", ".join(CATEGORIES)}.
Районы (если есть привязка, иначе ""): {", ".join(DISTRICTS)}.

Для каждого поста верни объект:
{{"id","relevant":bool,"is_almaty":bool,"is_spam_or_ad":bool,"is_paid_promo":bool,
"category":"<категория>","theme":"<3-7 слов>","severity":1-5,
"sentiment":"негатив"|"нейтрально"|"позитив","lang":"ru"|"kk"|"other",
"is_complaint":bool,"district":"<район|>","summary":"<1 фраза сути>"}}

Ответ строго: {{"results":[...]}} без markdown."""


def load_cache() -> Dict[str, dict]:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, dict]):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _extract_json(content: str) -> Optional[dict]:
    """Достаёт JSON из ответа, даже если модель обернула его в текст/```."""
    content = content.strip()
    content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.MULTILINE).strip()
    try:
        return json.loads(content)
    except Exception:
        pass
    m = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


# ── Фидбек модератора (👍/👎 на дашборде) → few-shot примеры для промпта ────────

REDIS_URL = os.getenv("REDIS_URL", "")


def _fetch_feedback_examples(limit: int = 15) -> str:
    """Тянет HGETALL feedback:up / feedback:down из Redis и собирает блок few-shot примеров."""
    if not REDIS_URL:
        return ""

    try:
        import redis  # noqa: WPS433
        client = redis.from_url(REDIS_URL, socket_timeout=5, decode_responses=True)
    except Exception as e:
        log.warning(f"Не удалось подключиться к Redis: {e}")
        return ""

    def _hgetall(key: str) -> List[dict]:
        try:
            raw = client.hgetall(key)
            items = []
            for v in raw.values():
                try:
                    items.append(json.loads(v))
                except Exception:
                    continue
            return items[-limit:]
        except Exception as e:
            log.warning(f"Не удалось получить фидбек ({key}): {e}")
            return []

    bad = _hgetall("feedback:down")
    good = _hgetall("feedback:up")
    if not bad and not good:
        return ""

    def _fmt(items: List[dict]) -> str:
        lines = []
        for it in items:
            text = (it.get("text") or "")[:150].replace("\n", " ")
            lines.append(f'- "{text}" — категория: {it.get("category","")}, тема: {it.get("theme","")}')
        return "\n".join(lines)

    block = "\n\nДополнительные примеры от модератора (учитывай обязательно):\n"
    if bad:
        block += "НЕ собирать такие посты (relevant=false), даже если похожи на городскую тему:\n" + _fmt(bad) + "\n"
    if good:
        block += "Собирать больше таких постов (relevant=true), похожих по теме/тону:\n" + _fmt(good) + "\n"
    return block


def classify_batch(batch: List[dict], api_key: str, system_prompt: str, retries: int = 3) -> Dict[str, dict]:
    """Классифицирует пачку постов. Возвращает {id: classification}."""
    payload_posts = [
        {"id": p["id"], "text": p.get("text", "")[:600]}
        for p in batch
    ]
    user_msg = (
        "Классифицируй посты ниже. Верни JSON {\"results\":[...]} с объектом на каждый id.\n\n"
        + json.dumps(payload_posts, ensure_ascii=False)
    )
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(API_URL, headers=headers, json=body, timeout=120)
            if r.status_code == 429:
                wait = 5 * attempt
                log.warning(f"  429 rate limit, жду {wait}с…")
                time.sleep(wait)
                continue
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
            parsed = _extract_json(content)
            if not parsed or "results" not in parsed:
                log.warning(f"  Не разобрал ответ (попытка {attempt})")
                continue
            out = {}
            for item in parsed["results"]:
                if isinstance(item, dict) and item.get("id"):
                    out[item["id"]] = item
            return out
        except requests.HTTPError as e:
            log.error(f"  HTTP {r.status_code}: {r.text[:300]}")
            if r.status_code in (401, 403):
                raise SystemExit("LLM API: ключ неверный или нет доступа. Проверь LLM_API_KEY в .env")
            time.sleep(3 * attempt)
        except Exception as e:
            log.warning(f"  Ошибка запроса (попытка {attempt}): {e}")
            time.sleep(3 * attempt)
    log.error("  Пачка не классифицирована после всех попыток")
    return {}


def classify_posts(posts: List[dict]) -> List[dict]:
    api_key = (API_KEY_ENV or "local").strip() or "local"
    if not _IS_LOCAL and api_key == "local":
        raise SystemExit(
            "LLM_API_KEY не задан. Добавь в .env:\n"
            "  LLM_API_KEY=sk-...  LLM_BASE_URL=https://api.deepseek.com/v1  (DeepSeek)\n"
            "  или LLM_BASE_URL=http://10.100.200.199:2000/v1 (локальный сервер)"
        )
    log.info(f"LLM: {API_BASE}  model={MODEL}  {'(локальный vLLM)' if _IS_LOCAL else '(облако)'}")

    feedback_block = _fetch_feedback_examples()
    if feedback_block:
        log.info("Учитываю фидбек модератора (Vercel KV) в промпте")
    system_prompt = SYSTEM_PROMPT + feedback_block

    cache = load_cache()
    todo = [p for p in posts if p["id"] not in cache]
    log.info(f"Постов всего: {len(posts)} | в кэше: {len(posts)-len(todo)} | к классификации: {len(todo)}")

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        log.info(f"Grok [{MODEL}] пачка {i//BATCH_SIZE + 1} ({len(batch)} постов)…")
        res = classify_batch(batch, api_key, system_prompt)
        for p in batch:
            cache[p["id"]] = res.get(p["id"], {
                "id": p["id"], "relevant": False, "is_almaty": False,
                "is_spam_or_ad": True, "is_paid_promo": False, "category": "Прочее",
                "theme": "", "severity": 1, "sentiment": "нейтрально", "lang": "ru",
                "is_complaint": False, "district": "",
                "summary": "Не удалось классифицировать",
            })
        save_cache(cache)
        time.sleep(1)

    enriched = []
    for p in posts:
        g = cache.get(p["id"], {})
        q = dict(p)
        q["grok"] = g
        enriched.append(q)
    return enriched


CAT_CANON = set(CATEGORIES)


def enrich_meta():
    """Уточняет топ-N постов (grok_todo) в data/meta_clean.json результатами Grok:
    перезаписывает категорию/остроту/тональность/район/тему/резюме, помечает заказное."""
    clean_path = HERE / "data" / "meta_clean.json"
    if not clean_path.exists():
        raise SystemExit(f"Нет {clean_path}. Сначала: python ingest_meta.py")
    posts = json.loads(clean_path.read_text(encoding="utf-8"))
    todo = [p for p in posts if p.get("grok_todo") and not p.get("grok_done")]
    log.info(f"Постов в корпусе: {len(posts)} | к уточнению Grok: {len(todo)}")
    if not todo:
        log.info("Нечего уточнять (нет grok_todo).")
        return

    api_key = (API_KEY_ENV or "local").strip() or "local"
    if not _IS_LOCAL and api_key == "local":
        raise SystemExit("LLM_API_KEY не задан в .env")
    cache = load_cache()

    feedback_block = _fetch_feedback_examples()
    if feedback_block:
        log.info("Учитываю фидбек модератора (Vercel KV) в промпте")
    system_prompt = SYSTEM_PROMPT + feedback_block

    for i in range(0, len(todo), BATCH_SIZE):
        batch = todo[i:i + BATCH_SIZE]
        miss = [p for p in batch if p["id"] not in cache]
        if miss:
            log.info(f"Grok [{MODEL}] {i+1}-{i+len(batch)} из {len(todo)}…")
            res = classify_batch(miss, api_key, system_prompt)
            for p in miss:
                cache[p["id"]] = res.get(p["id"], {})
            save_cache(cache)
            time.sleep(1)
        for p in batch:
            g = cache.get(p["id"], {})
            p["grok_done"] = True
            if not g:
                continue
            # заказное/реклама/нерелевантное → пометить на удаление из дашборда
            if g.get("is_paid_promo") or g.get("is_spam_or_ad") or (g.get("is_almaty") is False) \
                    or (g.get("relevant") is False):
                p["drop"] = True
                continue
            if g.get("category") in CAT_CANON:
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

    clean_path.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")
    dropped = sum(1 for p in posts if p.get("drop"))
    log.info(f"Готово. Уточнено: {len(todo)} | помечено заказным/мусором: {dropped}")
    log.info(f"→ {clean_path}")


def main():
    enrich_meta()


if __name__ == "__main__":
    main()
