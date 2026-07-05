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
