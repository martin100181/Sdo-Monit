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

import re

def read_envias_usdt(page) -> float:
    # Carga normal (sin tocar "Siguiente")
    page.goto(URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2500)

    # Encontrar el texto "Envías USDT" (con o sin tilde)
    label = page.get_by_text(re.compile(r"Env[ií]as\s+USDT", re.I)).first
    label.wait_for(timeout=30000)

    # Subimos en el DOM hasta encontrar un contenedor que también tenga "tether"
    container = None
    for i in range(1, 8):
        anc = label.locator(f"xpath=ancestor::*[{i}]")
        try:
            if anc.get_by_text(re.compile(r"tether", re.I)).count() > 0:
                container = anc
                break
        except Exception:
            pass

    # Fallback: si no encontramos "tether", usamos un ancestro cercano
    if container is None:
        container = label.locator("xpath=ancestor::div[1]")

    # Extraemos texto del contenedor y sacamos el primer número (ej: 91.5)
    text = container.inner_text()
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", text)
    if not m:
        raise RuntimeError(f"No encontré número dentro del bloque 'Envías USDT'. Texto visto: {text!r}")

    return float(m.group(1).replace(",", "."))

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        value = read_envias_usdt(page)
        browser.close()

    print(f"ENVÍAS_USDT={value}")

if __name__ == "__main__":
    main()
