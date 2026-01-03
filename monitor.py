import os
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = os.getenv("SALDO_URL", "https://saldo.com.ar/a/usdt/palpal/0/100")


def _to_float(num_str: str) -> float:
    """Convierte '91.5' o '91,5' a float."""
    return float(str(num_str).strip().replace(",", "."))


def _first_number(text: str) -> float:
    """Toma el primer número que encuentre en un texto."""
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)", text)
    if not m:
        raise RuntimeError(f"No encontré ningún número en el texto: {text!r}")
    return _to_float(m.group(1))


def _try_accept_banners(page) -> None:
    """Intenta cerrar/aceptar banners típicos (cookies, ok, etc.). No falla si no existen."""
    for pat in [r"Accept", r"I agree", r"Agree", r"OK", r"Got it", r"Aceptar", r"Acepto", r"Entendido"]:
        try:
            btn = page.get_by_role("button", name=re.compile(pat, re.I))
            if btn.count() > 0:
                btn.first.click(timeout=1000)
                page.wait_for_timeout(500)
                break
        except Exception:
            pass


def read_envias_usdt(page) -> float:
    """
    Lee el valor 'You send USDT' / 'Envías USDT' desde la misma pantalla.
    Estrategia robusta:
      1) Espera a que la página renderice el cotizador (presencia de PayPal y USDT/tether).
      2) Busca inputs numéricos visibles y elige el que esté en un contenedor con 'USDT' o 'tether'
         y NO en el bloque de 'PayPal'/'USD' (para evitar agarrar el 100).
      3) Fallback: parsea el texto visible cerca de 'USDT/tether' si no hay input usable.
    """
    page.goto(URL, wait_until="domcontentloaded", timeout=180_000)
    page.wait_for_timeout(1500)
    _try_accept_banners(page)

    # Espera señales claras de que el cotizador cargó
    # (PayPal suele aparecer siempre, y USDT/tether también)
    page.get_by_text(re.compile(r"paypal", re.I)).first.wait_for(timeout=120_000)
    page.wait_for_function(
        "document.body && (document.body.innerText.toLowerCase().includes('usdt') || document.body.innerText.toLowerCase().includes('tether'))",
        timeout=120_000,
    )
    page.wait_for_timeout(1500)

    # 1) Intento principal: leer desde inputs numéricos visibles, eligiendo el del bloque USDT/tether
    val = page.evaluate(
        r"""
        () => {
          const isVisible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
          const isNumber = (s) => {
            if (!s) return false;
            s = String(s).trim();
            return /^[0-9]+([.,][0-9]+)?$/.test(s);
          };

          const inputs = Array.from(document.querySelectorAll("input"))
            .filter(isVisible)
            .filter(el => isNumber(el.value));

          // Preferimos un input cuyo contenedor cercano mencione USDT/tether,
          // y evitamos los que estén dentro de un bloque que mencione PayPal/USD.
          const score = (el) => {
            let usdt = 0, paypal = 0;
            let node = el;
            for (let i = 0; i < 10 && node; i++) {
              const t = (node.innerText || "").toLowerCase();
              if (t.includes("usdt") || t.includes("tether")) usdt++;
              if (t.includes("paypal") || t.includes("usd")) paypal++;
              node = node.parentElement;
            }
            return { usdt, paypal };
          };

          let best = null;
          for (const el of inputs) {
            const s = score(el);
            // Queremos que sea USDT>0 y PayPal==0 idealmente
            const good = (s.usdt > 0) && (s.paypal === 0);
            if (good) return el.value;
            // Si no hay ideal, guardamos el que más "usdt" tenga y menos "paypal"
            if (!best) best = { el, s };
            else {
              if (s.usdt > best.s.usdt) best = { el, s };
              else if (s.usdt === best.s.usdt && s.paypal < best.s.paypal) best = { el, s };
            }
          }

          // Fallback de inputs: si hay alguno, devolvemos el "mejor" aunque tenga paypal/usd cerca
          return best ? best.el.value : null;
        }
        """
    )

    if val:
        return _to_float(val)

    # 2) Fallback: parsear texto visible cercano a USDT/tether.
    # Intento: encontrar un bloque que contenga "USDT" o "tether" y extraer el primer número
    body = page.inner_text("body")

    # Primer fallback: "USDT" cerca del número
    m = re.search(r"(?:usdt|tether)[\s\S]{0,200}?([0-9]+(?:[.,][0-9]+)?)", body, re.I)
    if m:
        return _to_float(m.group(1))

    # Segundo fallback: número seguido de USDT
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*USDT", body, re.I)
    if m:
        return _to_float(m.group(1))

    # Si llegamos acá, no pudimos
    raise RuntimeError("No pude encontrar el valor de 'You send/Envías USDT' (ni por inputs ni por texto).")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            # flags típicos para CI
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            # Intentamos forzar ES, pero el script NO depende de idioma.
            locale="es-AR",
            extra_http_headers={"Accept-Language": "es-AR,es;q=0.9,en;q=0.8"},
            viewport={"width": 1280, "height": 720},
        )
        page = context.new_page()

        try:
            envias = read_envias_usdt(page)
            print(f"ENVIAS_USDT={envias}")
        except (PlaywrightTimeoutError, Exception) as e:
            # Debug para que siempre puedas ver qué cargó realmente
            try:
                page.screenshot(path="debug_page.png", full_page=True)
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except Exception:
                pass
            print("ERROR:", repr(e))
            raise
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
