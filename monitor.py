import os
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = os.getenv("SALDO_URL", "https://saldo.com.ar/en-US/a/usdt/paypal/0/100")


def read_envias_usdt(page) -> float:
    page.goto(URL, wait_until="networkidle", timeout=180000)

    # Esperar que cargue cualquier input del cotizador
    page.wait_for_selector("input", timeout=60000)

    page.wait_for_timeout(2000)

    usdt_value = page.evaluate("""
        () => {
            const isVisible = el =>
                !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);

            const clean = v =>
                parseFloat(v.replace(",", "."));

            const inputs = Array.from(document.querySelectorAll("input"))
                .filter(isVisible);

            for (const input of inputs) {
                const container = input.closest("div, section, article") || document.body;
                const text = container.innerText.toLowerCase();

                if (text.includes("usdt") || text.includes("tether")) {
                    const val = input.value;
                    if (/^[0-9]+([.,][0-9]+)?$/.test(val)) {
                        return clean(val);
                    }
                }
            }

            return null;
        }
    """)

    if not usdt_value:
        raise RuntimeError("No se pudo encontrar el valor USDT")

    return usdt_value


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

        context = browser.new_context(
            locale="es-AR",
            viewport={"width": 1280, "height": 800}
        )

        page = context.new_page()

        try:
            envias = read_envias_usdt(page)
            print(f"ENVIAS_USDT={envias}")

        except (PlaywrightTimeoutError, Exception) as e:
            try:
                page.screenshot(path="debug_page.png", full_page=True)
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except:
                pass
            print("ERROR:", repr(e))
            raise

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
