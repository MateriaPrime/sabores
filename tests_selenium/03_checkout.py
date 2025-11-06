from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE = "http://127.0.0.1:8000"

def driver():
    opts = Options()
    # opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

if __name__ == "__main__":
    d = driver()
    w = WebDriverWait(d, 10)
    try:
        d.get(BASE + "/menu/")
        # Ajusta el selector a tu botón “Agregar”
        # Idea: pon data-test en el template: <button data-test="add-to-cart">Agregar</button>
        w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-test='add-to-cart']"))).click()

        # Ir al carrito (link “Carrito”)
        w.until(EC.element_to_be_clickable((By.LINK_TEXT, "Carrito"))).click()

        # Ir a checkout
        w.until(EC.element_to_be_clickable((By.LINK_TEXT, "Checkout"))).click()

        # Rellenar formulario de checkout
        w.until(EC.visibility_of_element_located((By.NAME, "nombre"))).send_keys("Cliente Test")
        w.until(EC.visibility_of_element_located((By.NAME, "telefono"))).send_keys("9999999")
        w.until(EC.visibility_of_element_located((By.NAME, "direccion"))).send_keys("Calle Falsa 123")
        w.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))).click()

        # Comprobar que cargó detalle del pedido (ajusta selector)
        w.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "h1, h2, .title")))
        print("Checkout OK")
    finally:
        d.quit()
