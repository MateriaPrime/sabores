# tests_selenium/test_05_admin_panel.py
import pytest
from django.contrib.auth.models import User, Group
from pedidos.models import Perfil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import time

@pytest.mark.django_db(transaction=True)
@pytest.mark.selenium
class TestAdminPanelSelenium:
    
    @pytest.fixture(autouse=True)
    def setup_data(self):
        # 1. Crear Admin
        self.admin = User.objects.create_superuser(
            'superadmin',
            'admin@test.com',
            'admin123'
        )
        Perfil.objects.get_or_create(user=self.admin)
        
        # 2. Crear Usuario normal
        self.usuario = User.objects.create_user(
            'usuario_prueba',
            'test@test.com',
            'user123'
        )
        perfil, created = Perfil.objects.get_or_create(user=self.usuario)
        perfil.saldo = 100
        perfil.save()
        
        # 3. Crear el Grupo (aseguramos que existe)
        Group.objects.get_or_create(name='Repartidor')

    def test_flujo_admin_cartera(self, live_server, driver):
        driver.get(f"{live_server.url}/login/")
        driver.find_element(By.NAME, "username").send_keys("superadmin")
        driver.find_element(By.NAME, "password").send_keys("admin123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

        time.sleep(2)

        driver.get(f"{live_server.url}/panel/cartera/{self.usuario.id}/")
        input_monto = driver.find_element(By.NAME, "monto")
        input_monto.clear()
        input_monto.send_keys("5000")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "5000" in body_text

    def test_flujo_asignar_rol(self, live_server, driver):
        """
        Prueba la asignación de roles usando el texto visible 'Repartidor'
        y luego verifica en la BD que el usuario quedó en ese grupo.
        """
        # 1) Login
        driver.get(f"{live_server.url}/login/")
        driver.find_element(By.NAME, "username").send_keys("superadmin")
        driver.find_element(By.NAME, "password").send_keys("admin123")
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        time.sleep(2)
        
        # 2) Ir a gestión de usuarios
        driver.get(f"{live_server.url}/panel/usuarios/")
        
        found = False
        attempts = 0
        
        while not found and attempts < 3:
            try:
                # Localizar el último select de roles
                selects = driver.find_elements(By.NAME, "role")
                assert selects, "No se encontró ningún <select name='role'> en la página."
                target_select = selects[-1]
                
                select_obj = Select(target_select)

                # Intentar seleccionar por TEXTO VISIBLE 'Repartidor'
                for option in select_obj.options:
                    if option.text.strip().lower() == "repartidor":
                        option.click()
                        found = True
                        break

                # Si no se encontró por texto, intentamos por value como fallback
                if not found:
                    try:
                        select_obj.select_by_value("Repartidor")
                        found = True
                    except NoSuchElementException:
                        try:
                            select_obj.select_by_value("repartidor")
                            found = True
                        except NoSuchElementException:
                            raise NoSuchElementException(
                                "No se encontró ninguna opción de rol 'Repartidor' "
                                "ni por texto visible ni por value."
                            )

            except NoSuchElementException as e:
                attempts += 1
                print(f"Intento {attempts}: {e}. Recargando página...")
                driver.refresh()
                time.sleep(1)

        if not found:
            pytest.fail("El rol 'Repartidor' no pudo seleccionarse después de 3 intentos.")
        
        # 3) Guardar cambios
        selects = driver.find_elements(By.NAME, "role")
        assert selects, "Después de la recarga no se encontró ningún <select name='role'>."
        target_select = selects[-1]
        
        form = target_select.find_element(By.XPATH, "./..")
        save_btn = form.find_element(By.CSS_SELECTOR, "button[type='submit']")
        save_btn.click()
        
        time.sleep(1)

        # 4) Verificar en la BASE DE DATOS que el usuario tiene el rol 'Repartidor'
        self.usuario.refresh_from_db()
        assert self.usuario.groups.filter(name="Repartidor").exists(), \
            "El usuario no quedó asignado al grupo 'Repartidor' en la base de datos."
