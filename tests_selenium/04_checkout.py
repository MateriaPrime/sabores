from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys # <--- AÑADIDO
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# (Imports de webdriver_manager, service, re, subprocess eliminados, ya no se necesitan)

HOST = "http://127.0.0.1:8000"
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
HEADLESS = False

# --- USUARIO DE PRUEBA (Debe existir en tu BD) ---
TEST_USER = "diegogenial"
TEST_PASS = "Perrajara21"


def build_driver():
    opts = Options()
    opts.binary_location = BRAVE_PATH
    if HEADLESS:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    
    # Esta es la forma moderna: Selenium Manager detecta Brave 142
    # y descarga el driver 142 automáticamente.
    return webdriver.Chrome(options=opts)

def W(drv, timeout=12):
    return WebDriverWait(drv, timeout)

# --- [INICIO] FUNCIONES DE LOGIN (COPIADAS DE 02_login.py) ---
def go_to_login(drv):
    drv.get(HOST)
    try:
        login_link = W(drv).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[normalize-space()='Ingresar']")
        ))
        login_link.click()
    except Exception:
        drv.get(HOST + "/login/")
    W(drv).until(EC.presence_of_element_located((By.TAG_NAME, "form")))

def assert_logged_in_as(drv, username):
    # (El base.html usa 'Hola, <username>' en un span)
    W(drv).until(EC.presence_of_element_located(
        (By.XPATH, f"//span[contains(., 'Hola') and contains(., '{username}')]")
    ))

def do_login(drv, username, password):
    user_el = W(drv).until(EC.element_to_be_clickable((By.NAME, "username")))
    pass_el = W(drv).until(EC.element_to_be_clickable((By.NAME, "password")))
    user_el.clear(); user_el.send_keys(username)
    pass_el.clear(); pass_el.send_keys(password)

    clicked = False
    for sel in ["button[type='submit']", "input[type='submit']"]:
        try:
            btn = drv.find_element(By.CSS_SELECTOR, sel)
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            W(drv).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        pass_el.send_keys(Keys.ENTER)

    assert_logged_in_as(drv, username)
# --- [FIN] FUNCIONES DE LOGIN ---


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
            EC.presence_of_all_elements_located((
                # <--- CORRECCIÓN 1: Usar 'contains()' en lugar de 'normalize-space()'
                By.XPATH, "//button[contains(., 'Agregar')]"
            ))
        )
    assert btns, "No encontré botones para agregar al carrito."
    btns[0].click()
    sleep(0.5) # Pequeña pausa para que la vista 'add_to_cart' procese

def submit_checkout_form(driver, nombre, telefono, direccion):
    W(driver).until(EC.presence_of_element_located((By.NAME, "nombre"))).send_keys(nombre)
    driver.find_element(By.NAME, "telefono").send_keys(telefono)
    driver.find_element(By.NAME, "direccion").send_keys(direccion)

    submit = None
    try:
        submit = driver.find_element(By.CSS_SELECTOR, "[data-test='checkout-submit']")
    except Exception:
        try:
            submit = driver.find_element(
                By.XPATH,
                # <--- CORRECCIÓN 2: Selector más específico para tu botón
                "//button[contains(., 'Confirmar pedido')]"
            )
        except Exception:
            submit = driver.find_element(By.XPATH, "//button[@type='submit']")
    
    # En tu cart.html, el botón abre un modal.
    # Necesitamos hacer clic en el botón del *modal*.
    submit.click() # Esto abre el modal
    sleep(0.5) # Espera a que aparezca el modal

    # Clic en el botón "Sí, confirmar" DENTRO del modal
    modal_confirm_button = W(driver).until(EC.element_to_be_clickable(
        (By.XPATH, "//div[@id='confirm-modal']//button[contains(., 'Sí, confirmar')]")
    ))
    modal_confirm_button.click()


def assert_order_detail_loaded(driver):
    # URL del tipo /orden/<id>/
    W(driver, 15).until(EC.url_matches(r"/orden/\d+/?$"))

    # Mensaje de confirmación visible
    W(driver).until(EC.presence_of_element_located((
        By.XPATH,
        # <--- CORRECCIÓN 3: Texto exacto de order_detail.html
        "//*[contains(., '¡Pedido Confirmado!')]"
    )))

def main():
    d = build_driver()
    try:
        # 1) Iniciar sesión
        go_to_login(d)
        do_login(d, TEST_USER, TEST_PASS)
        print("✅ Login OK")

        # 2) Ir al menú
        d.get(f"{HOST}/menu/")
        print("✅ Menú OK")

        # 3) Agregar primer plato
        click_first_add_to_cart(d)
        print("✅ Add to cart OK")

        # 4) Ir al carrito
        d.get(f"{HOST}/cart/")
        print("✅ Cart page OK")

        # 5) Completar checkout
        # <--- CORRECCIÓN 4: Usar teléfono con '+' (detectado en 03_signup_login.py)
        submit_checkout_form(d, "Cliente E2E", "+999999999", "Av. Prueba 123")
        print("✅ Checkout submit OK")

        # 6) Ver detalle de la orden
        assert_order_detail_loaded(d)
        print("✅ Order detail OK")

        # 7) Volver al menú (si hay link)
        try:
            back = d.find_element(By.XPATH, "//a[contains(., 'Volver al Menú')]")
            back.click()
            W(d).until(EC.url_contains("/menu/"))
            print("✅ Volver al menú OK")
        except Exception:
            pass

        if not HEADLESS:
            print("🏁 Test completado con éxito.")
            sleep(1.5)

    finally:
        d.quit()

if __name__ == "__main__":
    main()