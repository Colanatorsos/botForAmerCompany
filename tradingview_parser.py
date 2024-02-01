import pickle
import time
import traceback

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from config import Config

options = webdriver.ChromeOptions()
service = webdriver.ChromeService(executable_path=Config.CHROMEDRIVER_BINARY_LOCATION)

options.binary_location = Config.CHROME_BINARY_LOCATION
options.add_argument("--window-size=1920,1080")
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-setuid-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-accelerated-2d-canvas")
options.add_argument("--no-first-run")
options.add_argument("--no-zygote")
options.add_argument("--single-process")
options.add_argument("--disable-gpu")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("detach", True)

WAIT_FOR_ELEMENT_TIMEOUT = 5
COOKIES_FILENAME = "tv_cookies.pkl"


class TradingViewParser:
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(options=options)

    def wait_until(self, method, *, timeout: int = WAIT_FOR_ELEMENT_TIMEOUT, message=""):
        return WebDriverWait(self.driver, timeout).until(method, message)

    def load_cookies(self):
        self.driver.delete_all_cookies()
        try:
            for cookie in pickle.load(open(COOKIES_FILENAME, "rb")):
                self.driver.add_cookie(cookie)
        except FileNotFoundError:
            print("[TradingViewParser] No cookies found")

    def log_in(self, username: str, password: str):
        self.driver.get("https://ru.tradingview.com")
        self.load_cookies()
        self.driver.refresh()

        try:
            pfp = self.wait_until(EC.presence_of_element_located((By.CLASS_NAME, "tv-header__user-menu-button-userpic")))
            if pfp.get_attribute("src") is not None:
                print("[TradingViewParser] Already logged in")
                return
            else:
                raise Exception("Not logged in")
        except Exception as ex:
            print("[TradingViewParser] Not logged in. Logging in...")

        self.wait_until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Открыть меню пользователя']"))).click()
        self.wait_until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-name='header-user-menu-sign-in']"))).click()

        try:
            self.wait_until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[name='Email']")),
                timeout=3
            ).click()
        except TimeoutException as ex:
            print("[TradingViewParser] No email button, probably already on log in through email page")

        self.wait_until(EC.presence_of_element_located((By.ID, "id_username"))).send_keys(username)
        self.wait_until(EC.presence_of_element_located((By.ID, "id_password"))).send_keys(password)
        self.wait_until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-overflow-tooltip-text='Войти']"))).click()

        # Let cookies load (hardcoded but didn't find any other way to do this)
        time.sleep(5)

        pickle.dump(self.driver.get_cookies(), open(COOKIES_FILENAME, "wb"))
        self.quit()

    def get_chart_screenshot(self, symbol: str):
        self.driver.get(f"https://ru.tradingview.com/chart/?symbol={symbol}")
        self.load_cookies()
        self.driver.refresh()

        self.wait_until(EC.presence_of_element_located((By.ID, "header-toolbar-intervals"))).click()

        try:
            self.wait_until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-value='60'][data-role='menuitem']"))).click()
        except TimeoutException as ex:
            print("[TradingViewParser] Couldn't find 1 minute button element")

        # self.wait_until(EC.presence_of_element_located((By.ID, "header-toolbar-indicators"))).click()
        # self.wait_until(EC.presence_of_element_located((By.CSS_SELECTOR, ".input-qm7Rg5MB"))).send_keys("Super OrderBlock")

        # time.sleep(3)

        # self.wait_until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-title='Super OrderBlock / FVG / BoS Tools by makuchaku & eFe']"))).click()
        # self.driver.implicitly_wait(1)

        try:
            self.driver.execute_script("""
                const el = document.getElementById('overlap-manager-root');
                if (el) {
                    el.remove();
                }
            """)
            print("[TradingViewParser] Got popup when selecting Super OrderBlock! Probably not logged in!")
        except Exception as ex:
            print(traceback.format_exc())

        try:
            hide_indicator_button = self.wait_until(EC.presence_of_element_located((By.CSS_SELECTOR, "[title='Скрыть информацию об индикаторах']")))

            if hide_indicator_button is not None:
                hide_indicator_button.click()
        except TimeoutException as ex:
            print("[TradingViewParser] Couldn't find hide indicator button")

        time.sleep(3)

        chart = self.wait_until(EC.presence_of_element_located((By.CLASS_NAME, "chart-container")))
        screenshot_data = chart.screenshot_as_png

        return screenshot_data

    def quit(self):
        self.driver.quit()
