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
