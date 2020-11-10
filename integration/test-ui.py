import os
from os.path import dirname, join, exists
from subprocess import check_output

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from syncloudlib.integration.hosts import add_host_alias_by_ip
from syncloudlib.integration.screenshots import screenshots

DIR = dirname(__file__)
TMP_DIR = '/tmp/syncloud/ui'


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir, ui_mode):
    def module_teardown():
        device.activated()
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl > {0}/journalctl.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
        device.run_ssh('cp /var/log/syslog {0}/syslog.ui.{1}.log'.format(TMP_DIR, ui_mode), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), join(artifact_dir, 'log'))
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def test_start(module_setup, app, domain, device_host, screenshot_dir):
    if not exists(screenshot_dir):
        os.mkdir(screenshot_dir)
    add_host_alias_by_ip(app, domain, device_host)


def test_login(driver, app_domain):
    driver.get("https://{0}".format(app_domain))
    time.sleep(10)


def test_main(driver, device_user, device_password, ui_mode, screenshot_dir):

    user = driver.find_element_by_id("user")
    user.send_keys(device_user)
    password = driver.find_element_by_id("password")
    password.send_keys(device_password)
    screenshots(driver, screenshot_dir, 'login-' + ui_mode)
    # print(driver.page_source.encode('utf-8'))

    password.send_keys(Keys.RETURN)
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'login_progress-' + ui_mode)
       
    wait_driver = WebDriverWait(driver, 100)

    if ui_mode == "desktop":
        close_css_selector = 'button.header-close'
        wait_driver.until(EC.presence_of_element_located((By.CSS_SELECTOR, close_css_selector)))
        wizard_close_button = driver.find_element_by_css_selector(close_css_selector)
        screenshots(driver, screenshot_dir, 'main_first_time-' + ui_mode)
        hover = ActionChains(driver).move_to_element(wizard_close_button)
        hover.perform()
        screenshots(driver, screenshot_dir, 'main_first_time-hover-' + ui_mode)
        wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, close_css_selector)))
        screenshots(driver, screenshot_dir, 'main_first_time-click' + ui_mode)
        wizard_close_button.click()
    
    time.sleep(2)
    screenshots(driver, screenshot_dir, 'main-' + ui_mode)


def test_settings(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/settings/admin".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-' + ui_mode)


def test_settings_user(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/settings/user".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'user-' + ui_mode)


def test_settings_ldap(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/settings/admin/ldap".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-ldap-' + ui_mode)


def test_settings_security(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/settings/admin/overview#security-warning".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-security-' + ui_mode)


def test_settings_additional(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/settings/admin/additional".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'admin-additional-' + ui_mode)


def test_apps_calendar(driver, app_domain, ui_mode, screenshot_dir):
    driver.get("https://{0}/calendar".format(app_domain))
    time.sleep(10)
    screenshots(driver, screenshot_dir, 'calendar-' + ui_mode)


def test_verification(driver, app_domain, ui_mode, screenshot_dir):
    driver.get('https://{0}/settings/integrity/failed'.format(app_domain))
    screenshots(driver, screenshot_dir, 'integrity-failed-' + ui_mode)
    source = driver.page_source.encode("utf-8")
    assert 'INVALID_HASH' not in source
    assert 'EXCEPTION' not in source


def test_users(driver, app_domain, ui_mode, screenshot_dir):
    driver.get('https://{0}/settings/users'.format(app_domain))
    screenshots(driver, screenshot_dir, 'users-' + ui_mode)
    source = driver.page_source.encode("utf-8")
    assert 'Server Error' not in source
