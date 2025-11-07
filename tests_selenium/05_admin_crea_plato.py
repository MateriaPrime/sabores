import os
import re
import time
import subprocess
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
# ---------- CONFIG ----------
BASE_URL = "http://127.0.0.1:8000"
ADMIN_USER = "daniel"
ADMIN_PASS = "123"

# Ruta a Brave (ajústala si tu instalación es otra)
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

# Imagen de prueba
IMG_PATH = Path(__file__).parent / "assets" / "plato.jpg"
IMG_PATH.parent.mkdir(parents=True, exist_ok=True)
if not IMG_PATH.exists():
    from PIL import Image
    Image.new("RGB", (64, 64), (236, 127, 19)).save(IMG_PATH, "JPEG")

CATEGORIA_NOMBRE = "Sopas (Selenium)"
PLATO_NOMBRE = "Sopa de Tomate (Selenium)"


def brave_major():
    """
    Devuelve el 'major' de Brave (p.ej. '142') leyendo la versión del ejecutable
    con PowerShell (sin lanzar el navegador). Evita el mensaje de
    'Se está abriendo en una sesión de navegador existente.'
    """
    # 1) Intenta con PowerShell (leer VersionInfo.ProductVersion)
    try:
        ps_cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(Get-Item '{BRAVE_PATH}').VersionInfo.ProductVersion"
        ]
        out = subprocess.check_output(ps_cmd, text=True).strip()
        # out típico: 142.0.7444.60
        m = re.match(r"(\d+)\.", out)
        if m:
            return m.group(1)
    except Exception:
        pass

    # 2) Fallback: intenta con '--version' si no hay sesión abierta
    try:
        out = subprocess.check_output([BRAVE_PATH, "--version"], text=True).strip()
        # "Brave Browser 142.0.7444.60"
        m = re.search(r"\b(\d+)\.", out)
        if m:
            return m.group(1)
    except Exception:
        pass

    # 3) Fallback manual: variable de entorno BRAVE_MAJOR (opcional)
    env_major = os.environ.get("BRAVE_MAJOR")
    if env_major and env_major.isdigit():
        return env_major

    # 4) Último recurso: asume 142 (muy probable a fecha actual en Brave estable)
    return "142"


def build_driver(headless=False):
    opts = Options()
    opts.binary_location = BRAVE_PATH
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")

    # 👉 que webdriver-manager detecte la versión de Brave y baje el driver correcto
    service = Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install())
    return webdriver.Chrome(service=service, options=opts)

def wait(drv, t=10):
    return WebDriverWait(drv, t)


def admin_login(drv):
    drv.get(f"{BASE_URL}/admin/")
    wait(drv).until(EC.visibility_of_element_located((By.ID, "id_username")))
    drv.find_element(By.ID, "id_username").send_keys(ADMIN_USER)
    drv.find_element(By.ID, "id_password").send_keys(ADMIN_PASS)
    drv.find_element(By.CSS_SELECTOR, "input[type=submit]").click()
    wait(drv).until(EC.presence_of_element_located((By.LINK_TEXT, "Log out")))


def ensure_categoria(drv):
    drv.get(f"{BASE_URL}/admin/pedidos/categoria/add/")
    wait(drv).until(EC.visibility_of_element_located((By.ID, "id_nombre")))
    nombre = drv.find_element(By.ID, "id_nombre")
    nombre.clear()
    nombre.send_keys(CATEGORIA_NOMBRE)
    drv.find_element(By.NAME, "_save").click()
    # Estés creando nueva o chocando por duplicado, el admin vuelve al listado
    wait(drv).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#content")))


def crear_plato(drv):
    drv.get(f"{BASE_URL}/admin/pedidos/plato/add/")
    wait(drv).until(EC.visibility_of_element_located((By.ID, "id_nombre")))

    Select(drv.find_element(By.ID, "id_categoria")).select_by_visible_text(CATEGORIA_NOMBRE)
    drv.find_element(By.ID, "id_nombre").send_keys(PLATO_NOMBRE)
    drv.find_element(By.ID, "id_descripcion").send_keys("Plato creado por prueba Selenium.")
    precio = drv.find_element(By.ID, "id_precio")
    precio.clear()
    precio.send_keys("4990")

    # Subir imagen (para ImageField)
    drv.find_element(By.ID, "id_imagen").send_keys(str(IMG_PATH.resolve()))

    try:
        chk = drv.find_element(By.ID, "id_destacado")
        if not chk.is_selected():
            chk.click()
    except Exception:
        pass

    drv.find_element(By.NAME, "_save").click()
    wait(drv).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".messagelist .success, .messagelist .successnote")
        )
    )


def verificar_en_menu_publico(drv):
    drv.get(f"{BASE_URL}/menu/")
    wait(drv).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    body_text = drv.find_element(By.TAG_NAME, "body").text
    assert PLATO_NOMBRE in body_text, "No encontré el plato en /menu/"


def main():
    drv = build_driver(headless=False)
    try:
        admin_login(drv)
        ensure_categoria(drv)
        crear_plato(drv)
        verificar_en_menu_publico(drv)
        print("✅ Prueba OK: el admin creó un plato y aparece en /menu/")
        time.sleep(1)
    finally:
        drv.quit()


if __name__ == "__main__":
    main()
