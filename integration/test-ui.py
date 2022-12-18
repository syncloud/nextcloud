from os.path import dirname, join
from subprocess import check_output

import pytest
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from syncloudlib.integration.hosts import add_host_alias

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


def test_start(module_setup, app, domain, device_host):
    add_host_alias(app, device_host, domain)


def test_login(selenium):
    selenium.open_app()


def test_main(selenium, device_user, device_password, ui_mode, screenshot_dir):

    selenium.find_by_id("user").send_keys(device_user)
    password = selenium.find_by_id("password")
    password.send_keys(device_password)
    selenium.screenshot('login')
    password.send_keys(Keys.RETURN)
    selenium.find_by_xpath("//span[text()='test00']")

    if ui_mode == "desktop":
        close_css_selector = 'button.header-close'
        wizard_close_button = selenium.find_by_css(close_css_selector)
        selenium.screenshot('main_first_time')
        hover = ActionChains(selenium.driver).move_to_element(wizard_close_button)
        hover.perform()
        selenium.screenshot('main_first_time-hover')
        selenium.wait_driver.until(EC.element_to_be_clickable((By.CSS_SELECTOR, close_css_selector)))
        selenium.screenshot('main_first_time-click')
        wizard_close_button.click()

    selenium.screenshot('main')


def test_settings(selenium, app_domain):
    selenium.driver.get("https://{0}/settings/admin".format(app_domain))
    selenium.find_by_xpath("//h2[contains(.,'Background jobs')]")
    selenium.screenshot('admin')


def test_settings_user(selenium, app_domain):
    selenium.driver.get("https://{0}/settings/user".format(app_domain))
    selenium.find_by_xpath("//h3[contains(.,'Profile picture')]")
    selenium.screenshot('user')


def test_settings_ldap(selenium, app_domain):
    selenium.driver.get("https://{0}/settings/admin/ldap".format(app_domain))
    selenium.find_by_xpath("//h2[text()='LDAP/AD integration']")
    selenium.screenshot('admin-ldap')


def test_settings_security(selenium, app_domain):
    selenium.driver.get("https://{0}/settings/admin/overview#security-warning".format(app_domain))
    selenium.find_by_xpath("//h2[text()='Security & setup warnings']")
    progress_xpath = "//span[text()='Checking for system and security issues.']"
    selenium.find_by_xpath(progress_xpath)
    selenium.wait_or_screenshot(EC.invisibility_of_element_located((By.XPATH, progress_xpath)))
    source = selenium.driver.page_source
    selenium.screenshot('admin-security')
    assert 'no SVG support' not in source


# def test_settings_additional(selenium, app_domain):
#     selenium.driver.get("https://{0}/settings/admin/additional".format(app_domain))
#     selenium.find_by_xpath("//h2[text()='Maps routing settings']")
#     selenium.screenshot('admin-additional')


# def test_apps_calendar(selenium, app_domain):
#     selenium.driver.get("https://{0}/calendar".format(app_domain))
#     selenium.find_by_xpath("//span[@text()='+ New calendar']")
#     selenium.screenshot('calendar')


def test_verification(selenium, app_domain):
    selenium.driver.get('https://{0}/settings/integrity/failed'.format(app_domain))
    selenium.find_by_xpath("//pre[text()='No errors have been found.']")
    selenium.screenshot('integrity-failed')
    source = selenium.driver.page_source
    assert 'INVALID_HASH' not in source
    assert 'EXCEPTION' not in source


def test_users(selenium, app_domain, ui_mode):
    selenium.driver.get('https://{0}/settings/users'.format(app_domain))
    if ui_mode == "desktop":
        selenium.find_by_xpath("//span[@title='Admins']")
    selenium.screenshot('users')
    source = selenium.driver.page_source
    assert 'Server Error' not in source


def test_office(selenium, app_domain):
    selenium.driver.get('https://{0}/settings/admin/richdocuments'.format(app_domain))
    selenium.find_by_xpath("//label[normalize-space(text())='Use your own server']").click()
    selenium.screenshot('office-own')
    url = selenium.find_by_xpath("//input[@id='wopi_url']")
    url.clear()
    url.send_keys("https://{0}".format(app_domain))
    selenium.find_by_xpath("//*[normalize-space(text())='Disable certificate verification (insecure)']").click()
    selenium.screenshot('office-own-url')
    selenium.find_by_xpath("//input[@value='Save']").click()
    #selenium.find_by_xpath("//span[normalize-space(text())='Collabora Online server is reachable.']")
    selenium.screenshot('office-status')


def test_teardown(driver):
    driver.quit()

