import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import {
  signIn, dismissWizard, openMenuItem, openSettingsSection,
  appDomain, deviceUser, devicePassword,
} from '../helpers/auth'

test.describe('nextcloud', () => {
  test('a user signs in and navigates the app by clicking', async ({ page }, info) => {
    await test.step('sign in and dismiss the first-run wizard', async () => {
      await signIn(page)
      await dismissWizard(page)
      await shoot(page, info, 'main')
    })

    await test.step('webdav accepts syncloud password basic auth', async () => {
      const auth = 'Basic ' + Buffer.from(`${deviceUser}:${devicePassword}`).toString('base64')
      const resp = await page.request.fetch(`https://${appDomain}/remote.php/webdav/`, {
        method: 'PROPFIND', headers: { Authorization: auth, Depth: '0' },
      })
      expect(resp.status()).toBe(207)
    })

    await test.step('administration overview shows no setup warnings we care about', async () => {
      await openMenuItem(page, 'settings_administration')
      await expect(page.locator('//h2[contains(.,"setup warnings")]')).toBeVisible()
      expect(await page.content()).not.toContain('no SVG support')
      await shoot(page, info, 'admin-security')
    })

    await test.step('basic settings shows background jobs', async () => {
      await openSettingsSection(page, '/settings/admin/server')
      await expect(page.locator('//h2[contains(.,"Background jobs")]')).toBeVisible()
      await shoot(page, info, 'admin')
    })

    await test.step('ldap integration page loads', async () => {
      await openSettingsSection(page, '/settings/admin/ldap')
      await expect(page.locator('//h2[text()="LDAP/AD integration"]')).toBeVisible()
      await shoot(page, info, 'admin-ldap')
    })

    await test.step('integrity check reports no errors', async () => {
      const resp = await page.request.get(`https://${appDomain}/settings/integrity/failed`)
      const body = await resp.text()
      expect(body).toContain('No errors have been found.')
      expect(body).not.toContain('INVALID_HASH')
      expect(body).not.toContain('EXCEPTION')
    })

    await test.step('configure collabora with own server', async () => {
      await openSettingsSection(page, '/settings/admin/richdocuments')
      await page.locator('//label[normalize-space(text())="Use your own server"]').click()
      await shoot(page, info, 'office-own')
      const url = page.locator('#wopi_url')
      await url.clear()
      await url.fill(`https://${appDomain}`)
      await page.locator('//*[normalize-space(text())="Disable certificate verification (insecure)"]').click()
      await page.locator('//input[@value="Save"]').click()
      await shoot(page, info, 'office-status')
    })

    await test.step('users list loads without server error', async () => {
      await openMenuItem(page, 'core_users')
      await expect(page.locator('//a[@title="Admins"]')).toBeVisible()
      expect(await page.content()).not.toContain('Server Error')
      await shoot(page, info, 'users')
    })

    await test.step('personal settings show the profile picture controls', async () => {
      await openMenuItem(page, 'settings_personal')
      await expect(page.getByRole('heading', { name: 'Profile & contact' })).toBeVisible()
      await expect(page.getByText('Upload profile picture')).toBeVisible()
      await shoot(page, info, 'user')
    })

    await test.step('install memories from the app store', async () => {
      await openMenuItem(page, 'appstore')
      const search = page.getByRole('searchbox')
        .or(page.getByPlaceholder(/search/i))
        .or(page.locator('input[type="search"]'))
        .first()
      await search.fill('memories')
      await page.getByRole('link', { name: /^memories/i }).first().click()
      await page.locator('//input[@value="Download and enable"] | //button[@aria-label="Download and enable"]').click()
      await expect(page.locator('//div[contains(.,"Error")]')).toHaveCount(0)
      await shoot(page, info, 'install-app')
    })
  })
})
