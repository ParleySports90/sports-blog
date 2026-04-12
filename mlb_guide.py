"""
Guia MLB Diaria - Motor de datos estilo Guia Deportiva.
Usa MLB Stats API (statsapi.mlb.com) para obtener schedule, lanzadores probables,
y stats detallados de pitchers incluyendo splits home/away.
"""

import requests
from datetime import datetime, timezone

MLB_API = "https://statsapi.mlb.com/api/v1"
TIMEOUT = 15


def _get(url, params=None):
    """GET request con manejo de errores."""
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"    [!] MLB API error: {e}")
        return None


def fetch_mlb_schedule(date=None):
    """
    Obtiene juegos del dia con lanzadores probables.
    date: formato YYYY-MM-DD, default hoy.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    url = f"{MLB_API}/schedule"
    params = {
        "sportId": 1,
        "date": date,
        "hydrate": "probablePitcher(note),team,linescore",
    }
    data = _get(url, params)
    if not data:
        return []

    games = []
    for date_entry in data.get("dates", []):
        for game in date_entry.get("games", []):
            status = game.get("status", {}).get("abstractGameState", "")
            # Solo juegos programados o en progreso
            if status in ("Preview", "Pre-Game", "Warmup", "Live", "Final"):
                games.append(game)
    return games


def fetch_pitcher_stats(pitcher_id):
    """
    Obtiene stats de temporada + splits home/away de un lanzador.
    Retorna dict con stats o None si falla.
    """
    url = f"{MLB_API}/people/{pitcher_id}"
    params = {
        "hydrate": "stats(group=[pitching],type=[season,homeAndAway],sportId=1)",
    }
    data = _get(url, params)
    if not data:
        return None

    people = data.get("people", [])
    if not people:
        return None

    person = people[0]
    stats_groups = person.get("stats", [])

    result = {
        "name": person.get("lastInitName", person.get("fullName", "?")),
        "full_name": person.get("fullName", "?"),
        "hand": person.get("pitchHand", {}).get("code", "?"),
        "record": "0-0",
        "era": "-",
        "ip": "0",
        "hits": "0",
        "runs": "0",
        "er": "0",
        "bb": "0",
        "so": "0",
        "whip": "-",
        "k9": "-",
        "home_era": "-",
        "away_era": "-",
        "home_record": "0-0",
        "away_record": "0-0",
    }

    # Stats de temporada
    for stat_group in stats_groups:
        stat_type = stat_group.get("type", {}).get("displayName", "")
        splits = stat_group.get("splits", [])

        if stat_type == "season" and splits:
            s = splits[0].get("stat", {})
            w = s.get("wins", 0)
            l = s.get("losses", 0)
            result["record"] = f"{w}-{l}"
            result["era"] = str(s.get("era", "-"))
            result["ip"] = str(s.get("inningsPitched", "0"))
            result["hits"] = str(s.get("hits", 0))
            result["runs"] = str(s.get("runs", 0))
            result["er"] = str(s.get("earnedRuns", 0))
            result["bb"] = str(s.get("baseOnBalls", 0))
            result["so"] = str(s.get("strikeOuts", 0))
            result["whip"] = str(s.get("whip", "-"))
            result["k9"] = str(s.get("strikeoutsPer9Inn", "-"))

        elif stat_type == "homeAndAway":
            for split in splits:
                split_desc = split.get("split", {}).get("description", "")
                s = split.get("stat", {})
                if split_desc == "Home":
                    result["home_era"] = str(s.get("era", "-"))
                    result["home_record"] = f"{s.get('wins', 0)}-{s.get('losses', 0)}"
                elif split_desc == "Away":
                    result["away_era"] = str(s.get("era", "-"))
                    result["away_record"] = f"{s.get('wins', 0)}-{s.get('losses', 0)}"

    return result


def _safe_float(val, default=999.0):
    """Convierte string a float de forma segura."""
    try:
        v = float(val)
        return v if v > 0 else default
    except (ValueError, TypeError):
        return default


def _parse_record(record_str):
    """Parsea '10-5' a (wins, losses)."""
    try:
        parts = record_str.split("-")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 0, 0


def _calculate_pick(home_pitcher, away_pitcher, home_record, away_record,
                    home_team, away_team, is_home_pitching_home):
    """
    Calcula pick basado en comparacion de lanzadores y equipos.
    Retorna (pick_abbr, score_home, score_away).

    Pesos:
    1. ERA (30%) - menor = mejor
    2. WHIP (20%) - menor = mejor
    3. K/BB ratio (15%) - mayor = mejor
    4. Record equipo (15%) - mejor = ventaja
    5. Splits home/away (20%) - ERA relevante del split
    """
    score_home = 0.0
    score_away = 0.0

    # 1. ERA (30%)
    home_era = _safe_float(home_pitcher["era"])
    away_era = _safe_float(away_pitcher["era"])
    if home_era < away_era:
        score_home += 30 * min((away_era - home_era) / 3.0, 1.0)
    elif away_era < home_era:
        score_away += 30 * min((home_era - away_era) / 3.0, 1.0)

    # 2. WHIP (20%)
    home_whip = _safe_float(home_pitcher["whip"])
    away_whip = _safe_float(away_pitcher["whip"])
    if home_whip < away_whip:
        score_home += 20 * min((away_whip - home_whip) / 0.5, 1.0)
    elif away_whip < home_whip:
        score_away += 20 * min((home_whip - away_whip) / 0.5, 1.0)

    # 3. K/BB ratio (15%)
    home_so = _safe_float(home_pitcher["so"], 0)
    home_bb = _safe_float(home_pitcher["bb"], 1)
    away_so = _safe_float(away_pitcher["so"], 0)
    away_bb = _safe_float(away_pitcher["bb"], 1)
    home_kbb = home_so / max(home_bb, 1)
    away_kbb = away_so / max(away_bb, 1)
    if home_kbb > away_kbb:
        score_home += 15 * min((home_kbb - away_kbb) / 2.0, 1.0)
    elif away_kbb > home_kbb:
        score_away += 15 * min((away_kbb - home_kbb) / 2.0, 1.0)

    # 4. Record equipo (15%)
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    home_pct = hw / max(hw + hl, 1)
    away_pct = aw / max(aw + al, 1)
    if home_pct > away_pct:
        score_home += 15 * min((home_pct - away_pct) / 0.2, 1.0)
    elif away_pct > home_pct:
        score_away += 15 * min((away_pct - home_pct) / 0.2, 1.0)

    # 5. Splits home/away (20%)
    # Home pitcher en casa vs Away pitcher de visita
    home_split_era = _safe_float(home_pitcher["home_era"])
    away_split_era = _safe_float(away_pitcher["away_era"])
    if home_split_era < away_split_era:
        score_home += 20 * min((away_split_era - home_split_era) / 3.0, 1.0)
    elif away_split_era < home_split_era:
        score_away += 20 * min((home_split_era - away_split_era) / 3.0, 1.0)

    return score_home, score_away


def _generate_analysis(matchup):
    """Genera texto de analisis estilo Guia Deportiva."""
    hp = matchup["home_pitcher"]
    ap = matchup["away_pitcher"]
    pick = matchup["pick"]
    home = matchup["home_abbr"]
    away = matchup["away_abbr"]

    lines = []

    # Comparar lanzadores
    if pick == home:
        fav_p = hp
        fav_team = matchup["home_team"]
        dog_p = ap
        dog_team = matchup["away_team"]
        fav_abbr = home
        dog_abbr = away
    else:
        fav_p = ap
        fav_team = matchup["away_team"]
        dog_p = hp
        dog_team = matchup["home_team"]
        fav_abbr = away
        dog_abbr = home

    # Linea sobre el lanzador favorito
    era_fav = fav_p["era"]
    record_fav = fav_p["record"]
    so_fav = fav_p["so"]
    lines.append(
        f"{fav_p['name']} ({record_fav}, {era_fav} ERA) lidera el staff de {fav_team} "
        f"con {so_fav} ponches en {fav_p['ip']} innings."
    )

    # Split relevante
    if pick == home and fav_p["home_era"] != "-":
        lines.append(
            f"En casa registra {fav_p['home_era']} de ERA ({fav_p['home_record']})."
        )
    elif pick != home and fav_p["away_era"] != "-":
        lines.append(
            f"De visitante registra {fav_p['away_era']} de ERA ({fav_p['away_record']})."
        )

    # WHIP comparison
    fav_whip = fav_p["whip"]
    dog_whip = dog_p["whip"]
    if fav_whip != "-" and dog_whip != "-":
        try:
            if float(fav_whip) < float(dog_whip):
                lines.append(
                    f"WHIP de {fav_whip} vs {dog_whip} de {dog_p['name']} favorece a {fav_abbr}."
                )
        except ValueError:
            pass

    # Record de equipos
    lines.append(
        f"{matchup['home_abbr']} ({matchup['home_record']}) vs "
        f"{matchup['away_abbr']} ({matchup['away_record']})."
    )

    # Pick final
    lines.append(f"PICK: {pick}.")

    return " ".join(lines)


def build_matchup(game):
    """Construye un matchup completo con datos de ambos lanzadores."""
    teams = game.get("teams", {})
    home_team_data = teams.get("home", {})
    away_team_data = teams.get("away", {})

    home_team_info = home_team_data.get("team", {})
    away_team_info = away_team_data.get("team", {})

    # Lanzadores probables
    home_probable = home_team_data.get("probablePitcher", {})
    away_probable = away_team_data.get("probablePitcher", {})

    home_pitcher_id = home_probable.get("id")
    away_pitcher_id = away_probable.get("id")

    # Si no hay lanzadores probables, skip
    if not home_pitcher_id and not away_pitcher_id:
        return None

    # Obtener stats de lanzadores
    home_pitcher = None
    away_pitcher = None

    if home_pitcher_id:
        home_pitcher = fetch_pitcher_stats(home_pitcher_id)
    if away_pitcher_id:
        away_pitcher = fetch_pitcher_stats(away_pitcher_id)

    # Crear placeholders si no hay data
    if not home_pitcher:
        home_pitcher = {
            "name": home_probable.get("lastInitName", "TBD"),
            "full_name": home_probable.get("fullName", "TBD"),
            "hand": "?", "record": "0-0", "era": "-", "ip": "0",
            "hits": "0", "runs": "0", "er": "0", "bb": "0", "so": "0",
            "whip": "-", "k9": "-", "home_era": "-", "away_era": "-",
            "home_record": "0-0", "away_record": "0-0",
        }
    if not away_pitcher:
        away_pitcher = {
            "name": away_probable.get("lastInitName", "TBD"),
            "full_name": away_probable.get("fullName", "TBD"),
            "hand": "?", "record": "0-0", "era": "-", "ip": "0",
            "hits": "0", "runs": "0", "er": "0", "bb": "0", "so": "0",
            "whip": "-", "k9": "-", "home_era": "-", "away_era": "-",
            "home_record": "0-0", "away_record": "0-0",
        }

    # Records de equipos
    home_rec = home_team_data.get("leagueRecord", {})
    away_rec = away_team_data.get("leagueRecord", {})
    home_record = f"{home_rec.get('wins', 0)}-{home_rec.get('losses', 0)}"
    away_record = f"{away_rec.get('wins', 0)}-{away_rec.get('losses', 0)}"

    # Hora del juego
    game_date_str = game.get("gameDate", "")
    game_time = ""
    if game_date_str:
        try:
            dt = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            # Convertir a hora local (EST/EDT aprox)
            from datetime import timedelta
            dt_local = dt - timedelta(hours=4)  # EDT
            game_time = dt_local.strftime("%-I:%M %p") if hasattr(dt_local, 'strftime') else dt_local.strftime("%I:%M %p")
        except Exception:
            game_time = ""
    # Limpiar leading zero en hora Windows
    if game_time.startswith("0"):
        game_time = game_time[1:]

    venue = game.get("venue", {}).get("name", "")

    # Team logos (usar MLB static content)
    home_id = home_team_info.get("id", "")
    away_id = away_team_info.get("id", "")
    home_logo = f"https://www.mlbstatic.com/team-logos/{home_id}.svg" if home_id else ""
    away_logo = f"https://www.mlbstatic.com/team-logos/{away_id}.svg" if away_id else ""

    home_abbr = home_team_info.get("abbreviation", "???")
    away_abbr = away_team_info.get("abbreviation", "???")

    # Calcular pick
    score_home, score_away = _calculate_pick(
        home_pitcher, away_pitcher,
        home_record, away_record,
        home_team_info.get("name", ""),
        away_team_info.get("name", ""),
        True
    )
    pick = home_abbr if score_home >= score_away else away_abbr

    matchup = {
        "home_team": home_team_info.get("name", "?"),
        "away_team": away_team_info.get("name", "?"),
        "home_abbr": home_abbr,
        "away_abbr": away_abbr,
        "home_logo": home_logo,
        "away_logo": away_logo,
        "home_record": home_record,
        "away_record": away_record,
        "game_time": game_time,
        "venue": venue,
        "home_pitcher": home_pitcher,
        "away_pitcher": away_pitcher,
        "pick": pick,
        "score_home": round(score_home, 1),
        "score_away": round(score_away, 1),
        "analysis": "",
    }

    matchup["analysis"] = _generate_analysis(matchup)

    return matchup


def generate_mlb_guide(date=None):
    """
    Funcion principal: genera la guia MLB completa del dia.
    Retorna lista de matchups con stats de lanzadores y picks.
    """
    print("[*] Generando Guia MLB...")

    games = fetch_mlb_schedule(date)
    if not games:
        print("    Sin juegos de MLB programados para hoy")
        return []

    print(f"    {len(games)} juegos encontrados")

    matchups = []
    for game in games:
        try:
            matchup = build_matchup(game)
            if matchup:
                matchups.append(matchup)
                print(f"    {matchup['away_abbr']} @ {matchup['home_abbr']} -> Pick: {matchup['pick']}")
        except Exception as e:
            print(f"    [!] Error procesando juego: {e}")

    print(f"[OK] Guia MLB: {len(matchups)} matchups generados")
    return matchups


def print_mlb_guide(matchups):
    """Imprime la guia MLB en consola con formato tabla."""
    if not matchups:
        print("\nSin juegos de MLB para hoy.")
        return

    print(f"\n{'='*90}")
    print(f"  GUIA MLB - {datetime.now().strftime('%d/%m/%Y')}")
    print(f"{'='*90}")

    # Header de tabla
    print(f"\n{'Hora':<10} {'Matchup':<28} {'Lanzador Local':<18} {'ERA':>5} {'SO':>4} {'WHIP':>6} | {'Lanzador Visita':<18} {'ERA':>5} {'SO':>4} {'WHIP':>6} | {'Pick':>5}")
    print(f"{'-'*10} {'-'*28} {'-'*18} {'-'*5} {'-'*4} {'-'*6} | {'-'*18} {'-'*5} {'-'*4} {'-'*6} | {'-'*5}")

    for m in matchups:
        hp = m["home_pitcher"]
        ap = m["away_pitcher"]
        matchup_str = f"{m['away_abbr']} @ {m['home_abbr']}"
        print(
            f"{m['game_time']:<10} {matchup_str:<28} "
            f"{hp['name']:<18} {hp['era']:>5} {hp['so']:>4} {hp['whip']:>6} | "
            f"{ap['name']:<18} {ap['era']:>5} {ap['so']:>4} {ap['whip']:>6} | "
            f"{'>>'+m['pick'] if m['pick'] else 'N/A':>5}"
        )

    print(f"\n{'='*90}")
    print("\nANALISIS:")
    print(f"{'='*90}")

    for m in matchups:
        print(f"\n{m['away_abbr']} @ {m['home_abbr']} ({m['venue']})")
        print(f"  {m['analysis']}")
