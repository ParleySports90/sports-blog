"""
Motor de tracking de aciertos para pronosticos deportivos.
Guarda picks, verifica resultados via ESPN, y calcula estadisticas.
"""

import json
import os
import re
import requests
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PICKS_FILE = os.path.join(DATA_DIR, "picks_history.json")
ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"
TIMEOUT = 15

# Mapeo de ligas a sport_path de ESPN para consultar scoreboards
LEAGUE_SPORT_PATH = {
    "NBA": "basketball/nba",
    "MLB": "baseball/mlb",
    "NHL": "hockey/nhl",
    "La Liga": "soccer/esp.1",
    "Premier League": "soccer/eng.1",
    "Bundesliga": "soccer/ger.1",
    "Serie A": "soccer/ita.1",
    "Ligue 1": "soccer/fra.1",
    "Champions League": "soccer/uefa.champions",
    "Europa League": "soccer/uefa.europa",
    "Conference League": "soccer/uefa.europa.conf",
    "Copa Libertadores": "soccer/conmebol.libertadores",
    "Copa Sudamericana": "soccer/conmebol.sudamericana",
}

# Mapeo de sport_key a sport para stats
LEAGUE_SPORT = {
    "NBA": "basketball",
    "MLB": "baseball",
    "NHL": "hockey",
    "La Liga": "futbol",
    "Premier League": "futbol",
    "Bundesliga": "futbol",
    "Serie A": "futbol",
    "Ligue 1": "futbol",
    "Champions League": "futbol",
    "Europa League": "futbol",
    "Conference League": "futbol",
    "Copa Libertadores": "futbol",
    "Copa Sudamericana": "futbol",
}


def _load_data():
    """Carga el archivo de historial de picks."""
    if not os.path.exists(PICKS_FILE):
        return _empty_data()
    try:
        with open(PICKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _empty_data()


def _save_data(data):
    """Guarda el archivo de historial de picks."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PICKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _empty_data():
    """Retorna estructura de datos vacia."""
    return {
        "picks": [],
        "stats": {
            "total": 0, "wins": 0, "losses": 0, "pending": 0,
            "win_pct": 0.0, "current_streak": "W0",
            "by_sport": {
                "basketball": {"w": 0, "l": 0},
                "baseball": {"w": 0, "l": 0},
                "hockey": {"w": 0, "l": 0},
                "futbol": {"w": 0, "l": 0},
            }
        }
    }


def _make_pick_id(date_str, league, home_team, away_team):
    """Genera un ID unico para un pick."""
    home_short = home_team.split()[-1] if home_team else "UNK"
    away_short = away_team.split()[-1] if away_team else "UNK"
    return f"{date_str}_{league}_{home_short}_vs_{away_short}"


def save_picks(predictions):
    """
    Guarda los picks generados como 'pending' en el historial.
    predictions: dict con formato {sport_key: {name, icon, picks: [...]}}
    Solo agrega picks que no existan ya (por ID).
    """
    data = _load_data()
    existing_ids = {p["id"] for p in data["picks"]}
    today = datetime.now().strftime("%Y-%m-%d")
    added = 0

    for sport_key, sport_data in predictions.items():
        for pick in sport_data.get("picks", []):
            pick_id = _make_pick_id(
                today,
                pick.get("league", sport_data.get("name", "")),
                pick.get("home_team", ""),
                pick.get("away_team", ""),
            )

            if pick_id in existing_ids:
                continue

            entry = {
                "id": pick_id,
                "date": today,
                "league": pick.get("league", sport_data.get("name", "")),
                "sport": sport_key,
                "home_team": pick.get("home_team", ""),
                "away_team": pick.get("away_team", ""),
                "home_abbr": pick.get("home_abbr", ""),
                "away_abbr": pick.get("away_abbr", ""),
                "pick_label": pick.get("pick_label", ""),
                "pick_team": pick.get("pick_team", ""),
                "confidence": pick.get("confidence", 0),
                "status": "pending",
                "home_score": None,
                "away_score": None,
            }
            data["picks"].append(entry)
            existing_ids.add(pick_id)
            added += 1

    _recalculate_stats(data)
    _save_data(data)

    if added:
        print(f"  [Tracker] {added} picks guardados como pending")
    return added


def check_results():
    """
    Verifica resultados de picks pendientes consultando ESPN.
    Marca picks como 'won' o 'lost' segun el score final.
    """
    data = _load_data()
    pending = [p for p in data["picks"] if p["status"] == "pending"]

    if not pending:
        print("  [Tracker] No hay picks pendientes por verificar")
        return 0

    # Agrupar pending por liga para minimizar requests
    by_league = {}
    for pick in pending:
        league = pick["league"]
        if league not in by_league:
            by_league[league] = []
        by_league[league].append(pick)

    resolved = 0
    for league, picks in by_league.items():
        sport_path = LEAGUE_SPORT_PATH.get(league)
        if not sport_path:
            continue

        # Obtener scoreboard de la liga
        scoreboard = _fetch_scoreboard(sport_path)
        if not scoreboard:
            continue

        for pick in picks:
            result = _match_and_resolve(pick, scoreboard)
            if result:
                resolved += 1

    _recalculate_stats(data)
    _save_data(data)

    if resolved:
        print(f"  [Tracker] {resolved} picks resueltos")
    return resolved


def _fetch_scoreboard(sport_path):
    """Obtiene scoreboard de ESPN para una liga."""
    url = f"{ESPN_BASE}/{sport_path}/scoreboard"
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("events", [])
    except Exception:
        return []


def _match_and_resolve(pick, events):
    """
    Busca el partido del pick en los eventos y resuelve si termino.
    Retorna True si se resolvio el pick.
    """
    home_team = pick["home_team"].lower()
    away_team = pick["away_team"].lower()
    home_abbr = pick.get("home_abbr", "").lower()
    away_abbr = pick.get("away_abbr", "").lower()

    for event in events:
        state = event.get("status", {}).get("type", {}).get("state", "")
        if state != "post":  # Solo partidos terminados
            continue

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
            continue

        ev_home = home_comp.get("team", {}).get("displayName", "").lower()
        ev_away = away_comp.get("team", {}).get("displayName", "").lower()
        ev_home_abbr = home_comp.get("team", {}).get("abbreviation", "").lower()
        ev_away_abbr = away_comp.get("team", {}).get("abbreviation", "").lower()

        # Matching: por nombre completo o abreviatura
        home_match = (home_team == ev_home or home_abbr == ev_home_abbr
                      or home_team in ev_home or ev_home in home_team)
        away_match = (away_team == ev_away or away_abbr == ev_away_abbr
                      or away_team in ev_away or ev_away in away_team)

        if not (home_match and away_match):
            continue

        # Partido encontrado y terminado - obtener scores
        try:
            home_score = int(home_comp.get("score", 0))
            away_score = int(away_comp.get("score", 0))
        except (ValueError, TypeError):
            continue

        pick["home_score"] = home_score
        pick["away_score"] = away_score

        # Determinar W/L
        pick["status"] = _determine_result(pick, home_score, away_score)
        return True

    return False


def _determine_result(pick, home_score, away_score):
    """
    Determina si un pick fue won o lost.
    - ML pick (ej "LAL ML"): pick_team score > oponente
    - Spread pick (ej "LAL -5.5"): margen cubre el spread
    """
    pick_label = pick.get("pick_label", "")
    pick_team = pick.get("pick_team", "")
    home_team = pick.get("home_team", "")

    # Determinar si el pick es por el home o away
    pick_is_home = pick_team.lower() == home_team.lower()
    pick_score = home_score if pick_is_home else away_score
    opp_score = away_score if pick_is_home else home_score
    margin = pick_score - opp_score  # positivo = pick team gano por esa cantidad

    # Extraer spread del label si existe
    spread = _extract_spread(pick_label)

    if spread is not None:
        # Spread pick: margen + spread > 0 significa que cubre
        # Ej: pick "LAL -5.5", LAL gana por 7 -> margin=7, spread=-5.5 -> 7+(-5.5)=1.5 > 0 -> won
        # Ej: pick "GSW +3.5", GSW pierde por 2 -> margin=-2, spread=+3.5 -> -2+3.5=1.5 > 0 -> won
        adjusted = margin + spread
        if adjusted > 0:
            return "won"
        elif adjusted < 0:
            return "lost"
        else:
            return "push"  # empate exacto en spread (raro con .5)
    else:
        # ML pick: simplemente gano o no
        if margin > 0:
            return "won"
        elif margin < 0:
            return "lost"
        else:
            return "push"


def _extract_spread(pick_label):
    """
    Extrae el spread numerico de un pick label.
    "LAL -5.5" -> -5.5
    "GSW +3.5" -> +3.5
    "LAL ML" -> None
    """
    if "ML" in pick_label.upper():
        return None

    match = re.search(r'([+-]?\d+\.?\d*)', pick_label)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def _recalculate_stats(data):
    """Recalcula estadisticas a partir de todos los picks."""
    picks = data["picks"]
    stats = {
        "total": 0, "wins": 0, "losses": 0, "pending": 0,
        "win_pct": 0.0, "current_streak": "W0",
        "by_sport": {
            "basketball": {"w": 0, "l": 0},
            "baseball": {"w": 0, "l": 0},
            "hockey": {"w": 0, "l": 0},
            "futbol": {"w": 0, "l": 0},
        }
    }

    for pick in picks:
        status = pick.get("status", "pending")
        sport = pick.get("sport", "")

        if status == "won":
            stats["wins"] += 1
            stats["total"] += 1
            if sport in stats["by_sport"]:
                stats["by_sport"][sport]["w"] += 1
        elif status == "lost":
            stats["losses"] += 1
            stats["total"] += 1
            if sport in stats["by_sport"]:
                stats["by_sport"][sport]["l"] += 1
        elif status == "pending":
            stats["pending"] += 1

    # Win %
    decided = stats["wins"] + stats["losses"]
    stats["win_pct"] = round((stats["wins"] / decided * 100), 1) if decided > 0 else 0.0

    # Racha actual - recorrer picks resueltos en orden cronologico inverso
    resolved = [p for p in picks if p["status"] in ("won", "lost")]
    resolved.sort(key=lambda x: x.get("date", ""), reverse=True)

    streak_type = None
    streak_count = 0
    for pick in resolved:
        if streak_type is None:
            streak_type = pick["status"]
            streak_count = 1
        elif pick["status"] == streak_type:
            streak_count += 1
        else:
            break

    if streak_type == "won":
        stats["current_streak"] = f"W{streak_count}"
    elif streak_type == "lost":
        stats["current_streak"] = f"L{streak_count}"
    else:
        stats["current_streak"] = "W0"

    data["stats"] = stats


def get_stats():
    """Retorna estadisticas actuales."""
    data = _load_data()
    return data["stats"]


def get_recent_picks(n=10):
    """Retorna los ultimos N picks resueltos."""
    data = _load_data()
    resolved = [p for p in data["picks"] if p["status"] in ("won", "lost")]
    resolved.sort(key=lambda x: x.get("date", ""), reverse=True)
    return resolved[:n]


def get_tracking_data():
    """Retorna stats + ultimos picks para el template."""
    data = _load_data()
    stats = data["stats"]
    resolved = [p for p in data["picks"] if p["status"] in ("won", "lost")]
    resolved.sort(key=lambda x: x.get("date", ""), reverse=True)
    recent = resolved[:10]
    return {
        "stats": stats,
        "recent_picks": recent,
        "has_data": stats["total"] > 0,
    }


def print_tracking_stats():
    """Imprime stats de tracking en consola."""
    data = _load_data()
    stats = data["stats"]

    print(f"\n{'='*50}")
    print(f"  TRACKING DE ACIERTOS")
    print(f"{'='*50}")
    print(f"  Record: {stats['wins']}W - {stats['losses']}L ({stats['win_pct']}%)")
    print(f"  Racha actual: {stats['current_streak']}")
    print(f"  Pendientes: {stats['pending']}")
    print()

    print("  Por deporte:")
    for sport, record in stats["by_sport"].items():
        w, l = record["w"], record["l"]
        if w + l > 0:
            pct = round(w / (w + l) * 100, 1)
            print(f"    {sport}: {w}W-{l}L ({pct}%)")

    # Ultimos 10 picks resueltos
    recent = get_recent_picks(10)
    if recent:
        print(f"\n  Ultimos {len(recent)} picks:")
        for p in recent:
            icon = "W" if p["status"] == "won" else "L"
            score = f"{p.get('home_score', '?')}-{p.get('away_score', '?')}"
            print(f"    [{icon}] {p['pick_label']} | {p['home_team']} vs {p['away_team']} ({score})")

    print(f"{'='*50}\n")
