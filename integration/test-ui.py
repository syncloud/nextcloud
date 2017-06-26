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

    firefox_path = '{0}/firefox/firefox'.format(DIR)
    caps = DesiredCapabilities.FIREFOX
    caps["marionette"] = True
    caps['acceptSslCerts'] = True

    binary = FirefoxBinary(firefox_path)

    profile = webdriver.FirefoxProfile()
    profile.add_extension('{0}/JSErrorCollector.xpi'.format(DIR))
    profile.set_preference('app.update.auto', False)
    profile.set_preference('app.update.enabled', False)
    driver = webdriver.Firefox(profile,
                               capabilities=caps, log_path="{0}/firefox.log".format(LOG_DIR),
                               firefox_binary=binary, executable_path=join(DIR, 'geckodriver/geckodriver'))
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
    driver.get_screenshot_as_file(join(screenshot_dir, 'login.png'))
    # print(driver.page_source.encode('utf-8'))

    password.send_keys(Keys.RETURN)
    driver.get_screenshot_as_file(join(screenshot_dir, 'login_progress.png'))
    #time.sleep(30)
    #driver.get_screenshot_as_file(join(screenshot_dir, 'login_progress_2.png'))
   
    # try:
    #     password.submit()
    # except WebDriverException, e:
    #     if 'submit is not a function' in e.msg:
    #         print("https://github.com/SeleniumHQ/selenium/issues/3483")
    #         print(e)
    #         pass
    #     else:
    #         raise e
    # time.sleep(5)
    #
    
    wait_driver = WebDriverWait(driver, 120)
    #wait_driver.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, '#header #expandDisplayName'), DEVICE_USER))

    wait_driver.until(EC.element_to_be_clickable((By.ID, 'closeWizard')))
    wizard_close_button = driver.find_element_by_id("closeWizard")
    wizard_close_button.click()

    time.sleep(2)
    driver.get_screenshot_as_file(join(screenshot_dir, 'main.png'))


def test_settings(driver, user_domain):
    driver.get("https://{0}/index.php/settings/admin".format(user_domain))
    time.sleep(10)
    driver.get_screenshot_as_file(join(screenshot_dir, 'admin.png'))
