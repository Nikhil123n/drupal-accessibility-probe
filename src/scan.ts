import fs from 'fs';
import path from 'path';
import { chromium } from 'playwright';
import axeSource from 'axe-core';

type AxeResult = any;

// Run axe-core scan on a single page
async function runScan(url: string) {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'load', timeout: 60000 });

  // Inject axe-core
  await page.addScriptTag({ content: `${axeSource.source}` });

  const result: AxeResult = await page.evaluate(async () => {
    // @ts-ignore
    return await (window as any).axe.run(document, {
      runOnly: {
        type: 'tag',
        values: ['wcag21','wcag2aa','wcag2a','best-practice']
      }
    });
  });

  await browser.close();
  return result;
}

// Summarize axe-core violations
function summarizeAxe(axeRes: any) {
  const violations = axeRes.violations || [];
  const violations_by_rule: Record<string, number> = {};
  for (const v of violations) {
    const id = v.id;
    violations_by_rule[id] = (violations_by_rule[id] || 0) + v.nodes.length;
  }
  const total = violations.reduce((acc: number, v: any) => acc + v.nodes.length, 0);
  return { total, violations_by_rule };
}

// Main scan routine
async function main() {
  const targetsPath = path.join(__dirname, 'targets.json');
  const targets: string[] = JSON.parse(fs.readFileSync(targetsPath, 'utf-8'));

  const results: any[] = [];

  for (const url of targets) {
    console.log('Scanning', url);
    try {
      const axeRes = await runScan(url);
      const summary = summarizeAxe(axeRes);

      const scanRecord = {
        page_url: url,
        timestamp: new Date().toISOString(),
        total_violations: summary.total,
        violations_by_rule: summary.violations_by_rule,
        raw: axeRes
      };

      results.push(scanRecord);
      console.log('Scan completed for', url);
    } catch (err) {
      console.error('Scan failed for', url, err);
    }
  }

  // Save all scan results as an array in one JSON file
  const outDir = path.join(__dirname, '..', 'data');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.join(outDir, 'latest_scan.json');
  fs.writeFileSync(outPath, JSON.stringify(results, null, 2));
  console.log('All scan results saved to', outPath);

  return results;
}

// Run the scan if executed directly
if (require.main === module) {
  main()
    .then(() => process.exit(0))
    .catch(err => { console.error(err); process.exit(1); });
}
