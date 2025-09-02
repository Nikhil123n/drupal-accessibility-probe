import os
import json
import sqlite3
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = 'data'
LATEST_JSON = os.path.join(DATA_DIR, 'latest_scan.json')
DB_PATH = os.path.join(DATA_DIR, 'scans.db')
REPORTS_DIR = os.path.join('reports', 'charts')

os.makedirs(REPORTS_DIR, exist_ok=True)

def read_latest_json():
    if not os.path.exists(LATEST_JSON):
        raise FileNotFoundError(f"{LATEST_JSON} not found. Run the scanner first.")
    with open(LATEST_JSON, 'r') as f:
        data = json.load(f)
        # Ensure it's a list
        if isinstance(data, dict):
            return [data]
        return data

def insert_into_sqlite(scan):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_url TEXT,
            timestamp TEXT,
            total_violations INTEGER,
            violations_by_rule TEXT
        )
    """)
    c.execute("INSERT INTO scans (page_url, timestamp, total_violations, violations_by_rule) VALUES (?, ?, ?, ?)",
              (scan['page_url'], scan['timestamp'], scan.get('total_violations', 0), json.dumps(scan.get('violations_by_rule', {}))))
    conn.commit()
    conn.close()

def sanitize_filename(url: str) -> str:
    return url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '_')

def chart_violations_by_rule(scan):
    v = scan.get('violations_by_rule', {})
    if not v:
        print(f"No rule data to plot for {scan['page_url']}.")
        return None

    df = pd.DataFrame(list(v.items()), columns=['rule', 'count']).sort_values('count', ascending=False)
    plt.figure(figsize=(8,4))
    plt.bar(df['rule'], df['count'])
    plt.xticks(rotation=45, ha='right')
    plt.ylabel('Count')
    plt.title(f"Violations by Rule: {scan['page_url']}")
    out_filename = f"violations_{sanitize_filename(scan['page_url'])}.png"
    out_path = os.path.join(REPORTS_DIR, out_filename)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    print("Wrote", out_path)
    return out_filename

def generate_summary_html_all(scans):
    out_path = os.path.join('reports', 'summary.html')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    html = """
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Drupal Accessibility & Analytics Mini-Probe</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                padding: 20px;
                background: linear-gradient(to right, #f0f4f8, #d9e2ec);
                color: #333;
            }
            h1, h2, h3 { color: #1a73e8; }
            .site-button {
                margin: 5px;
                padding: 10px 15px;
                cursor: pointer;
                background-color: #1a73e8;
                color: white;
                border: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .site-button:hover {
                background-color: #1558b0;
            }
            .site-section { display:none; margin-top:20px; }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin-top: 20px; 
                background-color: white;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                border-radius: 8px;
                overflow: hidden;
            }
            th, td { 
                border-bottom: 1px solid #ddd; 
                padding: 12px; 
                text-align: left; 
            }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f5f9; }
            img { max-width: 800px; margin-top: 10px; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
    <h1>Drupal Accessibility & Analytics Mini-Probe</h1>
    <div id="site-buttons">
    """

    for scan in scans:
        site_id = sanitize_filename(scan['page_url'])
        html += f'<button class="site-button" onclick="showSite(\'{site_id}\')">{scan["page_url"]}</button>'

    html += "</div>"

    # Overall table
    html += """
    <h2>Overall Summary</h2>
    <table>
        <thead>
            <tr>
                <th>Page URL</th>
                <th>Timestamp</th>
                <th>Total Violations</th>
                <th>Top 3 Rule Counts</th>
            </tr>
        </thead>
        <tbody>
    """

    for scan in scans:
        top_rules = sorted(scan.get('violations_by_rule', {}).items(), key=lambda x: x[1], reverse=True)[:3]
        html += f"""
            <tr>
                <td>{scan['page_url']}</td>
                <td>{scan['timestamp']}</td>
                <td>{scan.get('total_violations',0)}</td>
                <td>{', '.join([f"{r}:{c}" for r,c in top_rules])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    # Per-site sections with charts
    from urllib.parse import urlparse
    for scan in scans:
        site_id = sanitize_filename(scan['page_url'])
        chart_file = f"charts/violations_{site_id}.png"
        # Format timestamp
        try:
            dt = datetime.fromisoformat(scan['timestamp'].replace('Z', '+00:00'))
            formatted_time = dt.strftime('%B %-d, %Y, %-I:%M %p')
        except Exception:
            formatted_time = scan['timestamp']
        # Get domain for link text
        parsed_url = urlparse(scan['page_url'])
        domain = parsed_url.hostname.replace('www.', '').capitalize() if parsed_url.hostname else scan['page_url']
        html += f"""
        <div id="{site_id}" class="site-section">
            <h2>Accessibility Report: <a href="{scan['page_url']}" target="_blank">{domain}</a></h2>
            <p><strong>Report Date:</strong> {formatted_time} | <strong>Total Violations:</strong> {scan.get('total_violations',0)}</p>
            <h3>Violations by Rule</h3>
            <img src="{chart_file}" alt="Violations chart for {scan['page_url']}">
        </div>
        """

    # JS for buttons
    html += """
    <script>
        function showSite(siteId){
            const sections = document.querySelectorAll('.site-section');
            sections.forEach(s => s.style.display = 'none');
            document.getElementById(siteId).style.display = 'block';
        }
    </script>
    </body>
    </html>
    """

    with open(out_path, 'w') as f:
        f.write(html)
    print("Wrote", out_path)


def main():
    scans = read_latest_json()  # list of scan objects
    for scan in scans:
        insert_into_sqlite(scan)
        chart_violations_by_rule(scan)  # per-site chart

    generate_summary_html_all(scans)  # table + per-site charts

if __name__ == '__main__':
    main()
