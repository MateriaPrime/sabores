# tests_selenium/01_smoke.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "http://127.0.0.1:8000/"

def get_driver(headless=False):
    opts = Options()
    opts.binary_location = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--window-size=1366,768")

    # 👇 sin webdriver_manager, Selenium Manager se encarga del driver
    driver = webdriver.Chrome(options=opts)
    return driver

if __name__ == "__main__":
    driver = get_driver(headless=False)
    try:
        driver.get(BASE_URL)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "header")))
        print("HOME OK")
    finally:
        driver.quit()
