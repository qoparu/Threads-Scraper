#!/usr/bin/env python3
"""
refresh.py — Обновление дашборда из свежих выгрузок Meta Content Library (FB/IG).

Без API. Сценарий:
  1. Ты экспортируешь свежие данные из Content Library (веб-интерфейс) и кладёшь
     CSV в data/raw/meta/  (имя файла ДОЛЖНО содержать "facebook" или "instagram").
  2. Запускаешь:
       python refresh.py            — пересобрать дашборд локально
       python refresh.py --deploy   — пересобрать И задеплоить на Vercel
       python refresh.py --no-ai    — без AI-проверки (быстрее; если ИИ-сервер недоступен)

Шаги: ingest_meta (CSV + Threads → meta_clean.json) → grok_filter (AI, если доступен)
      → build_dashboard (public/index.html) → [--deploy] Vercel.
"""

import os
import sys
import glob
import time
import socket
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = Path(__file__).parent


def banner(t):
    print("\n" + "=" * 56 + f"\n  {t}\n" + "=" * 56, flush=True)


def llm_reachable(timeout=4.0):
    """Быстрая проверка, что ИИ-сервер отвечает, чтобы не висеть 120с на батч."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass
    base = os.getenv("LLM_BASE_URL", "")
    if not base:
        return False
    u = urlparse(base)
    host = u.hostname
    port = u.port or (443 if u.scheme == "https" else 80)
    if not host:
        return False
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def main(deploy: bool, use_ai: bool):
    t0 = time.time()

    csvs = glob.glob(str(HERE / "data" / "raw" / "meta" / "*.csv"))
    fb = [c for c in csvs if "facebook" in Path(c).name.lower()]
    ig = [c for c in csvs if "instagram" in Path(c).name.lower()]
    print(f"Выгрузки в data/raw/meta/: Facebook={len(fb)}, Instagram={len(ig)}", flush=True)
    if not csvs:
        print("⚠ Нет CSV в data/raw/meta/ — FB/IG будут пустыми. Положи выгрузки Content Library.", flush=True)

    banner("1/4 · Приём выгрузок Meta (FB/IG) + Threads → meta_clean.json")
    import ingest_meta
    ingest_meta.main()

    banner("2/4 · AI-проверка и классификация")
    if not use_ai:
        print("Пропущено (--no-ai). Классификация — словарная.", flush=True)
    elif not llm_reachable():
        print("⚠ ИИ-сервер недоступен (нет связи с LLM_BASE_URL). Пропускаю AI-шаг.", flush=True)
        print("  Дашборд соберётся на словарной классификации — это нормально.", flush=True)
        print("  Подключись к внутренней сети и перезапусти, если нужна AI-проверка.", flush=True)
    else:
        try:
            import grok_filter
            grok_filter.main()
            print("AI-проверка выполнена.", flush=True)
        except Exception as e:
            print(f"⚠ AI-проверка прервалась: {e}. Продолжаю на словарной классификации.", flush=True)

    banner("3/4 · Сборка дашборда → public/index.html")
    import build_dashboard
    build_dashboard.main()

    if deploy:
        banner("4/4 · Деплой на Vercel")
        from merge_and_deploy import deploy_vercel
        ok = deploy_vercel()
        print("Деплой:", "OK" if ok else "не удался — см. лог выше", flush=True)
    else:
        banner("4/4 · Деплой пропущен")
        print("Локально готово: public/index.html", flush=True)
        print("Чтобы выложить — добавь флаг:  python refresh.py --deploy", flush=True)

    print(f"\nГотово за {time.time() - t0:.0f} c.", flush=True)


if __name__ == "__main__":
    main(deploy="--deploy" in sys.argv, use_ai="--no-ai" not in sys.argv)
