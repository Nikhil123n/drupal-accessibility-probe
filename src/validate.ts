import fs from 'fs';
import path from 'path';

function loadJson(p: string) {
  return JSON.parse(fs.readFileSync(p, 'utf-8'));
}

function summarize(scan: any) {
  const out: any = {};
  out.page_url = scan.page_url;
  out.timestamp = scan.timestamp;
  out.total_violations = scan.total_violations ?? scan.total_violations;
  out.top_rules = Object.entries(scan.violations_by_rule || {})
    .sort((a: any, b: any) => (b[1] as number) - (a[1] as number))
    .slice(0, 5)
    .map(([rule, count]) => ({ rule, count }));
  return out;
}

if (require.main === module) {
  const arg = process.argv[2] || path.join(__dirname, '..', 'data', 'latest_scan.json');
  if (!fs.existsSync(arg)) {
    console.error('File not found:', arg);
    process.exit(2);
  }
  const scan = loadJson(arg);
  const s = summarize(scan);
  console.log(JSON.stringify(s, null, 2));
  process.exit(0);
}

export { summarize };
