"""
Genera imagenes para Instagram usando Playwright.
Cada card es 1080x1350 px (retrato 4:5) con el diseno del blog.
"""

import os
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "instagram")


def _logo_tag(url, cls="team-logo"):
    if not url:
        return ""
    return f'<img src="{url}" class="{cls}" onerror="this.style.display=\'none\'">'


def _build_card_html(sport_name, sport_icon, picks, stats=None,
                     site_url="parleysports90.github.io/sports-blog"):
    today = datetime.now().strftime("%d %b %Y").upper()

    picks_html_parts = []
    for pick in picks[:6]:
        conf = pick.get("confidence", 0)
        conf_class = "high" if conf >= 75 else ("medium" if conf >= 60 else "low")
        conf_pct = min(conf, 100)

        home_abbr = pick.get("home_abbr") or pick.get("home_team", "")
        away_abbr = pick.get("away_abbr") or pick.get("away_team", "")
        record_home = pick.get("home_record", "")
        record_away = pick.get("away_record", "")
        label = pick.get("pick_label", "")
        league = pick.get("league", "")

        home_logo = _logo_tag(pick.get("home_logo", ""))
        away_logo = _logo_tag(pick.get("away_logo", ""))

        league_badge = (f'<span class="league-badge">{league}</span>'
                        if league and league != sport_name else "")

        picks_html_parts.append(f"""
        <div class="pick-card">
            <div class="pick-teams">
                <div class="team away-team">
                    {away_logo}
                    <div class="team-info">
                        <span class="team-abbr">{away_abbr}</span>
                        <span class="team-record">{record_away}</span>
                    </div>
                </div>
                <div class="pick-vs">VS</div>
                <div class="team home-team">
                    <div class="team-info text-right">
                        <span class="team-abbr">{home_abbr}</span>
                        <span class="team-record">{record_home}</span>
                    </div>
                    {home_logo}
                </div>
            </div>
            <div class="pick-bottom">
                <div class="pick-label-wrap">
                    {league_badge}
                    <span class="pick-label">{label}</span>
                </div>
                <div class="conf-wrap">
                    <div class="conf-bar-bg">
                        <div class="conf-bar {conf_class}" style="width:{conf_pct}%"></div>
                    </div>
                    <span class="conf-text {conf_class}">{conf}%</span>
                </div>
            </div>
        </div>""")

    picks_html = "\n".join(picks_html_parts)

    stats_html = ""
    if stats and stats.get("total", 0) > 0:
        w = stats["wins"]
        l = stats["losses"]
        pct = stats["win_pct"]
        streak = stats.get("current_streak", "")
        stats_html = f"""
        <div class="stats-row">
            <span class="stat"><span class="stat-val green">{w}W</span><span class="stat-lbl"> ganados</span></span>
            <span class="stat-sep">·</span>
            <span class="stat"><span class="stat-val red">{l}L</span><span class="stat-lbl"> perdidos</span></span>
            <span class="stat-sep">·</span>
            <span class="stat"><span class="stat-val accent">{pct}%</span><span class="stat-lbl"> acierto</span></span>
            <span class="stat-sep">·</span>
            <span class="stat"><span class="stat-val">{streak}</span><span class="stat-lbl"> racha</span></span>
        </div>"""

    css = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width: 1080px;
    min-height: 1350px;
    background: linear-gradient(160deg, #0d1117 0%, #0d1520 60%, #0d1117 100%);
    font-family: 'Inter', -apple-system, sans-serif;
    color: #e6edf3;
    display: flex;
    flex-direction: column;
    padding: 64px 72px 56px;
    position: relative;
    overflow: hidden;
}
body::before {
    content: "";
    position: absolute;
    top: -200px; right: -200px;
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(233,69,96,0.07) 0%, transparent 70%);
    pointer-events: none;
}
body::after {
    content: "";
    position: absolute;
    bottom: -150px; left: -150px;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(100,181,246,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 40px;
}
.header-left { display: flex; align-items: center; gap: 18px; }
.sport-icon { font-size: 3.2rem; line-height: 1; }
.sport-name {
    font-family: 'Oswald', sans-serif;
    font-size: 3rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: 2px;
    text-transform: uppercase;
}
.date-badge {
    font-size: 0.95rem;
    font-weight: 600;
    color: #8b949e;
    letter-spacing: 1.5px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 16px;
}
.divider {
    height: 2px;
    background: linear-gradient(90deg, #e94560 0%, rgba(233,69,96,0.3) 60%, transparent 100%);
    margin-bottom: 36px;
    border-radius: 2px;
}
.picks-list { display: flex; flex-direction: column; gap: 16px; flex: 1; }
.pick-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 18px 22px;
}
.pick-teams {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
}
.team { display: flex; align-items: center; gap: 10px; }
.away-team { flex-direction: row; }
.home-team { flex-direction: row-reverse; }
.team-logo { width: 42px; height: 42px; object-fit: contain; flex-shrink: 0; }
.team-info { display: flex; flex-direction: column; gap: 2px; }
.text-right { text-align: right; }
.team-abbr {
    font-family: 'Oswald', sans-serif;
    font-size: 1.4rem;
    font-weight: 600;
    color: #e6edf3;
    letter-spacing: 0.5px;
}
.team-record { font-size: 0.75rem; color: #8b949e; font-weight: 500; }
.pick-vs {
    font-family: 'Oswald', sans-serif;
    font-size: 0.85rem;
    color: #484f58;
    font-weight: 600;
    letter-spacing: 1px;
}
.pick-bottom { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.pick-label-wrap { display: flex; align-items: center; gap: 8px; }
.league-badge {
    font-size: 0.65rem;
    font-weight: 700;
    color: #8b949e;
    background: #1c2128;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 2px 6px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.pick-label {
    font-family: 'Oswald', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #64b5f6;
    letter-spacing: 1px;
}
.conf-wrap { display: flex; align-items: center; gap: 10px; }
.conf-bar-bg { width: 120px; height: 6px; background: #21262d; border-radius: 3px; overflow: hidden; }
.conf-bar { height: 100%; border-radius: 3px; }
.conf-bar.high { background: linear-gradient(90deg, #388e3c, #4caf50); }
.conf-bar.medium { background: linear-gradient(90deg, #f57c00, #ffb74d); }
.conf-bar.low { background: linear-gradient(90deg, #c62828, #e94560); }
.conf-text { font-size: 0.9rem; font-weight: 700; min-width: 38px; text-align: right; }
.conf-text.high { color: #4caf50; }
.conf-text.medium { color: #ffb74d; }
.conf-text.low { color: #e94560; }
.footer { margin-top: 32px; padding-top: 24px; border-top: 1px solid #21262d; }
.stats-row { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.stat { display: flex; align-items: baseline; gap: 3px; }
.stat-val { font-family: 'Oswald', sans-serif; font-size: 1.1rem; font-weight: 700; color: #e6edf3; }
.stat-val.green { color: #4caf50; }
.stat-val.red { color: #e94560; }
.stat-val.accent { color: #64b5f6; }
.stat-lbl { font-size: 0.8rem; color: #8b949e; }
.stat-sep { color: #30363d; font-size: 1rem; }
.branding { display: flex; align-items: center; justify-content: space-between; }
.brand-url { font-size: 0.85rem; color: #484f58; font-weight: 500; letter-spacing: 0.5px; }
.brand-tag {
    font-family: 'Oswald', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    color: #e94560;
    letter-spacing: 1px;
}
"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <span class="sport-icon">{sport_icon}</span>
            <span class="sport-name">{sport_name}</span>
        </div>
        <span class="date-badge">{today}</span>
    </div>
    <div class="divider"></div>
    <div class="picks-list">
        {picks_html}
    </div>
    <div class="footer">
        {stats_html}
        <div class="branding">
            <span class="brand-url">{site_url}</span>
            <span class="brand-tag">PRONOSTICOS</span>
        </div>
    </div>
</body>
</html>"""


def generate_instagram_images(predictions, tracking_data=None, output_dir=OUTPUT_DIR):
    """Genera un card PNG por deporte/liga. Retorna lista de rutas generadas."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [Instagram] Instala playwright: pip install playwright && playwright install chromium")
        return []

    os.makedirs(output_dir, exist_ok=True)
    stats = (tracking_data or {}).get("stats", {})
    generated = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})

        for sport_key, sport_data in predictions.items():
            picks = sport_data.get("picks", [])
            if not picks:
                continue

            sport_name = sport_data.get("name", sport_key.upper())
            sport_icon = sport_data.get("icon", "")

            by_league = {}
            for pick in picks:
                league = pick.get("league", sport_name)
                by_league.setdefault(league, []).append(pick)

            cards = ([(sport_name, sport_icon, picks)]
                     if len(by_league) == 1
                     else [(lg, sport_icon, lp) for lg, lp in by_league.items() if lp])

            for card_name, icon, card_picks in cards:
                html = _build_card_html(card_name, icon, card_picks, stats)
                page.set_content(html, wait_until="networkidle")
                safe = card_name.lower().replace(" ", "_").replace("/", "-")
                out_path = os.path.join(output_dir, f"{safe}.png")
                page.screenshot(path=out_path, full_page=True)
                generated.append(out_path)
                print(f"  [Instagram] {out_path}")

        browser.close()

    return generated
