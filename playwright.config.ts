import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './test/frontend/src/app/pages',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000,
  },
  reporter: 'list',
  use: {
    baseURL: 'http://192.168.50.143:3000',
    headless: true,
    viewport: { width: 1280, height: 720 },
    ignoreHTTPSErrors: true,
  },
});
