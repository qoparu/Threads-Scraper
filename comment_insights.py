#!/usr/bin/env python3
"""
comment_insights.py — «Мнение жителей» из комментариев под резонансным постом.

Двухступенчато:
  1) hard_filter() — дёшево режет спам, ботов, эмодзи-онли, «воду», дубли (без ИИ).
  2) analyze()     — локальный Qwen вытаскивает КОНСТРУКТИВ: предложения жителей,
                     общий настрой, короткое саммари, показательные (анонимные) цитаты.

Запуск демо:  python comment_insights.py   (прогон на встроенном примере)
"""
import os, re, json, sys, requests
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from dotenv import load_dotenv
load_dotenv()
import grok_filter as gf  # переиспользуем API_URL / MODEL / _extract_json

# ── 1. Жёсткий фильтр (до ИИ) ────────────────────────────────────────────────
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF←-➿⬀-⯿]")
_SPAM  = re.compile(r"(https?://|t\.me/|whatsapp|ватсап|вотсап|пишите?\s*(в\s*)?(лс|личк)|"
                    r"заработ|инвест|казино|ставк[аи]|промокод|скидк|достав(ка|ляем)|недорого|звоните|прайс|"
                    r"таргет|тикток|подписчик|followers|продвижен|раскрут|клиент(ов|ы)|заявк|маркетинг|реклам|"
                    r"жаз(ыңыз)?\b|поток клиент|бесплатно.{0,20}(модел|обучени))", re.I)
_BOTNAME = re.compile(r"(bot\b|_bot|_kz\b|shop|store|sale|magazin|dostavka|service_|news\d)", re.I)

def hard_filter(comments):
    seen, kept = set(), []
    dropped = {"spam": 0, "bot": 0, "emoji": 0, "short": 0, "dup": 0}
    for c in comments:
        text = (c.get("text") or "").strip()
        user = (c.get("username") or "")
        if _BOTNAME.search(user): dropped["bot"] += 1; continue
        if _SPAM.search(text):    dropped["spam"] += 1; continue
        letters = re.sub(r"[^\w]", "", _EMOJI.sub("", text))
        if len(letters) < 3 and _EMOJI.search(text): dropped["emoji"] += 1; continue
        if len(letters) < 10: dropped["short"] += 1; continue      # "+", "согласен", "ужас"
        key = " ".join(text.lower().split())[:60]
        if key in seen: dropped["dup"] += 1; continue
        seen.add(key)
        kept.append({"username": user, "text": text})
    return kept, dropped

# ── 2. Извлечение конструктива локальной моделью ─────────────────────────────
SYSTEM = """Ты — аналитик обращений граждан для акимата г. Алматы.
На вход — комментарии жителей под резонансным постом. Выдели КОНСТРУКТИВ и настроение.
Верни СТРОГИЙ JSON:
{
 "summary": "2-3 предложения: что жители в целом думают и что предлагают",
 "stance": "поддержка|раскол|возмущение|нейтрально",
 "suggestions": ["конкретное предложение/решение жителей", "..."],
 "notable_quotes": ["короткая показательная цитата дословно, без имён", "..."]
}
Правила: только то, что РЕАЛЬНО есть в комментариях (не выдумывай). В suggestions — до 5 пунктов,
только реальные КОНСТРУКТИВНЫЕ предложения. Предложения должны быть ПО ТЕМЕ поста и в КОМПЕТЕНЦИИ
городских властей (ЖКХ, транспорт, безопасность, экология, благоустройство, соцвопросы, госуслуги).
НЕ включай узкие коммерческие/брендовые просьбы (открыть магазин конкретного бренда и т.п.), рекламу и оффтоп.
ЗАПРЕЩЕНО: называть конкретных частных лиц по имени, оскорбления, разжигание розни, токсичные/политические выпады.
Формулируй обезличенно и по делу. В notable_quotes — до 2, только вежливые/содержательные. Пиши по-русски."""

def analyze(comments_kept, post_text=""):
    api_key = (os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY", "local")).strip() or "local"
    user_msg = ("Резонансный пост:\n" + (post_text or "—")[:500] +
                "\n\nКомментарии жителей:\n" +
                json.dumps([c["text"] for c in comments_kept], ensure_ascii=False, indent=1))
    body = {"model": gf.MODEL,
            "messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": user_msg}],
            "temperature": 0.2, "response_format": {"type": "json_object"}}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    r = requests.post(gf.API_URL, headers=headers, json=body, timeout=120)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    return gf._extract_json(content) or {"raw": content}

SYNTH_SYSTEM = """Ты — аналитик для акимата г. Алматы. На вход — список предложений/решений,
которые жители оставляли в комментариях под разными резонансными постами города.
Сведи их в ТОП городских решений: объедини похожие, убери дубли и воду, переформулируй как
конкретные меры уровня города. Отсортируй по значимости и частоте упоминания.
Верни СТРОГИЙ JSON: {"solutions":[{"title":"краткая мера","detail":"1 предложение пояснения","category":"тема"}]}
— до 8 пунктов. Только меры В КОМПЕТЕНЦИИ ГОРОДА; без брендов, рекламы, коммерческих и оффтоп-просьб.
ЗАПРЕЩЕНО: имена частных лиц, оскорбления, токсичность, политические выпады. По-русски."""

def synthesize_top_solutions(suggestions):
    """Сводит все предложения жителей в ранжированный топ городских решений (один вызов модели)."""
    suggestions = [s for s in suggestions if isinstance(s, str) and s.strip()]
    if not suggestions:
        return []
    api_key = (os.getenv("GROQ_API_KEY") or os.getenv("GROK_API_KEY", "local")).strip() or "local"
    body = {"model": gf.MODEL,
            "messages": [{"role": "system", "content": SYNTH_SYSTEM},
                         {"role": "user", "content": "Предложения жителей:\n" + json.dumps(suggestions, ensure_ascii=False)}],
            "temperature": 0.2, "response_format": {"type": "json_object"}}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        r = requests.post(gf.API_URL, headers=headers, json=body, timeout=120)
        r.raise_for_status()
        parsed = gf._extract_json(r.json()["choices"][0]["message"]["content"]) or {}
        return parsed.get("solutions", []) if isinstance(parsed, dict) else []
    except Exception as e:
        print("synthesize_top_solutions:", e)
        return []

def insights(post_text, comments):
    kept, dropped = hard_filter(comments)
    result = analyze(kept, post_text) if kept else {"summary": "нет содержательных комментариев"}
    return {"kept": len(kept), "dropped": dropped, "insights": result}

# ── Демо ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    POST = "Третий день нет воды в мкр Орбита, Бостандыкский район. Никто не объясняет, когда включат."
    COMMENTS = [
        {"username": "aigerim_a", "text": "Та же беда на Навои, воды нет с понедельника. Хотя бы предупреждали заранее через СМС!"},
        {"username": "d.serik",   "text": "Сделайте нормальный график отключений на сайте акимата, чтобы люди заранее знали"},
        {"username": "nurlan99",  "text": "😡😡😡"},
        {"username": "gulmira",   "text": "Ужас, сколько можно уже"},
        {"username": "askar_t",   "text": "Поставьте хотя бы подвоз воды в такие дни, особенно для семей с детьми"},
        {"username": "money_kz",  "text": "Заработок из дома от 80.000тг в день, пишите в личку!"},
        {"username": "b_zhan",    "text": "+"},
        {"username": "meruert",   "text": "Нужен телеграм-бот, куда вбиваешь адрес и видишь статус аварии и сроки"},
        {"username": "s.karim",   "text": "У нас в том году так же было, потом трубу меняли почти неделю"},
        {"username": "arman_kz",  "text": "Согласен полностью"},
        {"username": "dana.k",    "text": "Пусть Алматы Су публикует сроки восстановления, а не молчит"},
        {"username": "santeh_shop","text": "Скидки на сантехнику, доставка по Алматы, ватсап 87071234567"},
        {"username": "ruslan",    "text": "Работаю до 7, а воду дают днём когда никого нет дома — можно вечером включать?"},
        {"username": "aliya",     "text": "🚰💧😭"},
        {"username": "timur_a",   "text": "Почему нельзя заранее предупреждать в домовых чатах через КСК?"},
        {"username": "erlan",     "text": "Бардак как всегда"},
        {"username": "zhuldyz",   "text": "Дайте рабочий телефон горячей линии Алматы Су, никто не берёт трубку"},
        {"username": "voda_service_kz", "text": "Ремонт труб недорого, звоните"},
        {"username": "dana.k",    "text": "Пусть Алматы Су публикует сроки восстановления, а не молчит"},
    ]
    res = insights(POST, COMMENTS)
    print("Всего комментов:", len(COMMENTS))
    print("Отсеяно (жёсткий фильтр):", res["dropped"], "→ осталось:", res["kept"])
    print("\n===== МНЕНИЕ ЖИТЕЛЕЙ (из локальной модели) =====")
    print(json.dumps(res["insights"], ensure_ascii=False, indent=2))
