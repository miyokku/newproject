from __future__ import annotations

import threading

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from werkzeug.serving import make_server


class TestServer(threading.Thread):
    def __init__(self, flask_app):
        super().__init__(daemon=True)
        self.server = make_server("127.0.0.1", 0, flask_app)
        self.port = self.server.server_port
        self.context = flask_app.app_context()
        self.context.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()
        self.context.pop()


@pytest.fixture()
def live_server(isolated_app):
    server = TestServer(isolated_app)
    server.start()
    yield f"http://127.0.0.1:{server.port}"
    server.shutdown()


@pytest.fixture()
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1366,768")

    browser = webdriver.Chrome(options=options)
    yield browser
    browser.quit()


def wait(driver, timeout: int = 5):
    return WebDriverWait(driver, timeout)


@pytest.mark.ui
def test_guest_sees_home_page_and_registration_link(driver, live_server):
    driver.get(live_server + "/")

    assert driver.title == "MediaHub Lab"
    assert driver.find_element(By.TAG_NAME, "h2").text == "Лента"
    assert driver.find_element(By.LINK_TEXT, "Регистрация").is_displayed()


@pytest.mark.ui
def test_anonymous_user_is_redirected_to_login_page(driver, live_server):
    driver.get(live_server + "/post/new")

    wait(driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
    assert "Вход" in driver.page_source
    assert "/login" in driver.current_url


@pytest.mark.ui
def test_wrong_login_message_is_visible(driver, live_server):
    driver.get(live_server + "/login")

    driver.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys("wrong")
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys("bad")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait(driver).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, ".flash"), "Wrong credentials"))
    assert "Wrong credentials" in driver.page_source


@pytest.mark.ui
def test_user_can_register_login_and_create_text_post(driver, live_server):
    username = "selenium_user"
    password = "1234"
    post_text = "Selenium проверяет создание публикации"

    driver.get(live_server + "/register")
    driver.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys(username)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait(driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']")))
    assert "Registered" in driver.page_source

    driver.find_element(By.CSS_SELECTOR, "input[name='username']").send_keys(username)
    driver.find_element(By.CSS_SELECTOR, "input[name='password']").send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait(driver).until(EC.presence_of_element_located((By.LINK_TEXT, "➕ Новый пост")))
    driver.find_element(By.LINK_TEXT, "➕ Новый пост").click()

    wait(driver).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='text']")))
    driver.find_element(By.CSS_SELECTOR, "textarea[name='text']").send_keys(post_text)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait(driver).until(EC.text_to_be_present_in_element((By.TAG_NAME, "body"), post_text))
    assert post_text in driver.page_source
    assert username in driver.page_source
