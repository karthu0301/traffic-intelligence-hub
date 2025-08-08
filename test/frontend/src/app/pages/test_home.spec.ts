import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Home Page UI (mocked backend)', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('token', 'mock-token');
    });

    await page.route('**/upload*', async route => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ success: true }),
        contentType: 'application/json',
      });
    });

    await page.route('**/search*', async route => {
      await new Promise(r => setTimeout(r, 100));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              id: 99,
              filename: 'mock-image.jpg',
              annotated_image: '/images/annotated.jpg',
              timestamp: '2025-08-07T12:00:00Z',
              detections: [
                { plate_string: 'MOCK123', plate_confidence: 0.9, plate_crop_path: '/images/crop1.jpg' },
              ],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.route('**/result/*', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 99,
            filename: 'mock-image.jpg',
            annotated_image: '/images/annotated.jpg',
            timestamp: '2025-08-07T12:00:00Z',
            detections: [
              { plate_string: 'MOCK123', plate_confidence: 0.9, plate_crop_path: '/images/crop1.jpg' },
            ],
          }),
        });
      });

    await page.route('**/ask*', async route => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          answer: 'Mocked dev assistant response about MOCK123.',
        }),
        contentType: 'application/json',
      });
    });

    await page.goto('/');
  });

  test('renders home title and login/logout button', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Traffic Intelligence Hub' })).toBeVisible();
    const loginOrLogout = await page.getByRole('button', { name: /login|logout/i });
    await expect(loginOrLogout).toBeVisible();
  });

  test('uploads a file and shows filename', async ({ page }) => {
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText('Choose File(s)').click();
    const fileChooser = await fileChooserPromise;

    const filePath = path.resolve(__dirname, 'assets/sample.jpg');
    await fileChooser.setFiles(filePath);

    await expect(page.locator('text=sample.jpg')).toBeVisible();
    await page.getByRole('button', { name: /upload image/i }).click();
  });

  test('mocks and displays LLM response', async ({ page }) => {
    await page.getByPlaceholder('e.g. What plates were most common yesterday?').fill('Most common plate?');
    await page.getByRole('button', { name: 'Ask' }).click();
    await expect(page.locator('text=MOCK123')).toBeVisible();
  });

  test('renders upload history list', async ({ page }) => {
    await expect(page.getByText('mock-image.jpg')).toBeVisible();
  });

  test('clicks on upload history item and shows detection result', async ({ page }) => {
    const historyItem = page.getByText('mock-image.jpg');
    await expect(historyItem).toBeVisible();
    await historyItem.click();

    await expect(page.getByText('Detection Results')).toBeVisible();
    await expect(page.getByText('MOCK123')).toBeVisible();
  });

  test('changes sort order in upload history', async ({ page }) => {
    await expect(page.getByText('mock-image.jpg')).toBeVisible();

    const sortBySelect = page.locator(
      'select:has(option[value="filename"])'
    );
    const orderSelect = page.locator(
      'select:has(option[value="asc"])'
    );

    await expect(sortBySelect).toBeVisible();
    await sortBySelect.selectOption('filename');

    await expect(orderSelect).toBeVisible();
    await orderSelect.selectOption('asc');
  });

  test('switches report range and renders export button', async ({ page }) => {
    await page.selectOption('select', 'monthly');
    await expect(page.getByRole('button', { name: /export as csv/i })).toBeVisible();
  });
});
