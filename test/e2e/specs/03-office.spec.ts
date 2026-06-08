import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { signIn, appDomain } from '../helpers/auth'

test.describe('office', () => {
  test('configure collabora with own server', async ({ page }, testInfo) => {
    await signIn(page)
    await page.goto('/settings/admin/richdocuments')
    await page.locator('//label[normalize-space(text())="Use your own server"]').click()
    await shoot(page, testInfo, 'office-own')

    const url = page.locator('#wopi_url')
    await url.clear()
    await url.fill(`https://${appDomain}`)
    await page.locator('//*[normalize-space(text())="Disable certificate verification (insecure)"]').click()
    await shoot(page, testInfo, 'office-own-url')

    await page.locator('//input[@value="Save"]').click()
    await shoot(page, testInfo, 'office-status')
  })
})
