# tests_selenium/conftest.py
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def driver():
    """
    Este fixture inicializa el driver de Chrome para cada test
    y lo cierra al finalizar.
    """
    # Configuración de opciones (puedes descomentar headless para no ver la ventana)
    chrome_options = Options()
    # chrome_options.add_argument("--headless") 
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")

    # Inicializar el WebDriver (Chrome)
    # Nota: Asegúrate de tener ChromeDriver instalado o compatible
    driver = webdriver.Chrome(options=chrome_options)
    
    # Configurar una espera implícita general (útil para cargas lentas)
    driver.implicitly_wait(5)
    
    # Entregar el driver al test
    yield driver
    
    # Cerrar el navegador después del test
    driver.quit()