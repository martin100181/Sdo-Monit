import os
import re
from playwright.sync_api import sync_playwright

URL = os.getenv("SALDO_URL", "https://saldo.com.ar/a/usdt/palpal/0/100")

def parse_number(s: str) -> float:
    s = s.strip().replace("\u00a0", " ")
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", s)
    if not m:
        raise ValueError(f"No pude parsear número desde: {s!r}")
    return float(m.group(1).replace(",", "."))

def read_envias_usdt(page) -> float:
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(1500)

    candidates = [
        "xpath=//*[contains(normalize-space(.), 'Envías') and contains(normalize-space(.), 'USDT')]/following::input[1]",
        "xpath=//label[contains(., 'Envías') and contains(., 'USDT')]/following::input[1]",
        "xpath=//*[contains(normalize-space(.), 'Envías') and contains(normalize-space(.), 'USDT')]//input",
    ]

    last_err = None
    for sel in candidates:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=20000)
            raw = loc.input_value()
            if raw and raw.strip():
                return parse_number(raw)
        except Exception as e:
            last_err = e

    body = page.inner_text("body")
    m = re.search(r"Envías.*?([0-9]+(?:[.,][0-9]+)?)\s*USDT", body, re.I | re.S)
    if m:
        return parse_number(m.group(1))

    raise RuntimeError(f"No pude encontrar el valor de 'Envías USDT'. Último error: {last_err}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        value = read_envias_usdt(page)
        browser.close()

    print(f"ENVÍAS_USDT={value}")

if __name__ == "__main__":
    main()
