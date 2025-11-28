# tests_selenium/02_login.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/"
TEST_USER = "diegogenial"        # <-- cambia por un user real
TEST_PASS = "Perrajara21"    # <-- su pass

def get_driver(headless=False):
    opts = Options()
    opts.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")
    return webdriver.Chrome(options=opts)

def wait(drv, t=10):
    return WebDriverWait(drv, t)

def dump_html(drv, name="dump"):
    out = Path(f"{name}.html").absolute()
    out.write_text(drv.page_source, encoding="utf-8")
    print(f"💾 Dump HTML -> {out}")

def go_to_login(drv):
    drv.get(BASE_URL)
    # Clic en el link "Ingresar" del header (texto exacto)
    try:
        login_link = wait(drv).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[normalize-space()='Ingresar']")
        ))
        login_link.click()
    except Exception:
        # fallback: ir directo a /login/
        drv.get(BASE_URL + "login/")
    # Esperar a que haya un <form>
    wait(drv).until(EC.presence_of_element_located((By.TAG_NAME, "form")))

def do_login(drv, username, password):
    # Esperar campos por name (Django por defecto)
    user_el = wait(drv).until(EC.element_to_be_clickable((By.NAME, "username")))
    pass_el = wait(drv).until(EC.element_to_be_clickable((By.NAME, "password")))
    user_el.clear(); user_el.send_keys(username)
    pass_el.clear(); pass_el.send_keys(password)

    # 1) intenta botón submit
    clicked = False
    for sel in [
        "button[type='submit']",
        "input[type='submit']",
        "form button",
        "form input[type='submit']",
    ]:
        try:
            btn = drv.find_element(By.CSS_SELECTOR, sel)
            drv.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            wait(drv).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            clicked = True
            break
        except Exception:
            continue

    # 2) si no hubo botón, prueba con Enter en el password
    if not clicked:
        try:
            pass_el.send_keys(Keys.ENTER)
            clicked = True
        except Exception:
            pass

    # 3) si aún no, submit del primer form por JS
    if not clicked:
        try:
            drv.execute_script("document.querySelector('form').submit();")
            clicked = True
        except Exception:
            pass

    if not clicked:
        dump_html(drv, "selenium_dump_login_before_click")
        raise RuntimeError("No pude enviar el formulario de login (no hay botón ni submit).")

    # Verifica que estamos logueados: “Hola, <username>”
    try:
        wait(drv, 10).until(EC.presence_of_element_located(
            (By.XPATH, f"//span[contains(., 'Hola') and contains(., '{username}')]")
        ))
    except Exception:
        dump_html(drv, "selenium_dump_login_after_submit")
        raise

def do_logout(drv):
    # Link “Salir”
    logout = wait(drv).until(EC.element_to_be_clickable(
        (By.XPATH, "//a[normalize-space()='Salir']")
    ))
    drv.execute_script("arguments[0].scrollIntoView({block:'center'});", logout)
    logout.click()
    wait(drv).until(EC.presence_of_element_located(
        (By.XPATH, "//a[normalize-space()='Ingresar']")
    ))

if __name__ == "__main__":
    d = get_driver(headless=False)  # cuando esté estable, puedes poner True
    try:
        go_to_login(d)
        do_login(d, TEST_USER, TEST_PASS)
        print("✅ Login OK.")
        do_logout(d)
        print("✅ Logout OK.")
        time.sleep(1)
    finally:
        d.quit()


