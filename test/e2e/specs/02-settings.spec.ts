import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { signIn } from '../helpers/auth'

test.describe('settings', () => {
  test.beforeEach(async ({ page }) => {
    await signIn(page)
  })

  test('admin overview shows background jobs', async ({ page }, testInfo) => {
    await page.goto('/settings/admin')
    await expect(page.locator('//h2[contains(.,"Background jobs")]')).toBeVisible()
    await shoot(page, testInfo, 'admin')
  })

  test('personal settings show profile picture', async ({ page }, testInfo) => {
    await page.goto('/settings/user')
    await expect(page.locator('//label[contains(.,"Profile picture")]')).toBeVisible()
    await shoot(page, testInfo, 'user')
  })

  test('ldap integration page loads', async ({ page }, testInfo) => {
    await page.goto('/settings/admin/ldap')
    await expect(page.locator('//h2[text()="LDAP/AD integration"]')).toBeVisible()
    await shoot(page, testInfo, 'admin-ldap')
  })

  test('security warnings show no SVG support error', async ({ page }, testInfo) => {
    await page.goto('/settings/admin/overview#security-warning')
    await expect(page.locator('//h2[contains(.,"setup warnings")]')).toBeVisible()
    await shoot(page, testInfo, 'admin-security')
    expect(await page.content()).not.toContain('no SVG support')
  })

  test('integrity check reports no errors', async ({ page }, testInfo) => {
    await page.goto('/settings/integrity/failed')
    await expect(page.locator('//pre[text()="No errors have been found."]')).toBeVisible()
    await shoot(page, testInfo, 'integrity-failed')
    const source = await page.content()
    expect(source).not.toContain('INVALID_HASH')
    expect(source).not.toContain('EXCEPTION')
  })

  test('users list loads without server error', async ({ page }, testInfo) => {
    await page.goto('/settings/users')
    await expect(page.locator('//a[@title="Admins"]')).toBeVisible()
    await shoot(page, testInfo, 'users')
    expect(await page.content()).not.toContain('Server Error')
  })
})
