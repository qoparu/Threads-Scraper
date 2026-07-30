# JasPulse — мониторинг соцсетей г. Алматы

Сбор публичных постов из Threads (+ опционально Facebook/Instagram через Meta Content
Library) по теме Алматы → фильтрация рекламы/ботов/офтопа → data-driven дашборд городских
проблем, обновляемый по расписанию.

**Живой дашборд:** ссылка появится после первого деплоя (см. «Автозапуск» ниже).

## Как это устроено

```
almaty_monitor.py     скрапер Threads (Playwright) — хэштеги + поиск, антибот/антиреклама фильтры
run_hourly.py          раннер: TOP-фаза + RECENT-фаза → output/threads_live.json → деплой
merge_and_deploy.py    мёрж Threads + Meta-данных → пересборка дашборда → деплой на Vercel
ingest_meta.py         приём CSV-выгрузок Meta Content Library (FB/IG), опционально
build_dashboard.py     вся аналитика/агрегация → JSON-данные для дашборда
dashboard_template.py  весь HTML/CSS/JS дашборда (единственный файл, отвечающий за дизайн)
```

Подробнее об архитектуре дашборда, метриках и фильтрации — в
[`README_DASHBOARD.md`](README_DASHBOARD.md).

## Быстрый старт (локально)

Нужен Python 3.11+, куки авторизованной сессии Threads.

```bash
git clone https://github.com/qoparu/Threads-Scraper.git
cd Threads-Scraper

python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install --with-deps chromium
```

Кука Threads — см. [`ИНСТРУКЦИЯ.md`](ИНСТРУКЦИЯ.md) (как достать через DevTools). Положи в `.env`:

```
LOG_LEVEL=INFO
THREADS_COOKIE=<кука>
```

Разовый прогон:

```bash
python run_hourly.py
```

Результаты — в `output/` (JSON/CSV), лог — в `logs/`.

## Автозапуск (раз в час, без привязки к компьютеру)

**Вариант A — GitHub Actions (рекомендуется, бесплатно для публичного репо).**
Workflow уже настроен: [`.github/workflows/hourly-scrape.yml`](.github/workflows/hourly-scrape.yml)
крутится по расписанию на GitHub-раннерах. Нужно один раз добавить секреты в
Settings → Secrets and variables → Actions:

| Secret | Откуда |
|---|---|
| `THREADS_COOKIE` | DevTools, см. `ИНСТРУКЦИЯ.md` |
| `VERCEL_TOKEN` | vercel.com/account/tokens |
| `VERCEL_ORG_ID` / `VERCEL_PROJECT_ID` | `cat public/.vercel/project.json` после `npx vercel link` |
| `GROQ_API_KEY` | опционально, для AI-фильтрации топ-постов |

Проверить запуск вручную: вкладка **Actions** → workflow → **Run workflow**.

**Вариант B — свой сервер/VPS** (если нужен постоянный процесс вне GitHub, например для
Meta-данных/большого кэша). Инструкция — [`deploy/DEPLOY_SERVER.md`](deploy/DEPLOY_SERVER.md),
установка одной командой — `bash deploy/setup.sh` (ставит venv, Chromium, systemd-таймер).

Перенос между машинами (что переносить руками, что через git) — [`deploy/ПЕРЕНОС.md`](deploy/ПЕРЕНОС.md).

## Безопасность

- `.env`, `auth_state.json`, `data/` — никогда не коммитятся (см. `.gitignore`), передаются
  вручную (scp/флешка) или через секреты CI.
- Если кука/токен где-то засветились (чат, скриншот, публичный лог) — считай их
  скомпрометированными и создай новые.

## Лицензия

MIT — см. [`LICENSE`](LICENSE).
