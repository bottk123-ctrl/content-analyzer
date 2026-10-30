#!/usr/bin/env python
"""Снимок дашборда для README через Playwright.

Скрипт поднимает Streamlit на свободном порту, загружает ``data/sample.csv``
в file_uploader, ждёт отрисовку графиков и сохраняет full-page скриншот в
``assets/screenshot.png`` (светлая тема) и ``assets/screenshot-dark.png``
(тёмная тема).

Запуск::

    python scripts/screenshot.py

Требуется однократная установка:

    pip install playwright
    python -m playwright install chromium
"""

from __future__ import annotations

import contextlib
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "sample.csv"
OUT_LIGHT = ROOT / "assets" / "screenshot.png"
OUT_DARK = ROOT / "assets" / "screenshot-dark.png"

# Настройки съёмки.
VIEWPORT = {"width": 1500, "height": 950}
SCALE = 2
SETTLE_MS = 1500


def _free_port() -> int:
    """Свободный TCP-порт для Streamlit."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_health(url: str, timeout: float = 90.0) -> None:
    """Ждём, пока Streamlit начнёт отвечать на health-check."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:  # noqa: BLE001
            time.sleep(0.4)
    raise RuntimeError(f"Streamlit не поднялся за {timeout:.0f} c")


def _bg_color(page) -> str:
    """Вычисленный цвет фона приложения (для проверки смены темы)."""
    return page.evaluate(
        "() => getComputedStyle(document.querySelector('.stApp')).backgroundColor"
    )


def _capture(page, switch_to: str | None, out: Path) -> None:
    """Переключаем тему (если нужно), ждём отрисовку и сохраняем скриншот."""
    if switch_to is not None:
        before = _bg_color(page)
        # Сегмент-контрол темы рендерится как stButtonGroup (кнопки role=radio).
        page.locator(
            '[data-testid="stButtonGroup"] button', has_text=switch_to
        ).click()
        # Ждём, пока фон реально изменится.
        for _ in range(30):
            if _bg_color(page) != before:
                break
            page.wait_for_timeout(200)
        else:
            print(f"  ! предупреждение: тема «{switch_to}» не переключилась")
        page.wait_for_timeout(600)

    # Ждём KPI-карточки и оба графика Plotly.
    page.wait_for_selector(".ca-kpi", timeout=30000)
    page.wait_for_selector('[data-testid="stPlotlyChart"] .js-plotly-plot',
                           timeout=30000)
    # Даём анимациям и Plotly дорисоваться.
    page.wait_for_timeout(SETTLE_MS)

    # У Streamlit прокрутка идёт во внутреннем контейнере, поэтому full_page
    # не захватывает контент ниже вьюпорта. Измеряем реальную высоту и
    # подгоняем размер вьюпорта, чтобы всё поместилось.
    content_height = page.evaluate(
        """() => {
            const sels = [
                '[data-testid="stMain"]',
                'section.stMain',
                'main',
                '[data-testid="stAppViewContainer"]',
                '.stApp',
            ];
            let h = 0;
            for (const s of sels) {
                const el = document.querySelector(s);
                if (el) h = Math.max(h, el.scrollHeight);
            }
            return Math.max(h, document.body.scrollHeight);
        }"""
    )
    target = min(int(content_height) + 40, 8000)
    page.set_viewport_size({"width": VIEWPORT["width"], "height": target})
    page.wait_for_timeout(SETTLE_MS)

    out.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out), full_page=True)
    print(f"  сохранено: {out.relative_to(ROOT)}")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        print("Playwright не установлен. Выполните:\n"
              "  pip install playwright\n"
              "  python -m playwright install chromium", file=sys.stderr)
        return 1

    if not CSV.exists():
        print(f"Нет файла с данными: {CSV}", file=sys.stderr)
        return 1

    port = _free_port()
    url = f"http://localhost:{port}"
    print(f"Запускаю Streamlit на {url} …")

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
            "--server.headless", "true",
            "--server.port", str(port),
            "--browser.gatherUsageStats", "false",
        ],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        _wait_health(url)

        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport=VIEWPORT, device_scale_factor=SCALE
            )
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_selector('[data-testid="stApp"]', timeout=30000)

            # Источник данных по умолчанию — «CSV-файл» (пользователь не
            # залогинен), поэтому загрузчик уже виден. На всякий случай
            # выбираем радио явно.
            with contextlib.suppress(Exception):
                page.get_by_role("radio", name="CSV-файл").check()
                page.wait_for_timeout(400)

            # Загружаем пример данных.
            page.locator('input[type="file"]').first.set_input_files(str(CSV))

            print("Снимаю светлую тему …")
            _capture(page, None, OUT_LIGHT)

            print("Снимаю тёмную тему …")
            _capture(page, "Тёмная", OUT_DARK)

            browser.close()
    finally:
        proc.terminate()
        with contextlib.suppress(Exception):
            proc.wait(timeout=10)

    print("Готово.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
