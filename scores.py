"""
Modulo para obtener resultados deportivos de las principales ligas.
Usa las APIs publicas de ESPN.
"""

import requests
from datetime import datetime, timezone

# Endpoints de ESPN por liga
LEAGUES = {
    # Futbol - Europa
    "La Liga": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Espana",
    },
    "Premier League": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Inglaterra",
    },
    "Bundesliga": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Alemania",
    },
    "Serie A": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Italia",
    },
    "Ligue 1": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Francia",
    },
    "Primeira Liga": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/por.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Portugal",
    },
    "Eredivisie": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/ned.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Holanda",
    },
    # Futbol - Sudamerica
    "Liga Argentina": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/arg.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Argentina",
    },
    "Brasileirao": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Brasil",
    },
    # Competiciones internacionales
    "Champions League": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Europa",
    },
    "Europa League": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.europa/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Europa",
    },
    "Copa Libertadores": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/conmebol.libertadores/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Sudamerica",
    },
    "Copa Sudamericana": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/conmebol.sudamericana/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Sudamerica",
    },
    "Conference League": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.europa.conf/scoreboard",
        "sport": "futbol",
        "icon": "\u26bd",
        "country": "Europa",
    },
    # USA Sports
    "NBA": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "sport": "basketball",
        "icon": "\ud83c\udfc0",
        "country": "USA",
    },
    "MLB": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard",
        "sport": "baseball",
        "icon": "\u26be",
        "country": "USA",
    },
    "NHL": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
        "sport": "hockey",
        "icon": "\ud83c\udfd2",
        "country": "USA",
    },
    "NFL": {
        "url": "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard",
        "sport": "football",
        "icon": "\ud83c\udfc8",
        "country": "USA",
    },
}


def fetch_league_scores(league_name, league_info):
    """Obtiene resultados de una liga desde ESPN API."""
    matches = []
    try:
        resp = requests.get(league_info["url"], timeout=15)
        resp.raise_for_status()
        data = resp.json()

        events = data.get("events", [])
        for event in events:
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])

            if len(competitors) < 2:
                continue

            # Determinar home y away
            home = away = None
            for comp in competitors:
                if comp.get("homeAway") == "home":
                    home = comp
                elif comp.get("homeAway") == "away":
                    away = comp

            if not home or not away:
                home, away = competitors[0], competitors[1]

            home_team = home.get("team", {}).get("shortDisplayName", home.get("team", {}).get("displayName", "?"))
            away_team = away.get("team", {}).get("shortDisplayName", away.get("team", {}).get("displayName", "?"))
            home_score = home.get("score", "-")
            away_score = away.get("score", "-")
            home_logo = home.get("team", {}).get("logo", "")
            away_logo = away.get("team", {}).get("logo", "")

            # Estado del partido
            status_obj = event.get("status", {})
            status_type = status_obj.get("type", {})
            state = status_type.get("state", "pre")  # pre, in, post
            short_detail = status_type.get("shortDetail", "")
            display_clock = status_obj.get("displayClock", "")
            period = status_obj.get("period", 0)

            if state == "pre":
                match_state = "scheduled"
                display_status = short_detail
                game_detail = ""
            elif state == "in":
                match_state = "live"
                display_status = short_detail
                # Detalle especifico por deporte
                sport = league_info["sport"]
                if sport == "baseball":
                    # MLB: "Top 5th", "Bot 3rd", "Mid 7th"
                    game_detail = short_detail
                elif sport == "futbol":
                    # Futbol: minuto del partido
                    game_detail = short_detail
                elif sport == "basketball":
                    # NBA: "Q3 5:30"
                    game_detail = short_detail
                elif sport == "hockey":
                    # NHL: "0:57 - 2nd"
                    game_detail = short_detail
                else:
                    game_detail = short_detail
            else:
                match_state = "finished"
                detail_lower = short_detail.lower()
                if "extra" in detail_lower or "ot" in detail_lower or "so" in detail_lower:
                    display_status = short_detail
                else:
                    display_status = "Final"
                game_detail = ""

            # Fecha del partido (hora Venezuela UTC-4)
            date_str = event.get("date", "")
            match_date = ""
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    from datetime import timedelta
                    dt_vzla = dt - timedelta(hours=4)
                    match_date = dt_vzla.strftime("%d/%m %I:%M %p")
                    # Limpiar leading zero
                    if match_date.split()[-2].startswith("0"):
                        parts = match_date.split()
                        parts[-2] = parts[-2][1:]
                        match_date = " ".join(parts)
                except Exception:
                    match_date = date_str[:10]

            matches.append({
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score,
                "home_logo": home_logo,
                "away_logo": away_logo,
                "status": display_status,
                "state": match_state,
                "date": match_date,
                "game_detail": game_detail if state == "in" else "",
            })

        print(f"  [OK] {league_name}: {len(matches)} partidos")
    except Exception as e:
        print(f"  [ERROR] {league_name}: {e}")

    return matches


def fetch_all_scores():
    """Obtiene resultados de todas las ligas."""
    print("[*] Obteniendo resultados deportivos...\n")
    all_scores = {}

    for league_name, league_info in LEAGUES.items():
        matches = fetch_league_scores(league_name, league_info)
        all_scores[league_name] = {
            "matches": matches,
            "icon": league_info["icon"],
            "sport": league_info["sport"],
            "country": league_info["country"],
        }

    total = sum(len(v["matches"]) for v in all_scores.values())
    active = sum(1 for v in all_scores.values() if v["matches"])
    print(f"\n[OK] Total: {total} partidos de {active} ligas con actividad.")
    return all_scores
