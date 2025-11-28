# tests_selenium/test_06_admin_panel_extra.py

import time
import pytest
from django.contrib.auth.models import User, Group
from pedidos.models import Perfil

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def wait(driver, t=10):
    return WebDriverWait(driver, t)


def login_as_superadmin(driver, live_server):
    """
    Helper para logearse como superadmin.
    Usa el mismo patrón que los otros tests que ya pasan.
    """
    driver.get(f"{live_server.url}/login/")

    driver.find_element(By.NAME, "username").clear()
    driver.find_element(By.NAME, "username").send_keys("superadmin")

    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys("admin123")

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    # Dejamos que Django procese el login
    time.sleep(2)


@pytest.mark.django_db(transaction=True)
@pytest.mark.selenium
class TestAdminPanelExtraSelenium:

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """
        Datos base:
        - superadmin
        - usuario normal con saldo inicial = 100
        - grupo 'Repartidor'
        """
        self.admin = User.objects.create_superuser(
            "superadmin", "admin@test.com", "admin123"
        )
        Perfil.objects.get_or_create(user=self.admin)

        self.usuario = User.objects.create_user(
            "usuario_prueba", "test@test.com", "user123"
        )
        perfil, _ = Perfil.objects.get_or_create(user=self.usuario)
        perfil.saldo = 100
        perfil.save()

        Group.objects.get_or_create(name="Repartidor")

    def test_panel_usuarios_muestra_saldo_en_listado(self, live_server, driver):
        """
        Verifica que el panel de usuarios carga correctamente
        y que aparece el saldo (100) en algún lugar de la página.
        """
        login_as_superadmin(driver, live_server)

        driver.get(f"{live_server.url}/panel/usuarios/")

        # Esperamos el select de roles; indica que cargó el listado
        wait(driver).until(EC.presence_of_element_located((By.NAME, "role")))

        page = driver.page_source
        assert "100" in page, (
            "El saldo inicial (100) no aparece en el HTML de /panel/usuarios/."
        )

    def test_cartera_actualiza_saldo_en_bd(self, live_server, driver):
        """
        Verifica que la recarga de saldo suma al saldo actual
        y que el nuevo saldo queda correctamente guardado en la BD.
        (No exigimos que se vea en /panel/usuarios/, porque esa vista
        no muestra la columna de saldo).
        """
        login_as_superadmin(driver, live_server)

        # Guardamos saldo inicial
        perfil_before = Perfil.objects.get(user=self.usuario)
        saldo_inicial = perfil_before.saldo  # debería ser 100

        # Ir a la vista de cartera del usuario
        driver.get(f"{live_server.url}/panel/cartera/{self.usuario.id}/")

        # Esperamos explícitamente el campo 'monto'
        wait(driver).until(EC.presence_of_element_located((By.NAME, "monto")))
        input_monto = driver.find_element(By.NAME, "monto")

        monto_recarga = "5000"
        input_monto.clear()
        input_monto.send_keys(monto_recarga)

        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(1)

        # Comprobamos en BD: debe haber sumado
        perfil_after = Perfil.objects.get(user=self.usuario)
        esperado = saldo_inicial + int(monto_recarga)
        assert perfil_after.saldo == esperado, (
            f"El saldo en BD es {perfil_after.saldo} pero se esperaba {esperado} "
            f"(saldo_inicial={saldo_inicial} + recarga={monto_recarga})."
        )

    def test_admin_puede_eliminar_un_usuario(self, live_server, driver):
        """
        Verifica que desde /panel/usuarios/ se puede eliminar al usuario de prueba.
        Usamos el form cuyo action empieza con /panel/usuarios/eliminar/<id>/ y
        enviamos el formulario por JS para saltarnos el confirm() de onsubmit.
        """
        login_as_superadmin(driver, live_server)

        # Confirmamos que el usuario de prueba existe
        assert User.objects.filter(pk=self.usuario.id).exists()

        driver.get(f"{live_server.url}/panel/usuarios/")
        wait(driver).until(EC.presence_of_element_located((By.NAME, "role")))

        # Localizamos el <form> de eliminación para ESTE usuario
        action_prefix = f"/panel/usuarios/eliminar/{self.usuario.id}/"
        form_selector = f"form[action^='{action_prefix}']"

        form_el = wait(driver).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, form_selector))
        )

        # Enviamos el form por JS: no dispara onsubmit ni el confirm()
        driver.execute_script("arguments[0].submit();", form_el)
        time.sleep(1)

        # Verificamos que YA NO existe en BD
        assert not User.objects.filter(pk=self.usuario.id).exists(), (
            "El usuario de prueba sigue existiendo en la BD después de intentar eliminarlo."
        )
