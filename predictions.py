"""
Motor de pronosticos deportivos diarios.
Analiza partidos del dia usando datos de ESPN (records, rachas, lesiones, odds)
y genera las mejores apuestas por deporte con score de confianza.
"""

import requests
from datetime import datetime

# Ligas que soportan pronosticos
PREDICTION_LEAGUES = {
    "NBA": {
        "sport_path": "basketball/nba",
        "icon": "\U0001f3c0",
        "sport": "basketball",
        "has_odds": True,
        "has_injuries": True,
    },
    "MLB": {
        "sport_path": "baseball/mlb",
        "icon": "\u26be",
        "sport": "baseball",
        "has_odds": True,
        "has_injuries": True,
    },
    "NHL": {
        "sport_path": "hockey/nhl",
        "icon": "\U0001f3d2",
        "sport": "hockey",
        "has_odds": True,
        "has_injuries": True,
    },
    # Futbol - sin odds ni lesiones via API
    "La Liga": {
        "sport_path": "soccer/esp.1",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Premier League": {
        "sport_path": "soccer/eng.1",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Bundesliga": {
        "sport_path": "soccer/ger.1",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Serie A": {
        "sport_path": "soccer/ita.1",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Ligue 1": {
        "sport_path": "soccer/fra.1",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Champions League": {
        "sport_path": "soccer/uefa.champions",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
TIMEOUT = 15


def _get(url):
    """GET request con manejo de errores."""
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_team_data(sport_path, team_id):
    """Obtiene datos de un equipo: record, racha, record casa/visita."""
    url = f"{ESPN_BASE}/{sport_path}/teams/{team_id}"
    data = _get(url)
    if not data:
        return None

    team = data.get("team", {})
    record_items = team.get("record", {}).get("items", [])

    overall = {"wins": 0, "losses": 0, "ties": 0, "pct": 0.0}
    home_record = {"wins": 0, "losses": 0}
    away_record = {"wins": 0, "losses": 0}
    streak = ""

    for item in record_items:
        item_type = item.get("type", "")
        stats = {s["name"]: s["value"] for s in item.get("stats", []) if "name" in s}

        if item_type == "total":
            overall["wins"] = int(stats.get("wins", 0))
            overall["losses"] = int(stats.get("losses", 0))
            overall["ties"] = int(stats.get("ties", stats.get("otLosses", 0)))
            gp = overall["wins"] + overall["losses"] + overall["ties"]
            overall["pct"] = overall["wins"] / gp if gp > 0 else 0
            streak = item.get("summary", "")
        elif item_type == "home":
            h_stats = {s["name"]: s["value"] for s in item.get("stats", []) if "name" in s}
            home_record["wins"] = int(h_stats.get("wins", 0))
            home_record["losses"] = int(h_stats.get("losses", 0))
        elif item_type == "road" or item_type == "away":
            a_stats = {s["name"]: s["value"] for s in item.get("stats", []) if "name" in s}
            away_record["wins"] = int(a_stats.get("wins", 0))
            away_record["losses"] = int(a_stats.get("losses", 0))

    # Si no se obtuvo record home/away de los items, intentar del summary
    if home_record["wins"] == 0 and home_record["losses"] == 0:
        for item in record_items:
            summary = item.get("description", "")
            if "Home" in summary or "home" in summary:
                home_record = _parse_record_summary(item.get("summary", ""))
            elif "Away" in summary or "Road" in summary or "road" in summary:
                away_record = _parse_record_summary(item.get("summary", ""))

    # Racha - extraer del streak stat si no vino en summary
    if not streak:
        for item in record_items:
            if item.get("type") == "total":
                stats = {s["name"]: s["value"] for s in item.get("stats", []) if "name" in s}
                s_type = stats.get("streakType", "")
                s_len = int(stats.get("streak", 0))
                if s_type and s_len:
                    streak = f"{'W' if s_type == 'win' else 'L'}{s_len}"

    return {
        "name": team.get("displayName", ""),
        "abbreviation": team.get("abbreviation", ""),
        "logo": team.get("logos", [{}])[0].get("href", "") if team.get("logos") else "",
        "overall": overall,
        "home_record": home_record,
        "away_record": away_record,
        "streak": streak,
    }


def _parse_record_summary(summary):
    """Parsea un summary tipo '30-10' a dict."""
    parts = summary.split("-")
    if len(parts) >= 2:
        try:
            return {"wins": int(parts[0]), "losses": int(parts[1])}
        except ValueError:
            pass
    return {"wins": 0, "losses": 0}


def fetch_team_injuries(sport_path, team_id):
    """Obtiene jugadores lesionados de un equipo."""
    url = f"{ESPN_BASE}/{sport_path}/teams/{team_id}/roster"
    data = _get(url)
    if not data:
        return []

    injuries = []
    athletes = data.get("athletes", [])
    for group in athletes:
        for player in group.get("items", []):
            status = player.get("status", {})
            status_type = status.get("type", "")
            if status_type in ("day-to-day", "out", "injured", "suspension"):
                injuries.append({
                    "name": player.get("displayName", player.get("fullName", "?")),
                    "status": status.get("abbreviation", status_type.upper()),
                    "position": player.get("position", {}).get("abbreviation", ""),
                })
    return injuries


def extract_odds_from_event(event):
    """Extrae odds/lineas de un evento del scoreboard."""
    competition = event.get("competitions", [{}])[0]
    odds_list = competition.get("odds", [])

    if not odds_list:
        return None

    odds = odds_list[0]  # Primer proveedor (usualmente DraftKings)
    result = {
        "spread": "",
        "over_under": "",
        "home_ml": "",
        "away_ml": "",
        "provider": odds.get("provider", {}).get("name", ""),
        "favorite_team_id": "",
    }

    # Spread
    result["spread"] = odds.get("spread", odds.get("details", ""))
    result["over_under"] = str(odds.get("overUnder", ""))

    # Moneylines de homeTeamOdds/awayTeamOdds
    home_odds = odds.get("homeTeamOdds", {})
    away_odds = odds.get("awayTeamOdds", {})
    result["home_ml"] = str(home_odds.get("moneyLine", home_odds.get("odds", "")))
    result["away_ml"] = str(away_odds.get("moneyLine", away_odds.get("odds", "")))
    result["favorite_team_id"] = str(odds.get("favoriteTeamId", ""))

    return result


def fetch_scoreboard_events(sport_path):
    """Obtiene eventos del dia desde el scoreboard."""
    url = f"{ESPN_BASE}/{sport_path}/scoreboard"
    data = _get(url)
    if not data:
        return []
    return data.get("events", [])


def parse_streak_number(streak_str):
    """Extrae numero de racha. 'W5' -> 5, 'L3' -> -3."""
    if not streak_str:
        return 0
    streak_str = streak_str.strip().upper()
    for s in streak_str.split(","):
        s = s.strip()
        if s.startswith("W"):
            try:
                return int(s[1:])
            except ValueError:
                return 0
        elif s.startswith("L"):
            try:
                return -int(s[1:])
            except ValueError:
                return 0
    return 0


def calculate_confidence(home_data, away_data, home_injuries, away_injuries, odds, is_soccer=False):
    """
    Calcula score de confianza (0-100) para un partido.
    Retorna (score, pick_team, pick_label, factors).
    """
    factors = []

    # === 1. Diferencia de records (25%) ===
    home_pct = home_data["overall"]["pct"]
    away_pct = away_data["overall"]["pct"]
    record_diff = home_pct - away_pct  # positivo = home mejor
    record_score = min(abs(record_diff) * 100, 25)  # max 25 pts

    home_w = home_data["overall"]["wins"]
    home_l = home_data["overall"]["losses"]
    away_w = away_data["overall"]["wins"]
    away_l = away_data["overall"]["losses"]
    factors.append(f"{home_data['abbreviation']} {home_w}-{home_l} ({home_pct:.3f}) vs {away_data['abbreviation']} {away_w}-{away_l} ({away_pct:.3f})")

    # === 2. Ventaja casa/visita (20%) ===
    home_hw = home_data["home_record"]["wins"]
    home_hl = home_data["home_record"]["losses"]
    home_home_gp = home_hw + home_hl
    home_home_pct = home_hw / home_home_gp if home_home_gp > 0 else 0.5

    away_aw = away_data["away_record"]["wins"]
    away_al = away_data["away_record"]["losses"]
    away_away_gp = away_aw + away_al
    away_away_pct = away_aw / away_away_gp if away_away_gp > 0 else 0.5

    venue_diff = home_home_pct - away_away_pct
    venue_score = min(abs(venue_diff) * 50, 20)  # max 20 pts

    factors.append(f"{home_data['abbreviation']} {home_hw}-{home_hl} en casa - {away_data['abbreviation']} {away_aw}-{away_al} de visita")

    # === 3. Racha reciente (20%) ===
    home_streak = parse_streak_number(home_data["streak"])
    away_streak = parse_streak_number(away_data["streak"])
    streak_diff = home_streak - away_streak
    streak_score = min(abs(streak_diff) * 3, 20)  # max 20 pts

    home_streak_str = home_data["streak"] if home_data["streak"] else "N/A"
    away_streak_str = away_data["streak"] if away_data["streak"] else "N/A"
    factors.append(f"{home_data['abbreviation']} racha {home_streak_str} - {away_data['abbreviation']} racha {away_streak_str}")

    # === 4. Impacto de lesiones (15%) ===
    injury_score = 0
    if not is_soccer:
        home_inj_count = len(home_injuries)
        away_inj_count = len(away_injuries)
        injury_diff = away_inj_count - home_inj_count  # positivo = away mas lesionados = ventaja home
        injury_score = min(abs(injury_diff) * 3, 15)  # max 15 pts

        home_inj_str = ", ".join([f"{i['name']} ({i['status']})" for i in home_injuries[:3]]) if home_injuries else "sin lesiones importantes"
        away_inj_str = ", ".join([f"{i['name']} ({i['status']})" for i in away_injuries[:3]]) if away_injuries else "sin lesiones importantes"
        factors.append(f"{home_data['abbreviation']}: {home_inj_str} | {away_data['abbreviation']}: {away_inj_str}")
    else:
        # Sin datos de lesiones para futbol, redistribuir peso
        record_score = min(abs(record_diff) * 120, 30)
        venue_score = min(abs(venue_diff) * 60, 25)
        streak_score = min(abs(streak_diff) * 4, 25)

    # === 5. Valor en linea de apuestas (20%) ===
    odds_score = 0
    if odds and not is_soccer:
        # Si hay spread, evaluar si la diferencia de rendimiento justifica la linea
        try:
            spread_val = float(odds.get("spread", "0").replace("+", ""))
        except (ValueError, AttributeError):
            spread_val = 0

        if spread_val != 0:
            # Un spread alto con buena diferencia de records = alta confianza
            expected_margin = record_diff * 15  # estimado
            if (record_diff > 0 and spread_val < 0) or (record_diff < 0 and spread_val > 0):
                # La linea concuerda con los records
                odds_score = min(abs(spread_val) * 1.5, 20)
            else:
                odds_score = 5  # Hay valor contrario

        ou = odds.get("over_under", "")
        spread_display = odds.get("spread", "N/A")
        home_ml = odds.get("home_ml", "")
        away_ml = odds.get("away_ml", "")
        factors.append(f"Linea: {spread_display} | O/U: {ou} | ML: {home_ml}/{away_ml}")
    elif not is_soccer:
        factors.append("Lineas no disponibles")
    else:
        # Futbol sin odds, redistribuir
        record_score = min(abs(record_diff) * 140, 35)
        venue_score = min(abs(venue_diff) * 70, 30)

    # Sumar todo
    raw_total = record_score + venue_score + streak_score + injury_score + odds_score

    # Determinar pick (quien favorece el analisis)
    home_advantage = 0
    if record_diff > 0:
        home_advantage += 1
    elif record_diff < 0:
        home_advantage -= 1
    if venue_diff > 0:
        home_advantage += 1
    elif venue_diff < 0:
        home_advantage -= 1
    if streak_diff > 0:
        home_advantage += 1
    elif streak_diff < 0:
        home_advantage -= 1
    if not is_soccer:
        if (away_inj_count - home_inj_count) > 0:
            home_advantage += 1
        elif (away_inj_count - home_inj_count) < 0:
            home_advantage -= 1

    pick_home = home_advantage >= 0
    pick_team = home_data if pick_home else away_data

    # Construir pick label
    if odds and odds.get("spread") and not is_soccer:
        spread = odds["spread"]
        pick_label = f"{pick_team['abbreviation']} {spread}"
    else:
        pick_label = f"{pick_team['abbreviation']} ML"

    # Normalizar confianza a 50-95 rango
    confidence = max(50, min(95, int(50 + raw_total)))

    return confidence, pick_team["name"], pick_label, factors


def generate_analysis_text(pick_label, confidence, factors, home_name, away_name):
    """Genera texto de analisis legible para un pronostico."""
    lines = []
    for f in factors:
        if "racha" in f.lower() or "record" in f.lower() or "vs" in f.lower():
            lines.append(f"  {f}")
        elif "casa" in f.lower() or "visita" in f.lower():
            lines.append(f"  {f}")
        elif "lesion" in f.lower() or "sin lesiones" in f.lower() or "Day-To-Day" in f or "Out" in f or "DTD" in f or "O" in f:
            lines.append(f"  {f}")
        elif "linea" in f.lower() or "ML:" in f:
            lines.append(f"  {f}")
        else:
            lines.append(f"  {f}")
    return lines


def fetch_predictions_for_league(league_name, league_info):
    """Obtiene pronosticos para una liga."""
    print(f"  [*] Analizando {league_name}...")

    sport_path = league_info["sport_path"]
    is_soccer = league_info["sport"] == "futbol"
    has_odds = league_info["has_odds"]
    has_injuries = league_info["has_injuries"]

    events = fetch_scoreboard_events(sport_path)
    predictions = []

    # Filtrar solo partidos programados (pre) - no analizar los ya jugados
    scheduled_events = []
    for event in events:
        state = event.get("status", {}).get("type", {}).get("state", "")
        if state == "pre":
            scheduled_events.append(event)

    if not scheduled_events:
        print(f"    Sin partidos programados para hoy")
        return []

    for event in scheduled_events:
        competition = event.get("competitions", [{}])[0]
        competitors = competition.get("competitors", [])

        if len(competitors) < 2:
            continue

        home_comp = away_comp = None
        for comp in competitors:
            if comp.get("homeAway") == "home":
                home_comp = comp
            elif comp.get("homeAway") == "away":
                away_comp = comp
        if not home_comp or not away_comp:
            home_comp, away_comp = competitors[0], competitors[1]

        home_id = home_comp.get("team", {}).get("id", "")
        away_id = away_comp.get("team", {}).get("id", "")
        home_team_name = home_comp.get("team", {}).get("displayName", "?")
        away_team_name = away_comp.get("team", {}).get("displayName", "?")
        home_logo = home_comp.get("team", {}).get("logo", "")
        away_logo = away_comp.get("team", {}).get("logo", "")

        if not home_id or not away_id:
            continue

        # Obtener datos detallados de cada equipo
        home_data = fetch_team_data(sport_path, home_id)
        away_data = fetch_team_data(sport_path, away_id)

        if not home_data or not away_data:
            continue

        # Usar logos del scoreboard si no vienen del team endpoint
        if not home_data["logo"] and home_logo:
            home_data["logo"] = home_logo
        if not away_data["logo"] and away_logo:
            away_data["logo"] = away_logo

        # Lesiones
        home_injuries = []
        away_injuries = []
        if has_injuries:
            home_injuries = fetch_team_injuries(sport_path, home_id)
            away_injuries = fetch_team_injuries(sport_path, away_id)

        # Odds
        odds = None
        if has_odds:
            odds = extract_odds_from_event(event)

        # Calcular confianza
        confidence, pick_team_name, pick_label, factors = calculate_confidence(
            home_data, away_data, home_injuries, away_injuries, odds, is_soccer
        )

        # Fecha/hora del partido
        date_str = event.get("date", "")
        match_time = ""
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                match_time = dt.strftime("%H:%M")
            except Exception:
                match_time = ""

        prediction = {
            "home_team": home_data["name"],
            "away_team": away_data["name"],
            "home_abbr": home_data["abbreviation"],
            "away_abbr": away_data["abbreviation"],
            "home_logo": home_data["logo"],
            "away_logo": away_data["logo"],
            "home_record": f"{home_data['overall']['wins']}-{home_data['overall']['losses']}",
            "away_record": f"{away_data['overall']['wins']}-{away_data['overall']['losses']}",
            "pick_label": pick_label,
            "pick_team": pick_team_name,
            "confidence": confidence,
            "factors": factors,
            "odds": odds,
            "home_injuries": home_injuries[:5],
            "away_injuries": away_injuries[:5],
            "match_time": match_time,
            "league": league_name,
        }

        predictions.append(prediction)
        print(f"    {home_team_name} vs {away_team_name} -> {pick_label} ({confidence}%)")

    return predictions


def fetch_all_predictions(min_picks=3, confidence_threshold=55):
    """
    Obtiene pronosticos de todas las ligas.
    Retorna dict agrupado por deporte con top picks.
    """
    print("[*] Generando pronosticos deportivos...\n")

    all_predictions = {
        "basketball": {"name": "NBA", "icon": "\U0001f3c0", "picks": []},
        "baseball": {"name": "MLB", "icon": "\u26be", "picks": []},
        "hockey": {"name": "NHL", "icon": "\U0001f3d2", "picks": []},
        "futbol": {"name": "Futbol", "icon": "\u26bd", "picks": []},
    }

    for league_name, league_info in PREDICTION_LEAGUES.items():
        predictions = fetch_predictions_for_league(league_name, league_info)
        sport = league_info["sport"]

        if sport in all_predictions:
            all_predictions[sport]["picks"].extend(predictions)

    # Ordenar por confianza y seleccionar top picks
    total_picks = 0
    for sport, data in all_predictions.items():
        # Ordenar por confianza descendente
        data["picks"].sort(key=lambda x: x["confidence"], reverse=True)
        # Filtrar por threshold y limitar
        data["picks"] = [p for p in data["picks"] if p["confidence"] >= confidence_threshold]
        # Top N picks
        data["picks"] = data["picks"][:min_picks]
        total_picks += len(data["picks"])
        if data["picks"]:
            print(f"\n  [{data['name']}] {len(data['picks'])} picks seleccionados")

    print(f"\n[OK] Total: {total_picks} pronosticos generados")
    return all_predictions


def print_predictions(predictions):
    """Imprime pronosticos en consola con formato legible."""
    for sport, data in predictions.items():
        if not data["picks"]:
            continue

        name = data["name"]
        print(f"\n{'='*60}")
        print(f"[{name}] TOP PICKS DEL DIA")
        print(f"{'='*60}")

        for i, pick in enumerate(data["picks"], 1):
            print(f"\n{i}. {pick['pick_label']}  ({pick['home_team']} vs {pick['away_team']})  [Confianza: {pick['confidence']}%]")
            for factor in pick["factors"]:
                print(f"   {factor}")
            print()
