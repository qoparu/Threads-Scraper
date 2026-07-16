"""
Тест поиска по ключевым словам на threads.com/search
"""
import os, sys, json
from urllib.parse import unquote
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

COOKIE_STR = os.getenv("THREADS_COOKIE", "")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def build_cookies(s):
    cookies = []
    for part in s.split(";"):
        part = part.strip()
        if "=" not in part: continue
        name, _, value = part.partition("=")
        for domain in [".threads.com", ".threads.net"]:
            cookies.append({"name": name.strip(), "value": unquote(value.strip()),
                            "domain": domain, "path": "/"})
    return cookies

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=CHROME,
                                  args=["--no-sandbox", "--disable-dev-shm-usage"])
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
        locale="ru-RU",
    )
    ctx.add_cookies(build_cookies(COOKIE_STR))
    page = ctx.new_page()

    # Открываем поиск по ключевому слову
    query = "алматы"
    url = f"https://www.threads.com/search?q={query}&serp_type=default"
    print(f"=== Открываю: {url} ===")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)
    print(f"Title: {page.title()}")
    print(f"URL: {page.url}")

    # Ищем вкладку "Недавние"/"Latest"/"Recent"
    body_text = page.locator("body").inner_text()[:600]
    print(f"\nPage text preview:\n{body_text}")

    # Пробуем кликнуть "Недавние"
    for sel in ['span:has-text("Недавние")', 'span:has-text("Latest")', 'span:has-text("Recent")',
                'a:has-text("Недавние")', '[role="tab"]:has-text("Недавние")']:
        try:
            el = page.locator(sel)
            if el.count() > 0:
                el.first.click()
                page.wait_for_timeout(2000)
                print(f"Кликнул: {sel}")
                break
        except Exception:
            pass

    page.wait_for_timeout(3000)

    # Извлекаем посты из DOM
    posts = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('[data-pressable-container]').forEach(c => {
            const timeEl = c.querySelector('time[datetime]');
            if (!timeEl) return;
            const lines = c.innerText.split('\\n').map(l => l.trim()).filter(l => l);
            results.push({
                username: lines[0] || '',
                text: lines.slice(2, -3).join(' '),
                datetime: timeEl.getAttribute('datetime'),
                inner: c.innerText.substring(0, 300),
            });
        });
        return results;
    }""")

    print(f"\nНайдено постов: {len(posts)}")
    for i, p in enumerate(posts[:5]):
        print(f"\n--- Пост {i+1} ---")
        print(f"username: {p['username']}")
        print(f"datetime: {p['datetime']}")
        print(f"text: {p['text'][:150]}")

    # Скриншот
    page.screenshot(path="screenshot_search.png")
    print("\nСкриншот: screenshot_search.png")

    browser.close()
