// tests/scan.spec.ts
import { test, expect } from '@playwright/test';
import fs from 'fs';

test('scan generates a valid JSON file', async ({ page }) => {
  // Ensure latest_scan.json exists
  const jsonPath = 'data/latest_scan.json';
  expect(fs.existsSync(jsonPath)).toBeTruthy();

  // Load JSON
  const raw = fs.readFileSync(jsonPath, 'utf-8');
  const data = JSON.parse(raw);

  // Check structure
  expect(data).toHaveProperty('page_url');
  expect(data).toHaveProperty('timestamp');
  expect(data).toHaveProperty('total_violations');
});
