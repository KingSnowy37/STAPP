import html
import webbrowser

from .paths import DATA_DIR, REPORT_PATH
from .reporting import format_minutes, get_all_days, get_today_stats


def build_report_html() -> str:
    today = get_today_stats()
    rows = get_all_days()

    table_rows = "\n".join(
        f"""
        <tr>
          <td>{html.escape(day_key)}</td>
          <td>{html.escape(format_minutes(tracked_minutes))}</td>
          <td>{html.escape(format_minutes(active_minutes))}</td>
        </tr>
        """.strip()
        for day_key, tracked_minutes, active_minutes in rows
    )

    if not table_rows:
        table_rows = """
        <tr>
          <td colspan="3">No tracking data yet.</td>
        </tr>
        """.strip()

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Screen Time Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f4ee;
      --card: #fffdf8;
      --ink: #1f1b16;
      --muted: #6d6255;
      --line: #ded3c4;
      --accent: #b85c38;
      --accent-soft: #f4dfd3;
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, #fff7ef 0, transparent 28%),
        linear-gradient(180deg, #f4efe6 0%, var(--bg) 100%);
      color: var(--ink);
    }}

    .wrap {{
      max-width: 920px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}

    .hero {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 14px 40px rgba(66, 39, 19, 0.08);
    }}

    h1 {{
      margin: 0 0 10px;
      font-size: 34px;
      line-height: 1.05;
    }}

    p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }}

    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin-top: 22px;
    }}

    .stat {{
      background: var(--accent-soft);
      border-radius: 14px;
      padding: 16px;
    }}

    .label {{
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    .value {{
      font-size: 28px;
      font-weight: 700;
    }}

    .table-card {{
      margin-top: 22px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 14px 40px rgba(66, 39, 19, 0.05);
    }}

    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 8px;
    }}

    th, td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--line);
    }}

    th {{
      font-size: 13px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}

    @media (max-width: 640px) {{
      h1 {{ font-size: 28px; }}
      .wrap {{ padding: 20px 14px 32px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>Screen Time Report</h1>
      <p>Local activity tracking only. No data leaves this computer.</p>
      <div class="stats">
        <div class="stat">
          <span class="label">Today Active</span>
          <span class="value">{html.escape(format_minutes(today["active_minutes"]))}</span>
        </div>
        <div class="stat">
          <span class="label">Today Tracked</span>
          <span class="value">{html.escape(format_minutes(today["tracked_minutes"]))}</span>
        </div>
        <div class="stat">
          <span class="label">Avg Idle</span>
          <span class="value">{today["avg_idle_seconds"]}s</span>
        </div>
      </div>
    </section>

    <section class="table-card">
      <h2>Daily Totals</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Tracked</th>
            <th>Active</th>
          </tr>
        </thead>
        <tbody>
          {table_rows}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""


def write_report() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report_html(), encoding="utf-8")


def open_report() -> None:
    write_report()
    webbrowser.open(REPORT_PATH.resolve().as_uri())
