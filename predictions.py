"""
Motor de pronosticos deportivos diarios.
Analiza partidos del dia usando datos de ESPN (records, rachas, lesiones, odds)
y genera las mejores apuestas por deporte con score de confianza.
Cuotas de casas de apuestas via The Odds API.
"""

import requests
from datetime import datetime, timezone, timedelta

try:
    import config as _cfg
    ODDS_API_KEY = getattr(_cfg, "ODDS_API_KEY", "")
    ODDS_BOOKMAKERS = getattr(_cfg, "ODDS_BOOKMAKERS", "")
except ImportError:
    ODDS_API_KEY = ""
    ODDS_BOOKMAKERS = ""

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
    "Europa League": {
        "sport_path": "soccer/uefa.europa",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Conference League": {
        "sport_path": "soccer/uefa.europa.conf",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Copa Libertadores": {
        "sport_path": "soccer/conmebol.libertadores",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
    "Copa Sudamericana": {
        "sport_path": "soccer/conmebol.sudamericana",
        "icon": "\u26bd",
        "sport": "futbol",
        "has_odds": False,
        "has_injuries": False,
    },
}

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
TIMEOUT = 15

# Torneos internacionales: buscar datos del equipo en su liga local para tener historial completo
TOURNAMENT_LEAGUES = {
    "Champions League", "Europa League", "Conference League",
    "Copa Libertadores", "Copa Sudamericana",
}

# Mapeo de ligas locales por pais/region para buscar datos reales de equipos en torneos
DOMESTIC_LEAGUE_PATHS = [
    "soccer/esp.1",      # La Liga
    "soccer/eng.1",      # Premier League
    "soccer/ger.1",      # Bundesliga
    "soccer/ita.1",      # Serie A
    "soccer/fra.1",      # Ligue 1
    "soccer/por.1",      # Primeira Liga
    "soccer/ned.1",      # Eredivisie
    "soccer/arg.1",      # Liga Argentina
    "soccer/bra.1",      # Brasileirao
    "soccer/col.1",      # Liga Colombiana
    "soccer/ecu.1",      # Liga Ecuatoriana
    "soccer/chi.1",      # Liga Chilena
    "soccer/par.1",      # Liga Paraguaya
    "soccer/uru.1",      # Liga Uruguaya
    "soccer/bol.1",      # Liga Boliviana
    "soccer/per.1",      # Liga Peruana
    "soccer/ven.1",      # Liga Venezolana
    "soccer/mex.1",      # Liga MX
    "soccer/tur.super_lig",  # Super Lig Turca
    "soccer/gre.1",      # Super Liga Griega
    "soccer/sco.1",      # Scottish Premiership
    "soccer/bel.1",      # Jupiler Pro League
    "soccer/aut.1",      # Bundesliga Austriaca
    "soccer/sui.1",      # Super League Suiza
    "soccer/cze.1",      # Liga Checa
    "soccer/ukr.1",      # Premier League Ucraniana
]


# Cache global de equipos por liga domestica (se llena una vez por ejecucion)
_domestic_teams_cache = {}

# Prioridad de ligas a buscar segun el torneo
TOURNAMENT_DOMESTIC_PRIORITY = {
    "Copa Libertadores": [
        "soccer/arg.1", "soccer/bra.1", "soccer/col.1", "soccer/chi.1",
        "soccer/ecu.1", "soccer/par.1", "soccer/uru.1", "soccer/bol.1",
        "soccer/per.1", "soccer/ven.1", "soccer/mex.1",
    ],
    "Copa Sudamericana": [
        "soccer/arg.1", "soccer/bra.1", "soccer/col.1", "soccer/chi.1",
        "soccer/ecu.1", "soccer/par.1", "soccer/uru.1", "soccer/bol.1",
        "soccer/per.1", "soccer/ven.1", "soccer/mex.1",
    ],
    "Champions League": [
        "soccer/esp.1", "soccer/eng.1", "soccer/ger.1", "soccer/ita.1",
        "soccer/fra.1", "soccer/por.1", "soccer/ned.1", "soccer/tur.super_lig",
        "soccer/sco.1", "soccer/bel.1", "soccer/aut.1", "soccer/sui.1",
        "soccer/cze.1", "soccer/ukr.1", "soccer/gre.1",
    ],
    "Europa League": [
        "soccer/esp.1", "soccer/eng.1", "soccer/ger.1", "soccer/ita.1",
        "soccer/fra.1", "soccer/por.1", "soccer/ned.1", "soccer/tur.super_lig",
        "soccer/sco.1", "soccer/bel.1", "soccer/aut.1", "soccer/sui.1",
        "soccer/cze.1", "soccer/ukr.1", "soccer/gre.1",
    ],
    "Conference League": [
        "soccer/esp.1", "soccer/eng.1", "soccer/ger.1", "soccer/ita.1",
        "soccer/fra.1", "soccer/por.1", "soccer/ned.1", "soccer/tur.super_lig",
        "soccer/sco.1", "soccer/bel.1", "soccer/aut.1", "soccer/sui.1",
        "soccer/cze.1", "soccer/ukr.1", "soccer/gre.1",
    ],
}


def _load_domestic_teams_cache(league_paths=None):
    """Carga y cachea los equipos de las ligas domesticas especificadas."""
    paths_to_load = league_paths or DOMESTIC_LEAGUE_PATHS
    # Solo cargar las que no estan en cache
    new_paths = [p for p in paths_to_load if not any(k.startswith(f"{p}:") for k in _domestic_teams_cache)]

    if not new_paths:
        return

    print(f"    [*] Cargando equipos de {len(new_paths)} ligas locales...")
    loaded = 0
    for league_path in new_paths:
        try:
            url = f"{ESPN_BASE}/{league_path}/teams"
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()

            for group in data.get("sports", [{}]):
                for league in group.get("leagues", [{}]):
                    for team in league.get("teams", []):
                        t = team.get("team", {})
                        t_id = t.get("id", "")
                        t_name = t.get("displayName", "").lower()
                        t_abbr = t.get("abbreviation", "").lower()
                        t_short = t.get("shortDisplayName", "").lower()
                        if t_id and t_name:
                            _domestic_teams_cache[f"{league_path}:{t_id}"] = {
                                "id": t_id,
                                "name": t_name,
                                "abbr": t_abbr,
                                "short": t_short,
                                "league_path": league_path,
                            }
                            loaded += 1
        except Exception:
            continue

    if loaded:
        print(f"    [OK] {loaded} equipos cargados ({len(_domestic_teams_cache)} total)")


def _find_domestic_team_data(team_name, team_abbr, tournament_name=""):
    """
    Busca datos de un equipo en su liga local cuando juega torneo internacional.
    Usa cache y prioriza ligas de la region del torneo.
    """
    # Determinar en que ligas buscar segun el torneo
    priority_paths = TOURNAMENT_DOMESTIC_PRIORITY.get(tournament_name, DOMESTIC_LEAGUE_PATHS)
    _load_domestic_teams_cache(priority_paths)

    team_name_lower = team_name.lower()
    # Para nombres compuestos como "Barcelona SC", usar palabras significativas
    team_words = [w for w in team_name_lower.split() if len(w) > 2 and w not in ("de", "la", "el", "del", "los", "las", "fc", "sc", "cf", "cd")]
    main_word = team_words[-1] if team_words else ""

    best_match = None
    best_score = 0

    # Solo buscar en equipos de las ligas de la region del torneo
    region_teams = {k: v for k, v in _domestic_teams_cache.items()
                    if v["league_path"] in priority_paths}

    for key, t in region_teams.items():
        score = 0

        # Match por nombre exacto (maxima prioridad)
        if team_name_lower == t["name"]:
            score = 15

        # Match por abreviatura exacta
        elif team_abbr.lower() == t["abbr"] and len(team_abbr) >= 2:
            score = 12

        # Match por nombre completo contenido
        elif team_name_lower in t["name"] or t["name"] in team_name_lower:
            # Bonus si el match es mas especifico (mas largo)
            match_len = min(len(team_name_lower), len(t["name"]))
            score = 8 + min(match_len / 10, 3)

        # Match por short name exacto
        elif t["short"] and t["short"] == team_name_lower:
            score = 10

        # Match por short name contenido
        elif t["short"] and len(t["short"]) > 3 and (t["short"] in team_name_lower or team_name_lower in t["short"]):
            score = 7

        # Match por primera palabra significativa (para "Boca Juniors" -> "boca")
        elif team_words and len(team_words[0]) > 3:
            first_word = team_words[0]
            if first_word in t["name"].split() or t["name"].startswith(first_word):
                score = 6

        # Match por palabra principal (ultima)
        elif main_word and len(main_word) > 4 and main_word in t["name"].split():
            score = 5

        if score > best_score:
            best_score = score
            best_match = t

    if best_match and best_score >= 5:
        team_data = fetch_team_data(best_match["league_path"], best_match["id"])
        if team_data and team_data["overall"]["wins"] + team_data["overall"]["losses"] > 3:
            return team_data, best_match["league_path"]

    return None, None


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


def fetch_scoreboard_events(sport_path, date_str=None):
    """Obtiene eventos del dia desde el scoreboard.
    date_str: fecha en formato YYYYMMDD (si no se pasa, usa la fecha de hoy).
    """
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    url = f"{ESPN_BASE}/{sport_path}/scoreboard?dates={date_str}"
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


def fetch_soccer_team_stats(sport_path, team_id):
    """
    Obtiene estadisticas avanzadas de un equipo de futbol:
    - Goles anotados/recibidos (para estimar remates)
    - Tarjetas amarillas/rojas
    - Tiros de esquina estimados
    - Goleadores principales
    """
    url = f"{ESPN_BASE}/{sport_path}/teams/{team_id}/statistics"
    data = _get(url)
    stats = {
        "goals_for": 0,
        "goals_against": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "corners": 0,
        "shots": 0,
        "shots_on_target": 0,
        "games_played": 0,
    }
    if not data:
        return stats

    # Parsear stats del equipo
    categories = data.get("results", data.get("splits", {}).get("categories", []))
    if isinstance(categories, dict):
        categories = categories.get("categories", [])

    for cat in categories:
        cat_stats = {}
        for stat in cat.get("stats", []):
            cat_stats[stat.get("name", "")] = stat.get("value", 0)

        stats["goals_for"] = int(cat_stats.get("totalGoals", cat_stats.get("goalsFor", stats["goals_for"])))
        stats["goals_against"] = int(cat_stats.get("goalsAgainst", cat_stats.get("goalsConceded", stats["goals_against"])))
        stats["yellow_cards"] = int(cat_stats.get("yellowCards", cat_stats.get("foulsCommitted", stats["yellow_cards"])))
        stats["red_cards"] = int(cat_stats.get("redCards", stats["red_cards"]))
        stats["corners"] = int(cat_stats.get("cornerKicks", cat_stats.get("corners", stats["corners"])))
        stats["shots"] = int(cat_stats.get("totalShots", cat_stats.get("shotsTotal", stats["shots"])))
        stats["shots_on_target"] = int(cat_stats.get("shotsOnTarget", cat_stats.get("shotsOnGoal", stats["shots_on_target"])))
        gp = cat_stats.get("gamesPlayed", cat_stats.get("appearances", 0))
        if gp:
            stats["games_played"] = int(gp)

    return stats


def fetch_team_top_scorers(sport_path, team_id):
    """Obtiene los goleadores principales de un equipo."""
    url = f"{ESPN_BASE}/{sport_path}/teams/{team_id}/roster"
    data = _get(url)
    scorers = []
    if not data:
        return scorers

    athletes = data.get("athletes", [])
    for group in athletes:
        for player in group.get("items", []):
            name = player.get("displayName", player.get("fullName", ""))
            position = player.get("position", {}).get("abbreviation", "")
            # Obtener stats del jugador si estan disponibles
            player_stats = player.get("statistics", {})
            goals = 0
            if player_stats:
                for stat_group in player_stats if isinstance(player_stats, list) else [player_stats]:
                    stats_map = {}
                    for s in stat_group.get("stats", []):
                        if isinstance(s, dict):
                            stats_map[s.get("name", "")] = s.get("value", 0)
                    goals = int(stats_map.get("totalGoals", stats_map.get("goals", 0)))
            if goals > 0:
                scorers.append({"name": name, "goals": goals, "position": position})

    scorers.sort(key=lambda x: x["goals"], reverse=True)
    return scorers[:5]


def fetch_probable_lineup(sport_path, team_id):
    """Obtiene la alineacion probable basada en el roster del equipo."""
    url = f"{ESPN_BASE}/{sport_path}/teams/{team_id}/roster"
    data = _get(url)
    lineup = []
    if not data:
        return lineup

    athletes = data.get("athletes", [])
    position_order = {"GK": 1, "G": 1, "D": 2, "DF": 2, "M": 3, "MF": 3, "F": 4, "FW": 4, "ST": 4}

    for group in athletes:
        for player in group.get("items", []):
            status = player.get("status", {})
            status_type = status.get("type", "active")
            # Solo jugadores activos
            if status_type in ("out", "injured", "suspension"):
                continue
            name = player.get("displayName", player.get("fullName", ""))
            pos = player.get("position", {}).get("abbreviation", "")
            pos_name = player.get("position", {}).get("displayName", pos)
            if name and pos:
                lineup.append({
                    "name": name,
                    "position": pos,
                    "position_name": pos_name,
                    "order": position_order.get(pos, 5),
                })

    lineup.sort(key=lambda x: x["order"])
    return lineup[:11]


def generate_soccer_extra_bets(home_stats, away_stats, home_scorers, away_scorers):
    """
    Genera apuestas adicionales para partidos de futbol:
    - Total de tiros de esquina
    - Tarjetas totales
    - Remates al arco
    - Posibles goleadores
    """
    extra_bets = {}

    home_gp = max(home_stats["games_played"], 1)
    away_gp = max(away_stats["games_played"], 1)

    # Esquinas estimadas por partido
    home_corners_avg = home_stats["corners"] / home_gp if home_stats["corners"] > 0 else 4.5
    away_corners_avg = away_stats["corners"] / away_gp if away_stats["corners"] > 0 else 4.0
    total_corners_est = round(home_corners_avg + away_corners_avg, 1)
    if total_corners_est == 0:
        total_corners_est = 9.5  # promedio tipico
    extra_bets["corners"] = {
        "home_avg": round(home_corners_avg, 1),
        "away_avg": round(away_corners_avg, 1),
        "total_estimate": total_corners_est,
        "line": round(total_corners_est - 0.5) + 0.5,
        "pick": "Over" if total_corners_est > 9.5 else "Under",
    }

    # Tarjetas estimadas por partido
    home_cards_avg = home_stats["yellow_cards"] / home_gp if home_stats["yellow_cards"] > 0 else 2.0
    away_cards_avg = away_stats["yellow_cards"] / away_gp if away_stats["yellow_cards"] > 0 else 2.0
    total_cards_est = round(home_cards_avg + away_cards_avg, 1)
    if total_cards_est == 0:
        total_cards_est = 4.5  # promedio tipico
    extra_bets["cards"] = {
        "home_avg": round(home_cards_avg, 1),
        "away_avg": round(away_cards_avg, 1),
        "total_estimate": total_cards_est,
        "line": round(total_cards_est - 0.5) + 0.5,
        "pick": "Over" if total_cards_est > 4.5 else "Under",
    }

    # Remates estimados por partido
    home_shots_avg = home_stats["shots"] / home_gp if home_stats["shots"] > 0 else 12.0
    away_shots_avg = away_stats["shots"] / away_gp if away_stats["shots"] > 0 else 10.0
    total_shots_est = round(home_shots_avg + away_shots_avg, 1)
    home_sot_avg = home_stats["shots_on_target"] / home_gp if home_stats["shots_on_target"] > 0 else 4.5
    away_sot_avg = away_stats["shots_on_target"] / away_gp if away_stats["shots_on_target"] > 0 else 3.5
    total_sot_est = round(home_sot_avg + away_sot_avg, 1)
    extra_bets["shots"] = {
        "home_avg": round(home_shots_avg, 1),
        "away_avg": round(away_shots_avg, 1),
        "total_estimate": total_shots_est,
        "home_on_target_avg": round(home_sot_avg, 1),
        "away_on_target_avg": round(away_sot_avg, 1),
        "total_on_target": total_sot_est,
    }

    # Goles estimados por partido
    home_goals_avg = home_stats["goals_for"] / home_gp if home_stats["goals_for"] > 0 else 1.3
    away_goals_avg = away_stats["goals_for"] / away_gp if away_stats["goals_for"] > 0 else 1.0
    total_goals_est = round(home_goals_avg + away_goals_avg, 1)
    extra_bets["goals"] = {
        "home_avg": round(home_goals_avg, 1),
        "away_avg": round(away_goals_avg, 1),
        "total_estimate": total_goals_est,
        "line": 2.5,
        "pick": "Over" if total_goals_est > 2.5 else "Under",
    }

    # Posibles goleadores
    extra_bets["scorers"] = {
        "home": [{"name": s["name"], "goals": s["goals"], "position": s["position"]} for s in home_scorers[:3]],
        "away": [{"name": s["name"], "goals": s["goals"], "position": s["position"]} for s in away_scorers[:3]],
    }

    return extra_bets


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


# ============================================
# The Odds API - Cuotas de casas de apuestas
# ============================================

ODDS_API_SPORTS = {
    "basketball": "basketball_nba",
    "baseball": "baseball_mlb",
    "hockey": "icehockey_nhl",
    "futbol": None,  # futbol usa multiples keys, se maneja aparte
}

ODDS_API_SOCCER = {
    "La Liga": "soccer_spain_la_liga",
    "Premier League": "soccer_epl",
    "Bundesliga": "soccer_germany_bundesliga",
    "Serie A": "soccer_italy_serie_a",
    "Ligue 1": "soccer_france_ligue_one",
    "Champions League": "soccer_uefa_champs_league",
    "Europa League": "soccer_uefa_europa_league",
    "Conference League": "soccer_uefa_europa_conference_league",
    "Copa Libertadores": "soccer_conmebol_libertadores",
    "Copa Sudamericana": "soccer_conmebol_copa_sudamericana",
}


def fetch_odds_api(sport_key):
    """Obtiene cuotas de The Odds API para un deporte."""
    if not ODDS_API_KEY or not sport_key:
        return {}

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us,eu",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "american",
    }
    if ODDS_BOOKMAKERS:
        params["bookmakers"] = ODDS_BOOKMAKERS

    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 401:
            print("    [!] Odds API: API key invalida")
            return {}
        if resp.status_code == 422:
            return {}
        resp.raise_for_status()

        remaining = resp.headers.get("x-requests-remaining", "?")
        print(f"    [Odds API] {sport_key} OK (requests restantes: {remaining})")

        events = resp.json()
        # Indexar por equipos para hacer match con ESPN
        odds_map = {}
        for ev in events:
            home = ev.get("home_team", "")
            away = ev.get("away_team", "")
            key = f"{home} vs {away}".lower()
            odds_map[key] = _parse_odds_event(ev)
            # Tambien indexar por nombres parciales para matching flexible
            home_short = home.split()[-1].lower() if home else ""
            away_short = away.split()[-1].lower() if away else ""
            if home_short and away_short:
                odds_map[f"{home_short}_{away_short}"] = odds_map[key]
        return odds_map
    except Exception as e:
        print(f"    [!] Odds API error: {e}")
        return {}


def _parse_odds_event(event):
    """Parsea un evento de The Odds API a formato de cuotas."""
    bookmakers = event.get("bookmakers", [])
    result = {
        "spread": "",
        "over_under": "",
        "home_ml": "",
        "away_ml": "",
        "provider": "",
        "all_bookmakers": [],
    }

    if not bookmakers:
        return result

    for bm in bookmakers:
        bm_name = bm.get("title", bm.get("key", ""))
        bm_odds = {"name": bm_name, "h2h_home": "", "h2h_away": "", "spread": "", "total": ""}

        for market in bm.get("markets", []):
            mk = market.get("key", "")
            outcomes = market.get("outcomes", [])

            if mk == "h2h":
                for o in outcomes:
                    if o.get("name") == event.get("home_team"):
                        bm_odds["h2h_home"] = str(o.get("price", ""))
                    elif o.get("name") == event.get("away_team"):
                        bm_odds["h2h_away"] = str(o.get("price", ""))
            elif mk == "spreads":
                for o in outcomes:
                    if o.get("name") == event.get("home_team"):
                        point = o.get("point", "")
                        bm_odds["spread"] = f"{'+' if point > 0 else ''}{point}" if point else ""
            elif mk == "totals":
                for o in outcomes:
                    if o.get("name") == "Over":
                        bm_odds["total"] = str(o.get("point", ""))

        result["all_bookmakers"].append(bm_odds)

    # Usar el primer bookmaker como principal
    first = result["all_bookmakers"][0] if result["all_bookmakers"] else {}
    result["provider"] = first.get("name", "")
    result["home_ml"] = first.get("h2h_home", "")
    result["away_ml"] = first.get("h2h_away", "")
    result["spread"] = first.get("spread", "")
    result["over_under"] = first.get("total", "")

    return result


def match_odds_to_game(odds_map, home_name, away_name):
    """Busca las cuotas que coincidan con un partido."""
    if not odds_map:
        return None

    # Intento exacto
    key = f"{home_name} vs {away_name}".lower()
    if key in odds_map:
        return odds_map[key]

    # Intento por apellido del equipo
    home_short = home_name.split()[-1].lower()
    away_short = away_name.split()[-1].lower()
    short_key = f"{home_short}_{away_short}"
    if short_key in odds_map:
        return odds_map[short_key]

    # Intento por coincidencia parcial
    for k, v in odds_map.items():
        if home_short in k and away_short in k:
            return v

    return None


def fetch_predictions_for_league(league_name, league_info):
    """Obtiene pronosticos para una liga."""
    print(f"  [*] Analizando {league_name}...")

    sport_path = league_info["sport_path"]
    is_soccer = league_info["sport"] == "futbol"
    has_odds = league_info["has_odds"]
    has_injuries = league_info["has_injuries"]

    # Usar fecha de hoy (UTC) y tambien manana para cubrir partidos nocturnos
    # que en UTC caen en el dia siguiente pero son "de hoy" en hora local (Americas)
    today_utc = datetime.now(timezone.utc)
    today_str = today_utc.strftime("%Y%m%d")
    tomorrow_utc = today_utc + timedelta(days=1)
    tomorrow_str = tomorrow_utc.strftime("%Y%m%d")

    # Ventana de "hoy": desde las 08:00 UTC de hoy hasta las 08:00 UTC de manana
    # Esto cubre partidos de ~04:00 (Americas) hasta ~04:00 del dia siguiente
    window_start = today_utc.replace(hour=8, minute=0, second=0, microsecond=0)
    window_end = window_start + timedelta(hours=24)

    # Obtener eventos de hoy y manana (para capturar partidos nocturnos Americas)
    events = fetch_scoreboard_events(sport_path, today_str)
    events_tomorrow = fetch_scoreboard_events(sport_path, tomorrow_str)
    # Combinar sin duplicados (por id)
    seen_ids = {e.get("id") for e in events}
    for e in events_tomorrow:
        if e.get("id") not in seen_ids:
            events.append(e)

    predictions = []

    # Obtener cuotas de The Odds API si hay key configurada
    ext_odds_map = {}
    if ODDS_API_KEY:
        sport = league_info["sport"]
        if is_soccer:
            odds_sport_key = ODDS_API_SOCCER.get(league_name)
        else:
            odds_sport_key = ODDS_API_SPORTS.get(sport)
        if odds_sport_key:
            ext_odds_map = fetch_odds_api(odds_sport_key)

    # Filtrar solo partidos programados (pre) dentro de la ventana de hoy
    scheduled_events = []
    for event in events:
        state = event.get("status", {}).get("type", {}).get("state", "")
        if state != "pre":
            continue
        # Verificar que el evento este dentro de la ventana de hoy
        event_date_str = event.get("date", "")
        if event_date_str:
            try:
                event_dt = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
                if event_dt < window_start or event_dt >= window_end:
                    continue
            except Exception:
                pass
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

        # Para torneos internacionales, si los datos del torneo son insuficientes
        # (pocos partidos jugados), buscar datos en la liga local del equipo
        if league_name in TOURNAMENT_LEAGUES:
            home_total_games = home_data["overall"]["wins"] + home_data["overall"]["losses"] + home_data["overall"].get("ties", 0)
            away_total_games = away_data["overall"]["wins"] + away_data["overall"]["losses"] + away_data["overall"].get("ties", 0)

            if home_total_games < 4:
                domestic_data, domestic_path = _find_domestic_team_data(home_team_name, home_data.get("abbreviation", ""), league_name)
                if domestic_data:
                    # Preservar logo y nombre del torneo, usar stats de liga local
                    orig_logo = home_data["logo"]
                    orig_name = home_data["name"]
                    orig_abbr = home_data["abbreviation"]
                    home_data = domestic_data
                    home_data["logo"] = orig_logo or domestic_data["logo"]
                    home_data["name"] = orig_name
                    home_data["abbreviation"] = orig_abbr
                    print(f"    [+] {home_team_name}: usando datos de liga local ({domestic_path})")

            if away_total_games < 4:
                domestic_data, domestic_path = _find_domestic_team_data(away_team_name, away_data.get("abbreviation", ""), league_name)
                if domestic_data:
                    orig_logo = away_data["logo"]
                    orig_name = away_data["name"]
                    orig_abbr = away_data["abbreviation"]
                    away_data = domestic_data
                    away_data["logo"] = orig_logo or domestic_data["logo"]
                    away_data["name"] = orig_name
                    away_data["abbreviation"] = orig_abbr
                    print(f"    [+] {away_team_name}: usando datos de liga local ({domestic_path})")

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

        # Odds - primero intentar The Odds API, luego ESPN como fallback
        odds = None
        ext_odds = match_odds_to_game(ext_odds_map, home_team_name, away_team_name)
        if ext_odds and (ext_odds.get("home_ml") or ext_odds.get("spread")):
            odds = ext_odds
        elif has_odds:
            odds = extract_odds_from_event(event)

        # Calcular confianza
        confidence, pick_team_name, pick_label, factors = calculate_confidence(
            home_data, away_data, home_injuries, away_injuries, odds, is_soccer
        )

        # Apuestas adicionales para futbol (esquinas, tarjetas, remates, goleadores, alineaciones)
        extra_bets = None
        home_lineup = []
        away_lineup = []
        if is_soccer:
            try:
                home_stats = fetch_soccer_team_stats(sport_path, home_id)
                away_stats = fetch_soccer_team_stats(sport_path, away_id)
                home_scorers = fetch_team_top_scorers(sport_path, home_id)
                away_scorers = fetch_team_top_scorers(sport_path, away_id)
                home_lineup = fetch_probable_lineup(sport_path, home_id)
                away_lineup = fetch_probable_lineup(sport_path, away_id)
                extra_bets = generate_soccer_extra_bets(home_stats, away_stats, home_scorers, away_scorers)
            except Exception as e:
                print(f"    [!] Error obteniendo stats extra: {e}")

        # Fecha/hora del partido
        date_str = event.get("date", "")
        match_time = ""
        match_date = ""
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                match_time = dt.strftime("%H:%M")
                match_date = dt.strftime("%d/%m/%Y")
            except Exception:
                match_time = ""
                match_date = ""

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
            "match_date": match_date,
            "league": league_name,
            "extra_bets": extra_bets,
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
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
        # Filtrar por threshold
        data["picks"] = [p for p in data["picks"] if p["confidence"] >= confidence_threshold]
        # Futbol tiene mas ligas (10+), permitir mas picks; otros deportes limitar a min_picks
        max_picks = min_picks * 4 if sport == "futbol" else min_picks
        data["picks"] = data["picks"][:max_picks]
        total_picks += len(data["picks"])
        if data["picks"]:
            print(f"\n  [{data['name']}] {len(data['picks'])} picks seleccionados")

    print(f"\n[OK] Total: {total_picks} pronosticos generados")

    # Guardar picks en historial de tracking
    try:
        from tracker import save_picks
        save_picks(all_predictions)
    except Exception as e:
        print(f"  [!] Error guardando picks en tracker: {e}")

    # Agregar Guia MLB detallada
    try:
        from mlb_guide import generate_mlb_guide
        mlb_guide = generate_mlb_guide()
        if mlb_guide:
            all_predictions["baseball"]["mlb_guide"] = mlb_guide
    except Exception as e:
        print(f"  [!] Error generando Guia MLB: {e}")

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
