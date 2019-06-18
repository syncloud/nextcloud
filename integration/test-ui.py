import os
import shutil
from os.path import dirname, join, exists
import time
import pytest

from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.screenshots import screenshots

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
screenshot_dir = join(DIR, 'screenshot')
TMP_DIR = '/tmp/syncloud/ui'


@pytest.fixture(scope="session")
def module_setup(request, device, log_dir, ui_mode):
    request.addfinalizer(lambda: module_teardown(device, log_dir, ui_mode))


def module_teardown(device, log_dir, ui_mode):
    device.activated()
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
    device.run_ssh('journalctl > {0}/journalctl.ui.{1} log'.format(TMP_DIR, ui_mode), throw=False)
    device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
      
    device.scp_from_device('{0}/*'.format(TMP_DIR), join(log_dir, 'log'))


def test_start(module_setup, app, device_host):
    if not exists(screenshot_dir):
        os.mkdir(screenshot_dir)

    add_host_alias(app, device_host)

def test_login(driver, app_domain):

    driver.get("https://{0}".format(app_domain))
    time.sleep(10)
    print(driver.execute_script('return window.JSErrorCollector_errors ? window.JSErrorCollector_errors.pump() : []'))


def test_main(driver, app_domain, device_user, device_password):

    user = driver.find_element_by_id("user")
    user.send_keys(device_user)
    password = driver.find_element_by_id("password")
    password.send_keys(device_password)
    screenshots(driver, screenshot_dir, 'login')
    # print(driver.page_source.encode('utf-8'))

    password.send_keys(Keys.RETURN)
    #time.sleep(10)
    screenshots(driver, screenshot_dir, 'login_progress')
       
    wait_driver = WebDriverWait(driver, 300)

    wait_driver.until(EC.element_to_be_clickable((By.ID, 'cboxClose')))
    wizard_close_button = driver.find_element_by_id("cboxClose")
    screenshots(driver, screenshot_dir, 'main_first_time')
    wizard_close_button.click()

    time.sleep(2)
    screenshots(driver, screenshot_dir, 'main')


def test_settings(driver, app_domain):
    driver.get("https://{0}/index.php/settings/admin".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin')


def test_settings_user(driver, app_domain):
    driver.get("https://{0}/index.php/settings/user".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'user')


def test_settings_user(driver, app_domain):
    driver.get("https://{0}/index.php/settings/admin/ldap".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-ldap')


def test_settings_security(driver, app_domain):
    driver.get("https://{0}/index.php/settings/admin/overview#security-warning".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-security')


def test_settings_additional(driver, app_domain):
    driver.get("https://{0}/index.php/settings/admin/additional".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-additional')
