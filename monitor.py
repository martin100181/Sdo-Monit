import os
import re
from playwright.sync_api import sync_playwright

URL = os.getenv("SALDO_URL", "https://saldo.com.ar/a/usdt/palpal/0/100")

def parse_first_number(text: str) -> float:
    # Devuelve el primer número que encuentre (91.5 / 91,5)
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", text)
    if not m:
        raise RuntimeError(f"No encontré números en: {text!r}")
    return float(m.group(1).replace(",", "."))

def read_envias_usdt(page) -> float:
    page.goto(URL, wait_until="domcontentloaded", timeout=180000)
    page.wait_for_timeout(2500)

    # Espera a que aparezca tether (está en el bloque superior "You send/Envías")
    tether = page.get_by_text(re.compile(r"tether", re.I)).first
    tether.wait_for(timeout=120000)

    # subimos hasta un contenedor que tenga USDT y (Envías o You send)
    container = None
    for i in range(1, 12):
        anc = tether.locator(f"xpath=ancestor::*[{i}]")
        t = anc.inner_text()
        if re.search(r"USDT", t, re.I) and re.search(r"(Env[ií]as|You send)", t, re.I):
            container = anc
            break

    if container is None:
        container = tether.locator("xpath=ancestor::div[1]")

    text = container.inner_text()
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", text)
    if not m:
        raise RuntimeError(f"No encontré el número de USDT en el bloque. Texto: {text!r}")
    return float(m.group(1).replace(",", "."))


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="es-AR",
            extra_http_headers={"Accept-Language": "es-AR,es;q=0.9,en;q=0.8"},
            viewport={"width": 1280, "height": 720},
        )

        page = context.new_page()

        try:
            value = read_envias_usdt(page)
            print(f"ENVIAS_USDT={value}")
        except Exception as e:
            # Evidencia para debug si algo falla
            page.screenshot(path="debug_page.png", full_page=True)
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("ERROR:", repr(e))
            raise
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    main()
