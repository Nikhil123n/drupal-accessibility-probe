import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',       // folder with Playwright tests
  timeout: 30000,
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  reporter: [['list']],
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' }
    }
  ],
  // IGNORE all Jest tests
  testIgnore: ['**/jest_tests/**']
});
