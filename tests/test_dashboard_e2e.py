import subprocess
import time
import sys
from pathlib import Path

import pytest
import requests

STREAMLIT_PORT = 8502
STREAMLIT_URL = f"http://localhost:{STREAMLIT_PORT}"
PROJECT_ROOT = Path(__file__).parent.parent
STREAMLIT_SCRIPT = PROJECT_ROOT / "src" / "dashboard.py"
TIMEOUT = 300


def _wait_for_streamlit(page):
    page.locator("h1").first.wait_for(state="visible", timeout=120000)
    spinners = page.locator('[data-testid="stSpinner"]')
    if spinners.count() > 0:
        spinners.first.wait_for(state="hidden", timeout=300000)
    page.wait_for_function(
        "() => document.querySelectorAll('[data-testid=\"stPlotlyChart\"]').length >= 1",
        timeout=300000
    )


@pytest.fixture(scope="session")
def streamlit_server():
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(STREAMLIT_SCRIPT),
         "--server.port", str(STREAMLIT_PORT),
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false",
         "--server.enableCORS", "false",
         "--server.enableXsrfProtection", "false"],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    start = time.time()
    while time.time() - start < TIMEOUT:
        try:
            r = requests.get(STREAMLIT_URL, timeout=5)
            if r.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(2)
    else:
        proc.kill()
        raise RuntimeError("Streamlit server did not start in time")

    yield

    proc.kill()
    proc.wait()


@pytest.fixture(scope="session")
def session_page(playwright, streamlit_server):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(120000)
    page.goto(STREAMLIT_URL)
    _wait_for_streamlit(page)
    yield page
    context.close()
    browser.close()


def test_dashboard_loads(session_page):
    heading = session_page.locator("h1").first
    assert "Brazilian Stocks" in heading.text_content()


def test_entity_selector(session_page):
    sidebar = session_page.locator('[data-testid="stSidebar"]')
    sidebar.wait_for(state="visible", timeout=60000)
    sidebar_text = sidebar.inner_text()
    assert any(t in sidebar_text for t in ["PETR4", "VALE3", "ITUB4", "BBDC4"])


def test_kpi_cards_render(session_page):
    metrics = session_page.locator('[data-testid="stMetric"]')
    metrics.first.wait_for(state="visible", timeout=120000)
    count = metrics.count()
    assert count >= 3

    labels = [metrics.nth(i).locator("label").text_content() for i in range(count)]
    joined = " ".join(labels)
    assert "Retorno Acum." in joined
    assert "All-Time High" in joined


def test_tab_navigation(session_page):
    tabs = session_page.locator('button[data-baseweb="tab"]')
    tabs.first.wait_for(state="visible", timeout=60000)
    count = tabs.count()
    assert count >= 5

    tab_names = [tabs.nth(i).text_content() for i in range(count)]
    joined = " ".join(tab_names)
    assert "Overview" in joined
    assert "EDA" in joined
    assert "Forecast" in joined
    assert "Anomalias" in joined


def test_overview_charts(session_page):
    assert session_page.locator('[data-testid="stPlotlyChart"]').count() >= 2


@pytest.fixture(scope="function")
def fresh_page(session_page):
    context = session_page.context
    page = context.new_page()
    page.set_default_timeout(60000)
    page.goto(STREAMLIT_URL)
    page.locator("h1").first.wait_for(state="visible", timeout=30000)
    page.wait_for_timeout(2000)
    yield page
    page.close()


def test_decomp_tab(session_page):
    tab = session_page.locator('button[data-baseweb="tab"]').nth(2)
    tab.wait_for(state="visible", timeout=30000)
    tab.click(force=True, timeout=15000)
    session_page.wait_for_load_state("networkidle", timeout=30000)
    session_page.get_by_text("Modelo detectado").wait_for(state="visible", timeout=30000)


@pytest.mark.xfail(reason="Streamlit tab re-render on second switch does not render full content; #known_issue")
def test_anomalies_tab_only(fresh_page):
    fresh_page.wait_for_timeout(5000)
    tab = fresh_page.locator('button[data-baseweb="tab"]').nth(5)
    tab.wait_for(state="visible", timeout=30000)
    tab.focus()
    fresh_page.wait_for_timeout(1000)
    tab.click(force=True, timeout=15000)
    fresh_page.wait_for_function(
        "() => document.querySelector('button[data-baseweb=\"tab\"][aria-selected=\"true\"]') !== null",
        timeout=30000
    )
    fresh_page.wait_for_timeout(5000)
    fresh_page.get_by_role("heading", name="Outliers em Lote").wait_for(
        state="visible", timeout=30000
    )


def test_screenshot(session_page):
    session_page.screenshot(path="dashboard_screenshot.png", full_page=True)
    assert Path("dashboard_screenshot.png").stat().st_size > 10000
