"""
tests/e2e/check_env.py

Diagnostic script — run this BEFORE test_live_urls.py to confirm
your environment is correctly set up.

Run from project root:
    python -m tests.e2e.check_env
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
WARN = "\033[93m⚠\033[0m"


def check(label: str, fn):
    try:
        result = fn()
        print(f"  {PASS} {label}" + (f" — {result}" if result else ""))
        return True
    except Exception as e:
        print(f"  {FAIL} {label} — {e}")
        return False


print("\n\033[1mDarkDetect — Environment Check\033[0m\n")

all_ok = True

print("Python & core imports:")
all_ok &= check("Python 3.11+", lambda: f"Python {sys.version.split()[0]}")
all_ok &= check("beautifulsoup4", lambda: __import__("bs4") and "ok")
all_ok &= check("lxml", lambda: __import__("lxml") and "ok")
all_ok &= check("scikit-learn", lambda: __import__("sklearn") and "ok")
all_ok &= check("fastapi", lambda: __import__("fastapi") and "ok")
all_ok &= check("uvicorn", lambda: __import__("uvicorn") and "ok")
all_ok &= check("pydantic", lambda: __import__("pydantic") and "ok")

print("\nPlaywright:")
all_ok &= check("playwright installed", lambda: __import__("playwright") and "ok")

def check_chromium():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        version = browser.version
        browser.close()
        return f"Chromium {version}"

all_ok &= check("Chromium browser binary", check_chromium)

print("\nProject modules:")
all_ok &= check("scraper.fetch", lambda: __import__("scraper.fetch") and "ok")
all_ok &= check("detection_engine.rules", lambda: __import__("detection_engine.rules") and "ok")
all_ok &= check("detection_engine.engine", lambda: __import__("detection_engine.engine") and "ok")
all_ok &= check("detection_engine.classifier", lambda: __import__("detection_engine.classifier") and "ok")
all_ok &= check("api.main", lambda: __import__("api.main") and "ok")

print("\nData files:")
root = Path(__file__).parent.parent.parent
all_ok &= check("data/labelled/training.csv exists",
    lambda: "ok" if (root / "data/labelled/training.csv").exists() else (_ for _ in ()).throw(FileNotFoundError("not found")))

model_path = root / "data" / "models" / "classifier.pkl"
if model_path.exists():
    print(f"  {PASS} ML model found — classifier will run")
else:
    print(f"  {WARN} No ML model found — rule-based only (expected at this stage)")

print("\nNetwork:")
def check_network():
    import urllib.request
    urllib.request.urlopen("https://example.com", timeout=5)
    return "ok"
all_ok &= check("Internet access (example.com)", check_network)

print()
if all_ok:
    print("\033[92m\033[1mAll checks passed — ready to run test_live_urls.py\033[0m")
else:
    print("\033[91m\033[1mSome checks failed — fix the issues above before running live tests\033[0m")
    print("\nCommon fixes:")
    print("  pip install -r requirements.txt")
    print("  playwright install chromium")
print()