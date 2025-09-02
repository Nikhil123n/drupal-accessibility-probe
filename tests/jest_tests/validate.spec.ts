import { summarize } from '../../src/validate';

const sample = {
  page_url: "http://example.com",
  timestamp: "2025-09-01T00:00:00Z",
  total_violations: 3,
  violations_by_rule: { "image-alt": 2, "color-contrast": 1 }
};

test('summarize extracts key fields', () => {
  const s = summarize(sample);
  expect(s.page_url).toBe(sample.page_url);
  expect(s.total_violations).toBe(3);
});
