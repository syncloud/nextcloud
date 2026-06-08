import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { deviceUser, devicePassword, appDomain, wizardLocator, wizardCloseLocator } from '../helpers/auth'

test.describe('login', () => {
  test('user signs in and dismisses the first-run wizard', async ({ page }, testInfo) => {
    await page.goto('/')
    await page.locator('#user').fill(deviceUser)
    await page.locator('#password').fill(devicePassword)
    await shoot(page, testInfo, 'login')
    await page.locator('#password').press('Enter')
    await expect(page).toHaveURL(/\/apps\//, { timeout: 30_000 })

    const wizard = page.locator(wizardLocator)
    await expect(wizard).toBeVisible({ timeout: 30_000 })
    await shoot(page, testInfo, 'main_first_time')
    await page.locator(wizardCloseLocator).click()
    await expect(wizard).toBeHidden({ timeout: 30_000 })
    await shoot(page, testInfo, 'main')
  })

  test('webdav accepts syncloud password basic auth', async ({ request }) => {
    const auth = 'Basic ' + Buffer.from(`${deviceUser}:${devicePassword}`).toString('base64')
    const resp = await request.fetch(`https://${appDomain}/remote.php/webdav/`, {
      method: 'PROPFIND',
      headers: { Authorization: auth, Depth: '0' },
    })
    expect(resp.status()).toBe(207)
  })
})
