#!/usr/bin/env python3
"""
run_pipeline.py — Конвейер дашборда акимата (Meta Content Library: FB + Instagram).

Шаги:
  1. ingest_meta.py     — приём CSV из data/raw/meta/ + ЖЁСТКАЯ очистка  → data/meta_clean.json
  2. grok_filter.py     — (опц., --grok) уточнение топ-N постов моделью Grok
  3. build_dashboard.py — сборка                                        → public/index.html

Запуск:
    python run_pipeline.py            # очистка + сборка (лексика, бесплатно, быстро)
    python run_pipeline.py --grok     # + уточнение топ-N через Grok (нужен GROK_API_KEY)

Деплой: см. deploy.ps1 / README_DASHBOARD.md
"""
import sys
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
PY = sys.executable


def step(title, args):
    print("\n" + "=" * 60 + f"\n▶ {title}\n" + "=" * 60)
    if subprocess.run([PY, *args], cwd=HERE).returncode != 0:
        sys.exit(f"✖ Шаг провален: {title}")


def main():
    step("1/3 Очистка данных Meta (FB + Instagram)", ["ingest_meta.py"])
    if "--grok" in sys.argv:
        step("2/3 Уточнение топ-N постов через Grok", ["grok_filter.py"])
    step("3/3 Сборка дашборда", ["build_dashboard.py"])
    print("\n✓ Готово. Дашборд: public/index.html")
    print("  Деплой:  powershell -ExecutionPolicy Bypass -File deploy.ps1")


if __name__ == "__main__":
    main()
