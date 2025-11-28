# tests_selenium/test_04_checkout.py

import re
import time
import pytest

from django.contrib.auth.models import User
from pedidos.models import Perfil

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def W(drv, timeout=12):
    return WebDriverWait(drv, timeout)


def go_to_login(drv, base_url: str):
    """
    Va al home y trata de entrar por el link 'Ingresar'.
    Si no lo encuentra, cae directo a /login/.
    """
    drv.get(base_url)
    try:
        login_link = W(drv).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[normalize-space()='Ingresar']")
            )
        )
        login_link.click()
    except Exception:
        drv.get(base_url + "/login/")
    W(drv).until(EC.presence_of_element_located((By.TAG_NAME, "form")))


def assert_logged_in_as(drv, username: str):
    """
    En base.html se muestra: Hola, <username>
    """
    W(drv).until(
        EC.presence_of_element_located(
            (By.XPATH, f"//span[contains(., 'Hola') and contains(., '{username}')]")
        )
    )


def do_login(drv, base_url: str, username: str, password: str):
    go_to_login(drv, base_url)

    user_el = W(drv).until(EC.element_to_be_clickable((By.NAME, "username")))
    pass_el = W(drv).until(EC.element_to_be_clickable((By.NAME, "password")))
    user_el.clear()
    user_el.send_keys(username)
    pass_el.clear()
    pass_el.send_keys(password)

    clicked = False
    for sel in ["button[type='submit']", "input[type='submit']"]:
        try:
            btn = drv.find_element(By.CSS_SELECTOR, sel)
            drv.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", btn
            )
            W(drv).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            clicked = True
            break
        except Exception:
            continue
    if not clicked:
        pass_el.send_keys(Keys.ENTER)

    assert_logged_in_as(drv, username)


def click_first_add_to_cart(driver):
    """
    Intenta encontrar el primer botón/enlace para agregar al carrito,
    probando varios patrones típicos:
    - data-test='add-to-cart'
    - texto 'Agregar' / 'Añadir'
    - icono material 'add_shopping_cart'
    """
    intentos = [
        # 1) Por data-test (si lo tienes en el template)
        (By.CSS_SELECTOR, "[data-test='add-to-cart']"),

        # 2) Botón con texto Agregar/Añadir
        (By.XPATH, "//button[contains(., 'Agregar') or contains(., 'Añadir')]"),

        # 3) Enlace <a> con texto Agregar/Añadir
        (By.XPATH, "//a[contains(., 'Agregar') or contains(., 'Añadir')]"),

        # 4) Botón o enlace que contenga el icono 'add_shopping_cart'
        (
            By.XPATH,
            "//button[.//span[contains(@class,'material-symbols-outlined') and "
            "contains(normalize-space(.), 'add_shopping_cart')]]"
            " | "
            "//a[.//span[contains(@class,'material-symbols-outlined') and "
            "contains(normalize-space(.), 'add_shopping_cart')]]",
        ),
    ]

    last_exc = None
    for how, sel in intentos:
        try:
            btns = W(driver).until(
                EC.presence_of_all_elements_located((how, sel))
            )
            if btns:
                btns[0].click()
                time.sleep(0.5)  # pequeña pausa para que procese el add_to_cart
                return
        except TimeoutException as e:
            last_exc = e
            continue

    # Si llegamos aquí, no encontramos nada razonable que parezca "Agregar al carrito"
    # Esto ayuda a depurar mirando el HTML.
    html = driver.page_source
    with open("debug_menu_no_add_button.html", "w", encoding="utf-8") as f:
        f.write(html)

    raise AssertionError(
        "No encontré ningún botón/enlace para agregar al carrito en /menu/. "
        "Se guardó el HTML en debug_menu_no_add_button.html para inspección."
    )


def submit_checkout_form(driver, nombre, telefono, direccion):
    W(driver).until(
        EC.presence_of_element_located((By.NAME, "nombre"))
    ).send_keys(nombre)
    driver.find_element(By.NAME, "telefono").send_keys(telefono)
    driver.find_element(By.NAME, "direccion").send_keys(direccion)

    submit = None
    try:
        submit = driver.find_element(
            By.CSS_SELECTOR, "[data-test='checkout-submit']"
        )
    except Exception:
        try:
            submit = driver.find_element(
                By.XPATH,
                "//button[contains(., 'Confirmar pedido')]",
            )
        except Exception:
            submit = driver.find_element(
                By.XPATH, "//button[@type='submit']"
            )

    # En tu cart.html, el botón abre un modal.
    submit.click()  # abre el modal
    time.sleep(0.5)

    # Clic en "Sí, confirmar" dentro del modal
    modal_confirm_button = W(driver).until(
        EC.element_to_be_clickable(
            (
                By.XPATH,
                "//div[@id='confirm-modal']//button[contains(., 'Sí, confirmar')]",
            )
        )
    )
    modal_confirm_button.click()


def assert_order_detail_loaded(driver):
    """
    Comprueba que se cargó la página de detalle de orden
    (/orden/<id>/) y que aparece el mensaje de confirmación.
    """
    W(driver, 15).until(
        EC.url_matches(re.compile(r"/orden/\d+/?$"))
    )

    W(driver).until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                "//*[contains(., '¡Pedido Confirmado!')]",
            )
        )
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.selenium
class TestCheckoutE2E:
    @pytest.fixture(autouse=True)
    def setup_user(self):
        """
        Usuario de prueba para el flujo E2E.
        Equivalente al TEST_USER / TEST_PASS del script original,
        pero creado en la BD de pruebas.
        """
        self.password = "Perrajara21"
        self.user = User.objects.create_user(
            username="diegogenial",
            email="test_checkout@example.com",
            password=self.password,
        )
        Perfil.objects.get_or_create(user=self.user)

    def test_flujo_checkout_completo(self, live_server, driver):
        base_url = live_server.url

        # 1) Login
        do_login(driver, base_url, self.user.username, self.password)

        # 2) Ir al menú
        driver.get(f"{base_url}/menu/")
        # si la página tarda, podríamos esperar algo:
        W(driver).until(
            EC.presence_of_element_located((By.TAG_NAME, "main"))
        )

        # 3) Agregar primer plato
        click_first_add_to_cart(driver)

        # 4) Ir al carrito
        driver.get(f"{base_url}/cart/")
        W(driver).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )

        # 5) Completar checkout
        submit_checkout_form(
            driver,
            nombre="Cliente E2E",
            telefono="+999999999",
            direccion="Av. Prueba 123",
        )

        # 6) Ver detalle de la orden
        assert_order_detail_loaded(driver)

        # (opcional) intentar volver al menú si hay link
        try:
            back = driver.find_element(
                By.XPATH, "//a[contains(., 'Volver al Menú')]"
            )
            back.click()
            W(driver).until(EC.url_contains("/menu/"))
        except Exception:
            pass
