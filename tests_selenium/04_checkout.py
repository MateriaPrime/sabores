
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

HOST = "http://127.0.0.1:8000"  # Asegúrate de tener el runserver levantado
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
HEADLESS = False  # ponlo True cuando esté estable

def build_driver():
    opts = Options()
    opts.binary_location = BRAVE_PATH
    if HEADLESS:
        # Cuando ya esté estable, descomenta la línea siguiente y comenta la de abajo
        # opts.add_argument("--headless=new")
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    # webdriver_manager descarga un ChromeDriver reciente; funciona con Brave por ser Chromium
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

def W(drv, timeout=12):
    return WebDriverWait(drv, timeout)

def click_first_add_to_cart(driver):
    """
    Intenta primero por data-test, luego por texto 'Agregar'.
    """
    try:
        btns = W(driver).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-test='add-to-cart']"))
        )
    except Exception:
        btns = W(driver).until(
            EC.presence_of_all_elements_located((By.XPATH, "//button[normalize-space()='Agregar']"))
        )
    assert btns, "No encontré botones para agregar al carrito."
    btns[0].click()

def submit_checkout_form(driver, nombre, telefono, direccion):
    W(driver).until(EC.presence_of_element_located((By.NAME, "nombre"))).send_keys(nombre)
    driver.find_element(By.NAME, "telefono").send_keys(telefono)
    driver.find_element(By.NAME, "direccion").send_keys(direccion)

    # Intento 1: data-test
    try:
        submit = driver.find_element(By.CSS_SELECTOR, "[data-test='checkout-submit']")
    except Exception:
        # Intento 2: botón submit dentro del form (o con texto típico)
        try:
            submit = driver.find_element(
                By.XPATH,
                "//form//button[@type='submit' or contains(., 'Pagar') or contains(., 'Confirmar')]"
            )
        except Exception:
            # Intento 3: cualquier button type=submit
            submit = driver.find_element(By.XPATH, "//button[@type='submit']")
    submit.click()

def assert_order_detail_loaded(driver):
    # URL del tipo /orden/<id>/
    W(driver, 15).until(EC.url_matches(r"/orden/\d+/?$"))

    # Mensaje de confirmación visible
    W(driver).until(EC.presence_of_element_located((
        By.XPATH,
        "//*[contains(normalize-space(), 'Pedido Confirmado') or contains(normalize-space(), '¡Pedido Confirmado!')]"
    )))

def main():
    d = build_driver()
    try:
        # 1) Ir al menú
        d.get(f"{HOST}/menu/")

        # 2) Agregar primer plato
        click_first_add_to_cart(d)

        # 3) Ir al carrito
        d.get(f"{HOST}/cart/")

        # 4) Completar checkout
        submit_checkout_form(d, "Cliente E2E", "999999999", "Av. Prueba 123")

        # 5) Ver detalle de la orden
        assert_order_detail_loaded(d)

        # 6) Volver al menú (si hay link)
        try:
            back = d.find_element(By.XPATH, "//a[contains(@href, '/menu/')]")
            back.click()
            W(d).until(EC.url_contains("/menu/"))
        except Exception:
            # si no hay botón/anchor, no es crítico
            pass

        # Pequeña pausa visual si no es headless
        if not HEADLESS:
            sleep(1.5)

    finally:
        d.quit()

if __name__ == "__main__":
    main()
