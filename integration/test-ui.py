import os
import shutil
from os.path import dirname, join, exists
import time
import pytest
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.support.ui import WebDriverWait

DIR = dirname(__file__)
LOG_DIR = join(DIR, 'log')
DEVICE_USER = 'user'
DEVICE_PASSWORD = 'password'
log_dir = join(LOG_DIR, 'nextcloud_log')
screenshot_dir = join(DIR, 'screenshot')


@pytest.fixture(scope="module")
def driver():

    if exists(screenshot_dir):
        shutil.rmtree(screenshot_dir)
    os.mkdir(screenshot_dir)

    firefox_path = '/tools/firefox/firefox'
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    profile = webdriver.FirefoxProfile()
    profile.add_extension('/tools/firefox/JSErrorCollector.xpi')
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    driver = webdriver.Firefox(profile,
                               capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR),
                               firefox_binary=binary, executable_path=join(DIR, '/tools/geckodriver/geckodriver'))

    # driver.set_page_load_timeout(30)
    # print driver.capabilities['version']
    return driver


def test_login(driver, user_domain):

    driver.get("https://{0}".format(user_domain))
    time.sleep(10)
    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_main(driver, user_domain):

    user = driver.find_element_by_id("user")
    user.send_keys(DEVICE_USER)
    password = driver.find_element_by_id("password")
    password.send_keys(DEVICE_PASSWORD)
    screenshots(driver, screenshot_dir, 'login')
    # print(driver.page_source.encode('utf-8'))

    password.send_keys(Keys.RETURN)
    screenshots(driver, screenshot_dir, 'login_progress')
       
    wait_driver = WebDriverWait(driver, 120)

    wait_driver.until(EC.element_to_be_clickable((By.ID, 'closeWizard')))
    wizard_close_button = driver.find_element_by_id("closeWizard")
    wizard_close_button.click()

    time.sleep(2)
    screenshots(driver, screenshot_dir, 'main')


def test_settings(driver, user_domain):
    driver.get("https://{0}/index.php/settings/admin".format(user_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin')


def test_settings_user(driver, user_domain):
    driver.get("https://{0}/index.php/settings/user".format(user_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'user')


def test_settings_user(driver, user_domain):
    driver.get("https://{0}/index.php/settings/admin/ldap".format(user_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-ldap')


def screenshots(driver, dir, name):
    desktop_w = 1024
    desktop_h = 768
    driver.set_window_position(0, 0)
    driver.set_window_size(desktop_w, desktop_h)

    driver.get_screenshot_as_file(join(dir, '{}.png'.format(name)))

    mobile_w = 400
    mobile_h = 2000
    driver.set_window_position(0, 0)
    driver.set_window_size(mobile_w, mobile_h)
    driver.get_screenshot_as_file(join(dir, '{}-mobile.png'.format(name)))
    
    driver.set_window_position(0, 0)
    driver.set_window_size(desktop_w, desktop_h)
