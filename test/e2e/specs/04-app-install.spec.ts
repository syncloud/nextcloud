import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { signIn } from '../helpers/auth'

test.describe('app install', () => {
  test('install memories from the app store', async ({ page }, testInfo) => {
    await signIn(page)
    await page.goto('/settings/apps/discover/memories')
    await page.locator('//input[@value="Download and enable"]').click()
    await expect(page.locator('//div[contains(.,"Error")]')).toHaveCount(0)
    await shoot(page, testInfo, 'install-app')
  })
})
