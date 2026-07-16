#!/usr/bin/env python3
"""
threads_login.py — Одноразовый вход в Threads через браузер.

Открывает Chrome (видимый), ты логинишься вручную,
скрипт сохраняет сессию в auth_state.json.

Следующие запуски almaty_monitor.py / run_hourly.py
будут использовать auth_state.json автоматически — без .env и без ввода кук.

Когда обновлять: когда Threads начнёт требовать повторный логин (примерно раз в 90 дней).

Запуск:
    python threads_login.py
"""

import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE       = Path(__file__).parent
STATE_FILE = HERE / "auth_state.json"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def main():
    exe = next((p for p in CHROME_CANDIDATES if os.path.exists(p)), None)

    print("=" * 56)
    print("  Threads Login — сохранение сессии")
    print("=" * 56)
    print(f"  Браузер: {exe or 'Playwright Chromium (встроенный)'}")
    print(f"  Файл сессии: {STATE_FILE}")
    print()
    print("  1. Сейчас откроется браузер (подождите 10–20 сек).")
    print("  2. Войди в threads.com под своим аккаунтом.")
    print("  3. После входа нажми Enter в этом терминале.")
    print()
    print("  ⏳ Запуск браузера...", flush=True)

    # Используем встроенный Chromium — надёжнее системного Chrome
    # (не конфликтует с открытым Chrome, всегда найдёт бинарник)
    launch_kw = dict(
        headless=False,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    # Системный Chrome только если встроенный Chromium не найден
    # (по умолчанию НЕ передаём executable_path — Playwright использует свой Chromium)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_kw)
        print("  ✓ Браузер открыт", flush=True)
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            timezone_id="Asia/Almaty",
        )
        page = ctx.new_page()
        print("  ⏳ Открываю threads.com...", flush=True)
        page.goto("https://www.threads.com/", wait_until="domcontentloaded", timeout=30000)
        print("  ✓ Страница загружена", flush=True)
        print()

        input("  >>> Войди в браузере, затем нажми Enter здесь...")

        # Проверяем, что мы залогинены
        cookies = ctx.cookies()
        session = next((c for c in cookies if c["name"] == "sessionid"), None)

        if not session:
            print("\n  ✖ sessionid не найден — возможно, вход не выполнен.")
            print("    Попробуй снова.")
            browser.close()
            return

        ctx.storage_state(path=str(STATE_FILE))
        browser.close()

    print()
    print(f"  ✓ Сессия сохранена: {STATE_FILE}")
    print(f"  ✓ sessionid: {session['value'][:40]}...")
    print()
    print("  Теперь almaty_monitor.py и run_hourly.py будут работать")
    print("  автоматически без ввода кук (~90 дней).")
    print()
    print("  Когда сессия истечёт — просто запусти threads_login.py снова.")
    print("=" * 56)


if __name__ == "__main__":
    main()
