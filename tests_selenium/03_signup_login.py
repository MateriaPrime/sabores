# tests_selenium/03_signup_login.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, random
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/"

# --- Driver Brave (Chromium) ---
def get_driver(headless=False):
    opts = Options()
    # Ruta Brave (ajústala si la tienes en otra carpeta)
    opts.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--disable-gpu")
    return webdriver.Chrome(options=opts)

def wait(drv, t=12):
    return WebDriverWait(drv, t)

def dump_html(drv, name="dump"):
    out = Path(f"{name}.html").absolute()
    out.write_text(drv.page_source, encoding="utf-8")
    print(f"💾 Dump HTML -> {out}")

# --- helpers de navegación/acciones ---
def go_home(drv):
    drv.get(BASE_URL)
    wait(drv).until(EC.presence_of_element_located((By.TAG_NAME, "header")))

def go_signup(drv):
    """
    Intenta ir por el link 'Crear cuenta' del header.
    Si no lo encuentra, prueba /signup/cliente/ directo.
    """
    go_home(drv)
    # 1) intenta por link visible
    try:
        link = wait(drv).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[normalize-space()='Crear cuenta']")
        ))
        link.click()
    except Exception:
        # 2) fallback directo
        drv.get(BASE_URL + "signup/cliente/")
    # espera un form
    wait(drv).until(EC.presence_of_element_located((By.TAG_NAME, "form")))

def field(drv, *locators):
    """Devuelve el primer elemento que exista de una lista de localizadores."""
    for how, sel in locators:
        try:
            el = drv.find_element(how, sel)
            return el
        except Exception:
            continue
    return None

def form_has_errors(drv):
    """
    Busca mensajes de error habituales en Django forms.
    Ajusta selectores si usas otra marca.
    """
    # errores de campo (ul.errorlist li), mensajes (div[role=alert]), o spans de ayuda con texto rojo
    candidates = [
        (By.CSS_SELECTOR, "ul.errorlist li"),
        (By.CSS_SELECTOR, ".errorlist li"),
        (By.CSS_SELECTOR, "[role='alert']"),
        (By.XPATH, "//*[contains(@class,'text-red') or contains(@class,'text-rose-')][self::span or self::p or self::div]"),
    ]
    for how, sel in candidates:
        els = drv.find_elements(how, sel)
        if any(e.text.strip() for e in els):
            return True
    return False

def assert_logged_in_as(drv, username):
    # en tu base.html mostrábamos: Hola, <username>
    wait(drv).until(EC.presence_of_element_located(
        (By.XPATH, f"//span[contains(., 'Hola') and contains(., '{username}')]")
    ))

def logout(drv):
    try:
        link = wait(drv).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[normalize-space()='Salir']")
        ))
        link.click()
        wait(drv).until(EC.presence_of_element_located(
            (By.XPATH, "//a[normalize-space()='Ingresar']")
        ))
    except Exception:
        # si no está el link, no pasa nada
        pass

# --- flujo signup + login ---
def do_signup_cliente(drv):
    """
    Rellena el formulario de cliente:
      username, first_name, last_name, email (opcional), direccion, telefono, password1, password2, remember_me (opcional)
    y envía. Devuelve (username, password).
    """
    go_signup(drv)

    # Genera credenciales únicas
    suffix = str(int(time.time()))[-6:] + str(random.randint(10, 99))
    username = f"cli{suffix}"
    password = f"Test-{suffix}#A1"
    email = f"{username}@example.com"

    # Intenta encontrar campos por name, y si no existen, busca por id/placeholder/label.
    def fill(name_or_fallbacks, value):
        """
        name_or_fallbacks: lista de (how, selector) a probar.
        Rellena y hace clear().
        """
        el = field(drv, *name_or_fallbacks)
        if not el:
            dump_html(drv, "signup_missing_field")
            raise RuntimeError(f"No pude encontrar el campo: {name_or_fallbacks}")
        drv.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
        el.clear()
        el.send_keys(value)

    # username
    fill([
        (By.NAME, "username"),
        (By.CSS_SELECTOR, "#id_username"),
        (By.XPATH, "//input[@placeholder='Usuario']"),
        (By.XPATH, "//label[normalize-space()='Usuario']/following::input[1]"),
    ], username)

    # nombres
    fill([
        (By.NAME, "first_name"),
        (By.CSS_SELECTOR, "#id_first_name"),
        (By.XPATH, "//input[@placeholder='Nombre']"),
        (By.XPATH, "//label[normalize-space()='Nombre']/following::input[1]"),
    ], "Cliente")

    fill([
        (By.NAME, "last_name"),
        (By.CSS_SELECTOR, "#id_last_name"),
        (By.XPATH, "//input[@placeholder='Apellido']"),
        (By.XPATH, "//label[normalize-space()='Apellido']/following::input[1]"),
    ], "Prueba")

    # email (si tienes el campo)
    mail_input = field(drv, (By.NAME, "email"), (By.CSS_SELECTOR, "#id_email"))
    if mail_input:
        mail_input.clear(); mail_input.send_keys(email)

    # dirección
    fill([
        (By.NAME, "direccion"),
        (By.CSS_SELECTOR, "#id_direccion"),
        (By.XPATH, "//input[@placeholder='Dirección']"),
        (By.XPATH, "//label[normalize-space()='Dirección']/following::input[1]"),
        (By.XPATH, "//textarea[@name='direccion']"),
    ], "Calle Falsa 123")

    # teléfono
    fill([
        (By.NAME, "telefono"),
        (By.CSS_SELECTOR, "#id_telefono"),
        (By.XPATH, "//input[@placeholder='Teléfono']"),
        (By.XPATH, "//label[normalize-space()='Teléfono']/following::input[1]"),
    ], "+999999999")

    # password1 / password2
    fill([
        (By.NAME, "password1"),
        (By.CSS_SELECTOR, "#id_password1"),
        (By.XPATH, "//input[@type='password' and contains(@placeholder,'Contraseña')]"),
        (By.XPATH, "//label[normalize-space()='Contraseña']/following::input[@type='password'][1]"),
    ], password)

    fill([
        (By.NAME, "password2"),
        (By.CSS_SELECTOR, "#id_password2"),
        (By.XPATH, "//input[@type='password' and contains(@placeholder,'Confirm')]"),
        (By.XPATH, "//label[contains(.,'Confirm') or contains(.,'Repite')]/following::input[@type='password'][1]"),
    ], password)

    # remember me (si existe como checkbox)
    remember = field(drv,
        (By.NAME, "remember_me"),
        (By.CSS_SELECTOR, "#id_remember_me"),
        (By.XPATH, "//input[@type='checkbox' and (contains(@name,'remember') or contains(@id,'remember'))]")
    )
    if remember:
        if not remember.is_selected():
            drv.execute_script("arguments[0].click()", remember)

    # Submit: intenta varios selectores típicos
    submitted = False
    for sel in ["button[type='submit']", "input[type='submit']", "form button", "form input[type='submit']"]:
        try:
            btn = drv.find_element(By.CSS_SELECTOR, sel)
            drv.execute_script("arguments[0].scrollIntoView({block:'center'})", btn)
            wait(drv).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            submitted = True
            break
        except Exception:
            continue

    if not submitted:
        # Enter como plan B
        pwd2 = field(drv, (By.NAME, "password2"), (By.CSS_SELECTOR, "#id_password2"))
        if pwd2:
            pwd2.send_keys(Keys.ENTER)
            submitted = True

    if not submitted:
        dump_html(drv, "signup_no_submit")
        raise RuntimeError("No pude enviar el formulario de signup.")

    # Si el form tiene errores, no habrá saludo. Guardamos el HTML y fallamos.
    time.sleep(0.5)
    if form_has_errors(drv):
        dump_html(drv, "signup_with_errors")
        raise AssertionError("El formulario de registro devolvió errores (usuario ya existe, contraseña débil, etc.).")

    # Tras registro correcto, tu vista hace login automático y debe verse el saludo
    assert_logged_in_as(drv, username)

    return username, password

def do_login(drv, username, password):
    # ir a login desde header o /login/
    go_home(drv)
    try:
        link = wait(drv).until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Ingresar']")))
        link.click()
    except Exception:
        drv.get(BASE_URL + "login/")
    wait(drv).until(EC.presence_of_element_located((By.TAG_NAME, "form")))

    # user/pass
    u = wait(drv).until(EC.element_to_be_clickable((By.NAME, "username")))
    p = wait(drv).until(EC.element_to_be_clickable((By.NAME, "password")))
    u.clear(); u.send_keys(username)
    p.clear(); p.send_keys(password)

    # remember me si existe
    remember = field(drv,
        (By.NAME, "remember_me"),
        (By.CSS_SELECTOR, "#id_remember_me"),
        (By.XPATH, "//input[@type='checkbox' and (contains(@name,'remember') or contains(@id,'remember'))]")
    )
    if remember and not remember.is_selected():
        drv.execute_script("arguments[0].click()", remember)

    # submit
    submitted = False
    for sel in ["button[type='submit']", "input[type='submit']"]:
        try:
            btn = drv.find_element(By.CSS_SELECTOR, sel)
            drv.execute_script("arguments[0].scrollIntoView({block:'center'})", btn)
            wait(drv).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            submitted = True
            break
        except Exception:
            continue
    if not submitted:
        p.send_keys(Keys.ENTER)

    assert_logged_in_as(drv, username)

if __name__ == "__main__":
    d = get_driver(headless=False)  # cuando esté estable, puedes poner True
    try:
        # 1) Registro (auto-login incluido)
        u, pw = do_signup_cliente(d)
        print(f"✅ Signup OK: {u}")

        # 2) Logout
        logout(d)
        print("✅ Logout OK")

        # 3) Login manual con el usuario creado
        do_login(d, u, pw)
        print("✅ Login OK")

        time.sleep(1)
    finally:
        d.quit()
