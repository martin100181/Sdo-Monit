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

    # Espera a que exista algo característico del bloque superior (tether / USDT)
    # Esto evita depender del texto exacto "Envías USDT"
    page.wait_for_timeout(2000)
    page.wait_for_function(
        "document.body && (document.body.innerText.toLowerCase().includes('tether') || document.body.innerText.toLowerCase().includes('usdt'))",
        timeout=120000,
    )

    # Buscamos "tether" (está en el bloque de Envías) y subimos en el DOM
    tether = page.get_by_text(re.compile(r"tether", re.I)).first
    tether.wait_for(timeout=120000)

    container = None
    # Elegimos el ancestro que contenga "Envías" (o "Envias") pero NO "Recibes"
    for i in range(1, 12):
        anc = tether.locator(f"xpath=ancestor::*[{i}]")
        t = anc.inner_text()
        if re.search(r"Env[ií]as", t, re.I) and not re.search(r"Recibes", t, re.I):
            container = anc
            break

    # Fallback: si por alguna razón no aparece "Envías", usamos un ancestro cercano
    if container is None:
        container = tether.locator("xpath=ancestor::div[1]")

    text = container.inner_text()
    # En tu captura el primer número dentro de este bloque es el "91.5"
    return parse_first_number(text)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            locale="es-AR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
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
