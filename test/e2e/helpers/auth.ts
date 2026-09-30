import { Page, expect } from '@playwright/test'

export function required(name: string): string {
  const v = process.env[name]
  if (!v) throw new Error(`${name} is required`)
  return v
}

export const deviceUser = required('PLAYWRIGHT_DEVICE_USER')
export const devicePassword = required('PLAYWRIGHT_DEVICE_PASSWORD')
export const appDomain = required('PLAYWRIGHT_APP_DOMAIN')

const wizard = '//div[contains(@class, "first-run-wizard")]'
const wizardClose = wizard + '//div[@class="modal-container__content"]//button[@aria-label="Close"]'

export async function signIn(page: Page, user: string = deviceUser, password: string = devicePassword) {
  await page.goto('/')
  await page.locator('#user').fill(user)
  await page.locator('#password').fill(password)
  await page.locator('#password').press('Enter')
  await expect(page).toHaveURL(/\/apps\//, { timeout: 30_000 })
}

export const wizardLocator = wizard
export const wizardCloseLocator = wizardClose

export async function dismissWizard(page: Page) {
  const w = page.locator(wizard)
  if (await w.isVisible().catch(() => false)) {
    await page.locator(wizardClose).click()
    await expect(w).toBeHidden({ timeout: 30_000 })
  }
}

export async function openUserMenu(page: Page) {
  await page.getByRole('button', { name: 'Settings menu' }).click()
}

export async function openMenuItem(page: Page, id: string) {
  await openUserMenu(page)
  await page.locator('#' + id).click()
}

export async function openSettingsSection(page: Page, href: string) {
  await page.locator('a[href="' + href + '"]').first().click()
}
