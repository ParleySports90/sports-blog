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


def _build_pick_del_dia_html(pick, sport_name, sport_icon,
                             site_url="parleysports90.github.io/sports-blog"):
    """Genera HTML del card especial Pick del Dia (foco en un solo partido)."""
    today = datetime.now().strftime("%d %b %Y").upper()

    conf = pick.get("confidence", 0)
    conf_class = "high" if conf >= 75 else ("medium" if conf >= 60 else "low")
    conf_pct = min(conf, 100)
    conf_label = "FIJO 🔥" if conf >= 75 else ("SÓLIDO ✅" if conf >= 62 else "BAJO ⚠️")

    home_abbr = pick.get("home_abbr") or pick.get("home_team", "LOCAL")
    away_abbr = pick.get("away_abbr") or pick.get("away_team", "VISITA")
    home_record = pick.get("home_record", "")
    away_record = pick.get("away_record", "")
    home_logo = _logo_tag(pick.get("home_logo", ""), "logo-big")
    away_logo = _logo_tag(pick.get("away_logo", ""), "logo-big")
    label = pick.get("pick_label", "")
    league = pick.get("league", sport_name)

    factors = pick.get("factors", [])
    factors_html = "".join(f"<li>{f}</li>" for f in factors[:3])

    css = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width:1080px; min-height:1350px;
    background: linear-gradient(150deg, #0a0e17 0%, #0d1520 50%, #0a0e17 100%);
    font-family:'Inter',-apple-system,sans-serif;
    color:#e6edf3;
    display:flex; flex-direction:column;
    padding:60px 72px 56px;
    position:relative; overflow:hidden;
}
body::before {
    content:""; position:absolute; top:-120px; right:-120px;
    width:700px; height:700px;
    background:radial-gradient(circle,rgba(233,69,96,0.09) 0%,transparent 65%);
    pointer-events:none;
}
body::after {
    content:""; position:absolute; bottom:-100px; left:-100px;
    width:550px; height:550px;
    background:radial-gradient(circle,rgba(100,181,246,0.07) 0%,transparent 65%);
    pointer-events:none;
}
.banner {
    background:linear-gradient(90deg,#e94560,#c62845);
    border-radius:10px; padding:12px 28px;
    font-family:'Oswald',sans-serif; font-size:1.5rem;
    font-weight:700; letter-spacing:3px; text-align:center;
    color:#fff; margin-bottom:32px;
    text-shadow:0 2px 8px rgba(0,0,0,0.4);
}
.header {
    display:flex; align-items:center; justify-content:space-between;
    margin-bottom:10px;
}
.sport-wrap { display:flex; align-items:center; gap:14px; }
.sport-icon { font-size:2.8rem; }
.sport-name {
    font-family:'Oswald',sans-serif; font-size:2rem;
    font-weight:700; color:#fff; letter-spacing:2px;
    text-transform:uppercase;
}
.date-badge {
    font-size:0.85rem; font-weight:600; color:#8b949e;
    letter-spacing:1.5px; background:#161b22;
    border:1px solid #30363d; border-radius:8px; padding:8px 16px;
}
.league-tag {
    font-size:0.75rem; font-weight:700; color:#64b5f6;
    letter-spacing:1px; text-transform:uppercase;
    background:rgba(100,181,246,0.1); border:1px solid rgba(100,181,246,0.2);
    border-radius:6px; padding:4px 12px; margin-bottom:28px;
    display:inline-block;
}
.divider {
    height:2px;
    background:linear-gradient(90deg,#e94560 0%,rgba(233,69,96,0.2) 70%,transparent 100%);
    margin:16px 0 36px; border-radius:2px;
}
.matchup {
    display:grid; grid-template-columns:1fr auto 1fr;
    align-items:center; gap:20px; margin-bottom:40px;
}
.team { display:flex; flex-direction:column; align-items:center; gap:12px; }
.logo-big { width:90px; height:90px; object-fit:contain; }
.team-abbr {
    font-family:'Oswald',sans-serif; font-size:2.4rem;
    font-weight:700; color:#fff; letter-spacing:1px;
}
.team-record { font-size:0.9rem; color:#8b949e; }
.vs-block { text-align:center; }
.vs-text {
    font-family:'Oswald',sans-serif; font-size:1.1rem;
    color:#484f58; font-weight:600; letter-spacing:2px;
}
.pick-block {
    background:#161b22; border:1px solid #30363d;
    border-radius:16px; padding:28px 32px; margin-bottom:28px;
    text-align:center;
}
.pick-title {
    font-size:0.8rem; font-weight:600; color:#8b949e;
    letter-spacing:2px; text-transform:uppercase; margin-bottom:10px;
}
.pick-label {
    font-family:'Oswald',sans-serif; font-size:3rem;
    font-weight:700; color:#64b5f6; letter-spacing:2px;
    line-height:1.1;
}
.conf-section { margin-top:20px; }
.conf-row { display:flex; align-items:center; justify-content:center; gap:16px; }
.conf-bar-bg { flex:1; max-width:280px; height:10px; background:#21262d; border-radius:5px; overflow:hidden; }
.conf-bar { height:100%; border-radius:5px; }
.conf-bar.high { background:linear-gradient(90deg,#388e3c,#4caf50); }
.conf-bar.medium { background:linear-gradient(90deg,#f57c00,#ffb74d); }
.conf-bar.low { background:linear-gradient(90deg,#c62828,#e94560); }
.conf-pct {
    font-family:'Oswald',sans-serif; font-size:1.8rem;
    font-weight:700; min-width:72px;
}
.conf-pct.high { color:#4caf50; }
.conf-pct.medium { color:#ffb74d; }
.conf-pct.low { color:#e94560; }
.conf-label { font-size:0.95rem; font-weight:600; color:#8b949e; min-width:90px; text-align:left; }
.factors {
    list-style:none; background:#0d1117;
    border:1px solid #21262d; border-radius:12px;
    padding:16px 20px; margin-bottom:auto; flex:1;
}
.factors li {
    font-size:0.82rem; color:#8b949e; padding:5px 0;
    border-bottom:1px solid #161b22; display:flex; align-items:flex-start; gap:8px;
}
.factors li:last-child { border-bottom:none; }
.factors li::before { content:"▸"; color:#e94560; flex-shrink:0; }
.footer {
    margin-top:28px; padding-top:20px;
    border-top:1px solid #21262d;
    display:flex; align-items:center; justify-content:space-between;
}
.brand-url { font-size:0.8rem; color:#484f58; }
.brand-tag {
    font-family:'Oswald',sans-serif; font-size:1rem;
    font-weight:700; color:#e94560; letter-spacing:1.5px;
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
    <div class="banner">⭐ PICK DEL DÍA</div>
    <div class="header">
        <div class="sport-wrap">
            <span class="sport-icon">{sport_icon}</span>
            <span class="sport-name">{sport_name}</span>
        </div>
        <span class="date-badge">{today}</span>
    </div>
    <span class="league-tag">{league}</span>
    <div class="divider"></div>
    <div class="matchup">
        <div class="team">
            {away_logo}
            <span class="team-abbr">{away_abbr}</span>
            <span class="team-record">{away_record}</span>
        </div>
        <div class="vs-block">
            <div class="vs-text">VS</div>
        </div>
        <div class="team">
            {home_logo}
            <span class="team-abbr">{home_abbr}</span>
            <span class="team-record">{home_record}</span>
        </div>
    </div>
    <div class="pick-block">
        <div class="pick-title">NUESTRA JUGADA</div>
        <div class="pick-label">{label}</div>
        <div class="conf-section">
            <div class="conf-row">
                <div class="conf-bar-bg">
                    <div class="conf-bar {conf_class}" style="width:{conf_pct}%"></div>
                </div>
                <span class="conf-pct {conf_class}">{conf}%</span>
                <span class="conf-label">{conf_label}</span>
            </div>
        </div>
    </div>
    {"<ul class='factors'>" + factors_html + "</ul>" if factors_html else ""}
    <div class="footer">
        <span class="brand-url">{site_url}</span>
        <span class="brand-tag">@PARLEYSPORTS90</span>
    </div>
</body>
</html>"""


def generate_pick_del_dia_card(predictions, output_dir=OUTPUT_DIR):
    """Genera la imagen Pick del Dia. Retorna la ruta del archivo o None."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [Instagram] Instala playwright: pip install playwright && playwright install chromium")
        return None

    # Encontrar el pick con mayor confianza
    best_pick = None
    best_conf = 0
    best_sport_key = ""
    best_sport_data = {}
    for sport_key, sport_data in predictions.items():
        for pick in sport_data.get("picks", []):
            conf = pick.get("confidence", 0)
            if conf > best_conf:
                best_conf = conf
                best_pick = pick
                best_sport_key = sport_key
                best_sport_data = sport_data

    if not best_pick:
        print("  [Instagram] Sin picks para generar Pick del Dia.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    sport_name = best_sport_data.get("name", best_sport_key.upper())
    sport_icon = best_sport_data.get("icon", "🎯")
    html = _build_pick_del_dia_html(best_pick, sport_name, sport_icon)
    out_path = os.path.join(output_dir, "pick_del_dia.png")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=out_path, full_page=True)
        browser.close()

    print(f"  [Instagram] Pick del Día: {out_path}")
    return out_path


def _build_stats_card_html(stats, site_url="parleysports90.github.io/sports-blog"):
    today = datetime.now().strftime("%d %b %Y").upper()
    w = stats.get("wins", 0)
    l = stats.get("losses", 0)
    total = stats.get("total", 0)
    pct = stats.get("win_pct", 0)
    streak = stats.get("current_streak", "—")
    pct_bar = min(pct, 100)
    pct_class = "high" if pct >= 60 else ("medium" if pct >= 50 else "low")

    recent = stats.get("recent_picks", [])
    recent_html = ""
    for p in recent[:5]:
        result = p.get("result", "pending")
        icon = "✅" if result == "win" else ("❌" if result == "loss" else "⏳")
        label = p.get("pick_label", "")
        sport = p.get("sport", "")
        recent_html += f'<div class="pick-row"><span class="pick-icon">{icon}</span><span class="pick-info">{sport} — {label}</span></div>'

    css = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width:1080px; min-height:1350px;
    background:linear-gradient(150deg,#0a0e17 0%,#0d1520 50%,#0a0e17 100%);
    font-family:'Inter',-apple-system,sans-serif;
    color:#e6edf3; display:flex; flex-direction:column;
    padding:60px 72px 56px; position:relative; overflow:hidden;
}
body::before {
    content:""; position:absolute; top:-120px; right:-120px;
    width:700px; height:700px;
    background:radial-gradient(circle,rgba(100,181,246,0.08) 0%,transparent 65%);
    pointer-events:none;
}
.banner {
    background:linear-gradient(90deg,#1565c0,#0d47a1);
    border-radius:10px; padding:12px 28px;
    font-family:'Oswald',sans-serif; font-size:1.4rem;
    font-weight:700; letter-spacing:3px; text-align:center;
    color:#fff; margin-bottom:32px;
}
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:32px; }
.title { font-family:'Oswald',sans-serif; font-size:2.2rem; font-weight:700; color:#fff; letter-spacing:2px; }
.date-badge { font-size:0.85rem; color:#8b949e; background:#161b22; border:1px solid #30363d; border-radius:8px; padding:8px 16px; }
.divider { height:2px; background:linear-gradient(90deg,#64b5f6 0%,rgba(100,181,246,0.2) 70%,transparent 100%); margin-bottom:36px; border-radius:2px; }
.stats-grid { display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-bottom:32px; }
.stat-box { background:#161b22; border:1px solid #30363d; border-radius:14px; padding:24px; text-align:center; }
.stat-num { font-family:'Oswald',sans-serif; font-size:3.5rem; font-weight:700; line-height:1; }
.stat-num.green { color:#4caf50; }
.stat-num.red { color:#e94560; }
.stat-num.blue { color:#64b5f6; }
.stat-lbl { font-size:0.85rem; color:#8b949e; margin-top:6px; text-transform:uppercase; letter-spacing:1px; }
.pct-box { background:#161b22; border:1px solid #30363d; border-radius:14px; padding:24px; margin-bottom:24px; }
.pct-title { font-size:0.85rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:14px; }
.pct-row { display:flex; align-items:center; gap:16px; }
.pct-bar-bg { flex:1; height:14px; background:#21262d; border-radius:7px; overflow:hidden; }
.pct-bar { height:100%; border-radius:7px; }
.pct-bar.high { background:linear-gradient(90deg,#388e3c,#4caf50); }
.pct-bar.medium { background:linear-gradient(90deg,#f57c00,#ffb74d); }
.pct-bar.low { background:linear-gradient(90deg,#c62828,#e94560); }
.pct-num { font-family:'Oswald',sans-serif; font-size:2rem; font-weight:700; min-width:72px; text-align:right; }
.pct-num.high { color:#4caf50; }
.pct-num.medium { color:#ffb74d; }
.pct-num.low { color:#e94560; }
.recent-box { background:#161b22; border:1px solid #30363d; border-radius:14px; padding:20px; flex:1; margin-bottom:24px; }
.recent-title { font-size:0.8rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px; }
.pick-row { display:flex; align-items:center; gap:10px; padding:7px 0; border-bottom:1px solid #21262d; }
.pick-row:last-child { border-bottom:none; }
.pick-icon { font-size:1rem; }
.pick-info { font-size:0.82rem; color:#8b949e; }
.streak-box { background:#161b22; border:1px solid #30363d; border-radius:14px; padding:18px 24px; margin-bottom:24px; display:flex; align-items:center; justify-content:space-between; }
.streak-label { font-size:0.85rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px; }
.streak-val { font-family:'Oswald',sans-serif; font-size:1.8rem; font-weight:700; color:#ffb74d; }
.footer { margin-top:auto; padding-top:20px; border-top:1px solid #21262d; display:flex; justify-content:space-between; align-items:center; }
.brand-url { font-size:0.8rem; color:#484f58; }
.brand-tag { font-family:'Oswald',sans-serif; font-size:1rem; font-weight:700; color:#64b5f6; letter-spacing:1.5px; }
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
    <div class="banner">📊 ESTADÍSTICAS DE ACIERTOS</div>
    <div class="header">
        <span class="title">PARLEYSPORTS90</span>
        <span class="date-badge">{today}</span>
    </div>
    <div class="divider"></div>
    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-num green">{w}</div>
            <div class="stat-lbl">Ganados ✅</div>
        </div>
        <div class="stat-box">
            <div class="stat-num red">{l}</div>
            <div class="stat-lbl">Perdidos ❌</div>
        </div>
        <div class="stat-box" style="grid-column:1/-1">
            <div class="stat-num blue">{total}</div>
            <div class="stat-lbl">Total de picks analizados</div>
        </div>
    </div>
    <div class="pct-box">
        <div class="pct-title">Porcentaje de acierto</div>
        <div class="pct-row">
            <div class="pct-bar-bg"><div class="pct-bar {pct_class}" style="width:{pct_bar}%"></div></div>
            <span class="pct-num {pct_class}">{pct}%</span>
        </div>
    </div>
    <div class="streak-box">
        <span class="streak-label">🔥 Racha actual</span>
        <span class="streak-val">{streak}</span>
    </div>
    {"<div class='recent-box'><div class='recent-title'>Últimos picks</div>" + recent_html + "</div>" if recent_html else ""}
    <div class="footer">
        <span class="brand-url">{site_url}</span>
        <span class="brand-tag">@PARLEYSPORTS90</span>
    </div>
</body>
</html>"""


def _build_results_card_html(results, stats, site_url="parleysports90.github.io/sports-blog"):
    if not results:
        return None
    date_str = results[0].get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        display_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %b %Y").upper()
    except ValueError:
        display_date = date_str.upper()

    day_wins = sum(1 for r in results if r["status"] == "won")
    day_losses = sum(1 for r in results if r["status"] == "lost")

    rows_html = ""
    for r in results:
        icon = "✅" if r["status"] == "won" else "❌"
        row_class = "won" if r["status"] == "won" else "lost"
        label = r.get("pick_label", "")
        home_abbr = r.get("home_abbr") or r.get("home_team", "")[:3].upper()
        away_abbr = r.get("away_abbr") or r.get("away_team", "")[:3].upper()
        hs = r.get("home_score")
        as_ = r.get("away_score")
        score_str = f"{away_abbr} {as_} – {hs} {home_abbr}" if hs is not None else f"{away_abbr} vs {home_abbr}"
        conf = r.get("confidence", 0)
        rows_html += f"""
        <div class="result-row {row_class}">
            <span class="res-icon">{icon}</span>
            <div class="res-info">
                <span class="res-label">{label}</span>
                <span class="res-score">{score_str}</span>
            </div>
            <span class="res-conf">{conf}%</span>
        </div>"""

    total = stats.get("total", 0)
    w = stats.get("wins", 0)
    l = stats.get("losses", 0)
    pct = stats.get("win_pct", 0)
    streak = stats.get("current_streak", "—")
    day_class = "high" if day_wins > day_losses else ("low" if day_losses > day_wins else "medium")

    css = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width:1080px; min-height:1350px;
    background:linear-gradient(150deg,#0a0e17 0%,#0d1520 50%,#0a0e17 100%);
    font-family:'Inter',-apple-system,sans-serif;
    color:#e6edf3; display:flex; flex-direction:column;
    padding:56px 72px 52px; position:relative; overflow:hidden;
}
body::before {
    content:""; position:absolute; top:-100px; right:-100px;
    width:600px; height:600px;
    background:radial-gradient(circle,rgba(233,69,96,0.07) 0%,transparent 65%);
    pointer-events:none;
}
.banner {
    border-radius:10px; padding:12px 28px;
    font-family:'Oswald',sans-serif; font-size:1.4rem;
    font-weight:700; letter-spacing:3px; text-align:center;
    color:#fff; margin-bottom:28px;
    background:linear-gradient(90deg,#1b5e20,#388e3c);
}
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:28px; }
.title { font-family:'Oswald',sans-serif; font-size:1.8rem; font-weight:700; color:#fff; letter-spacing:2px; }
.date-badge { font-size:0.85rem; color:#8b949e; background:#161b22; border:1px solid #30363d; border-radius:8px; padding:8px 16px; }
.divider { height:2px; background:linear-gradient(90deg,#4caf50 0%,rgba(76,175,80,0.2) 70%,transparent 100%); margin-bottom:28px; border-radius:2px; }
.results-list { display:flex; flex-direction:column; gap:12px; flex:1; margin-bottom:28px; }
.result-row {
    display:flex; align-items:center; gap:14px;
    background:#161b22; border:1px solid #30363d;
    border-radius:12px; padding:16px 20px;
}
.result-row.won { border-left:4px solid #4caf50; }
.result-row.lost { border-left:4px solid #e94560; }
.res-icon { font-size:1.4rem; flex-shrink:0; }
.res-info { flex:1; display:flex; flex-direction:column; gap:3px; }
.res-label { font-family:'Oswald',sans-serif; font-size:1.3rem; font-weight:600; color:#e6edf3; letter-spacing:0.5px; }
.res-score { font-size:0.78rem; color:#8b949e; }
.res-conf { font-size:0.85rem; font-weight:700; color:#8b949e; flex-shrink:0; }
.summary-box {
    background:#161b22; border:1px solid #30363d;
    border-radius:14px; padding:20px 24px; margin-bottom:20px;
}
.day-record { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.day-label { font-size:0.8rem; color:#8b949e; text-transform:uppercase; letter-spacing:1px; }
.day-val { font-family:'Oswald',sans-serif; font-size:1.6rem; font-weight:700; }
.day-val.high { color:#4caf50; }
.day-val.medium { color:#ffb74d; }
.day-val.low { color:#e94560; }
.acc-row { display:flex; gap:20px; font-size:0.85rem; color:#8b949e; flex-wrap:wrap; }
.acc-item { display:flex; gap:6px; align-items:center; }
.acc-val { font-family:'Oswald',sans-serif; font-size:1rem; font-weight:700; color:#64b5f6; }
.footer { padding-top:18px; border-top:1px solid #21262d; display:flex; justify-content:space-between; align-items:center; }
.brand-url { font-size:0.8rem; color:#484f58; }
.brand-tag { font-family:'Oswald',sans-serif; font-size:1rem; font-weight:700; color:#e94560; letter-spacing:1.5px; }
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
    <div class="banner">📊 RESULTADOS DEL DÍA</div>
    <div class="header">
        <span class="title">PARLEYSPORTS90</span>
        <span class="date-badge">{display_date}</span>
    </div>
    <div class="divider"></div>
    <div class="results-list">{rows_html}</div>
    <div class="summary-box">
        <div class="day-record">
            <span class="day-label">Resultado del día</span>
            <span class="day-val {day_class}">{day_wins}W — {day_losses}L</span>
        </div>
        <div class="acc-row">
            <div class="acc-item">Acumulado: <span class="acc-val">{w}W-{l}L</span></div>
            <div class="acc-item">Acierto: <span class="acc-val">{pct}%</span></div>
            <div class="acc-item">Racha: <span class="acc-val">{streak}</span></div>
        </div>
    </div>
    <div class="footer">
        <span class="brand-url">{site_url}</span>
        <span class="brand-tag">@PARLEYSPORTS90</span>
    </div>
</body>
</html>"""


def _build_poll_card_html(game, site_url="parleysports90.github.io/sports-blog"):
    sport_icon = game.get("sport_icon", "⚽")
    sport_name = game.get("sport_name", "Deportes")
    league = game.get("league", sport_name)
    home_team = game.get("home_team", "Local")
    away_team = game.get("away_team", "Visita")
    home_abbr = game.get("home_abbr") or home_team[:3].upper()
    away_abbr = game.get("away_abbr") or away_team[:3].upper()
    home_logo = _logo_tag(game.get("home_logo", ""), "poll-logo")
    away_logo = _logo_tag(game.get("away_logo", ""), "poll-logo")
    today = datetime.now().strftime("%d %b %Y").upper()

    css = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    width:1080px; min-height:1350px;
    background:linear-gradient(150deg,#0a0e17 0%,#0d1520 50%,#0a0e17 100%);
    font-family:'Inter',-apple-system,sans-serif;
    color:#e6edf3; display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    padding:56px 72px; position:relative; overflow:hidden;
    text-align:center;
}
body::before {
    content:""; position:absolute; top:-150px; left:50%; transform:translateX(-50%);
    width:800px; height:800px;
    background:radial-gradient(circle,rgba(233,69,96,0.08) 0%,transparent 65%);
    pointer-events:none;
}
.question {
    font-family:'Oswald',sans-serif; font-size:2.4rem;
    font-weight:700; color:#fff; letter-spacing:3px;
    text-transform:uppercase; margin-bottom:8px;
}
.question-sub { font-size:1rem; color:#8b949e; margin-bottom:40px; letter-spacing:1px; }
.league-badge {
    display:inline-block; font-size:0.8rem; font-weight:700;
    color:#64b5f6; letter-spacing:1px; text-transform:uppercase;
    background:rgba(100,181,246,0.1); border:1px solid rgba(100,181,246,0.25);
    border-radius:6px; padding:5px 14px; margin-bottom:48px;
}
.matchup {
    display:grid; grid-template-columns:1fr auto 1fr;
    align-items:center; gap:24px; width:100%; margin-bottom:48px;
}
.team-side { display:flex; flex-direction:column; align-items:center; gap:14px; }
.poll-logo { width:110px; height:110px; object-fit:contain; }
.team-name {
    font-family:'Oswald',sans-serif; font-size:2rem;
    font-weight:700; color:#fff; letter-spacing:1px;
}
.vs-circle {
    width:72px; height:72px; border-radius:50%;
    background:#161b22; border:2px solid #30363d;
    display:flex; align-items:center; justify-content:center;
    font-family:'Oswald',sans-serif; font-size:1.1rem;
    color:#484f58; font-weight:700; letter-spacing:1px;
}
.divider { width:100%; height:1px; background:#21262d; margin-bottom:40px; }
.vote-section { width:100%; display:flex; flex-direction:column; gap:16px; margin-bottom:40px; }
.vote-btn {
    width:100%; padding:22px 32px; border-radius:14px;
    display:flex; align-items:center; gap:20px;
    font-family:'Oswald',sans-serif; font-size:1.8rem;
    font-weight:700; letter-spacing:1px;
}
.vote-a {
    background:linear-gradient(90deg,rgba(33,106,243,0.25),rgba(33,106,243,0.1));
    border:2px solid rgba(33,106,243,0.5);
    color:#64b5f6;
}
.vote-b {
    background:linear-gradient(90deg,rgba(233,69,96,0.25),rgba(233,69,96,0.1));
    border:2px solid rgba(233,69,96,0.5);
    color:#e94560;
}
.vote-letter {
    width:52px; height:52px; border-radius:10px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.6rem; flex-shrink:0;
}
.vote-a .vote-letter { background:rgba(33,106,243,0.3); }
.vote-b .vote-letter { background:rgba(233,69,96,0.3); }
.vote-team { flex:1; text-align:left; }
.cta {
    font-size:1.1rem; color:#8b949e; letter-spacing:1px;
    margin-bottom:32px;
}
.cta strong { color:#ffb74d; }
.footer { display:flex; justify-content:space-between; align-items:center; width:100%; }
.brand-url { font-size:0.8rem; color:#484f58; }
.brand-tag { font-family:'Oswald',sans-serif; font-size:1rem; font-weight:700; color:#e94560; letter-spacing:1.5px; }
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
    <div class="question">{sport_icon} ¿Quién gana hoy?</div>
    <div class="question-sub">{today}</div>
    <span class="league-badge">{league}</span>
    <div class="matchup">
        <div class="team-side">
            {away_logo}
            <span class="team-name">{away_abbr}</span>
        </div>
        <div class="vs-circle">VS</div>
        <div class="team-side">
            {home_logo}
            <span class="team-name">{home_abbr}</span>
        </div>
    </div>
    <div class="divider"></div>
    <div class="vote-section">
        <div class="vote-btn vote-a">
            <div class="vote-letter">A</div>
            <span class="vote-team">{away_team}</span>
        </div>
        <div class="vote-btn vote-b">
            <div class="vote-letter">B</div>
            <span class="vote-team">{home_team}</span>
        </div>
    </div>
    <div class="cta">Comenta <strong>A</strong> o <strong>B</strong> 👇 ¿Con quién vas?</div>
    <div class="footer">
        <span class="brand-url">{site_url}</span>
        <span class="brand-tag">@PARLEYSPORTS90</span>
    </div>
</body>
</html>"""


def generate_poll_card(game, output_dir=OUTPUT_DIR):
    """Genera card de encuesta para el partido mas importante del dia."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    os.makedirs(output_dir, exist_ok=True)
    html = _build_poll_card_html(game)
    out_path = os.path.join(output_dir, "poll.png")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=out_path, full_page=True)
        browser.close()

    print(f"  [Instagram] Poll card: {out_path}")
    return out_path


def generate_results_card(results, stats, output_dir=OUTPUT_DIR):
    """Genera card PNG con resultados del dia anterior. Retorna ruta o None."""
    if not results:
        print("  [Instagram] Sin resultados nuevos para generar card.")
        return None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    html = _build_results_card_html(results, stats)
    if not html:
        return None

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "resultados.png")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=out_path, full_page=True)
        browser.close()

    print(f"  [Instagram] Resultados card: {out_path}")
    return out_path


def generate_stats_card(tracking_data, output_dir=OUTPUT_DIR):
    """Genera card PNG de estadisticas de aciertos. Retorna ruta o None."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    stats = (tracking_data or {}).get("stats", {})
    if not stats or stats.get("total", 0) == 0:
        print("  [Instagram] Sin estadisticas para generar card.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    html = _build_stats_card_html(stats)
    out_path = os.path.join(output_dir, "stats_card.png")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.set_content(html, wait_until="networkidle")
        page.screenshot(path=out_path, full_page=True)
        browser.close()

    print(f"  [Instagram] Stats card: {out_path}")
    return out_path


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
