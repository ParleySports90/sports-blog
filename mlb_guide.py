"""
Guia MLB Diaria - Motor de datos estilo Guia Deportiva.
Usa MLB Stats API (statsapi.mlb.com) para obtener schedule, lanzadores probables,
stats detallados de pitchers incluyendo splits home/away, últimos 3 juegos,
splits por mano del bateador (vs zurdo/derecho) y arsenal de pitcheos.
"""

import csv
import io
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


# ─────────────────────────────────────────────
#  Nuevas funciones de estadísticas avanzadas
# ─────────────────────────────────────────────

def _calc_last_games_era(games):
    """Calcula ERA combinada de los últimos juegos para medir forma reciente."""
    if not games:
        return None
    total_er = sum(int(g.get("er", 0)) for g in games)
    total_ip = 0.0
    for g in games:
        try:
            ip_str = str(g.get("ip", "0"))
            if "." in ip_str:
                whole, frac = ip_str.split(".")
                total_ip += int(whole) + int(frac) / 3.0
            else:
                total_ip += float(ip_str)
        except (ValueError, TypeError):
            pass
    if total_ip == 0:
        return None
    return round(total_er * 9 / total_ip, 2)


def fetch_pitcher_last_games(pitcher_id, n=3):
    """Obtiene los últimos N juegos del lanzador desde el game log oficial."""
    season = datetime.now().year
    url = f"{MLB_API}/people/{pitcher_id}/stats"
    params = {
        "stats": "gameLog",
        "group": "pitching",
        "season": season,
        "limit": n,
    }
    data = _get(url, params)
    if not data:
        return []

    games = []
    for stat_group in data.get("stats", []):
        for split in stat_group.get("splits", [])[:n]:
            s = split.get("stat", {})
            # Formatear fecha corta
            raw_date = split.get("date", "")
            try:
                fmt_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%d/%m")
            except Exception:
                fmt_date = raw_date[:5] if raw_date else "-"
            games.append({
                "date": fmt_date,
                "opponent": split.get("opponent", {}).get("abbreviation",
                            split.get("opponent", {}).get("name", "?")),
                "ip": s.get("inningsPitched", "0"),
                "er": s.get("earnedRuns", 0),
                "h": s.get("hits", 0),
                "bb": s.get("baseOnBalls", 0),
                "k": s.get("strikeOuts", 0),
            })
        break  # Solo el primer grupo de stats
    return games[:n]


def fetch_pitcher_handedness_splits(pitcher_id):
    """
    Obtiene BAA (batting average against) del lanzador vs zurdos (vl) y derechos (vr).
    Permite evaluar si el pitcher domina mejor a un tipo de bateador.
    """
    season = datetime.now().year
    url = f"{MLB_API}/people/{pitcher_id}/stats"
    params = {
        "stats": "statSplits",
        "group": "pitching",
        "season": season,
        "sitCodes": "vl,vr",
    }
    data = _get(url, params)
    result = {
        "vs_left":  {"avg": "-", "ops": "-", "k": "-", "bb": "-"},
        "vs_right": {"avg": "-", "ops": "-", "k": "-", "bb": "-"},
    }
    if not data:
        return result

    for stat_group in data.get("stats", []):
        for split in stat_group.get("splits", []):
            code = split.get("split", {}).get("code", "")
            s = split.get("stat", {})
            entry = {
                "avg": s.get("avg", "-"),
                "ops": s.get("ops", "-"),
                "k":   str(s.get("strikeOuts", "-")),
                "bb":  str(s.get("baseOnBalls", "-")),
            }
            if code == "vl":
                result["vs_left"] = entry
            elif code == "vr":
                result["vs_right"] = entry
    return result


def fetch_pitch_arsenal(pitcher_id):
    """
    Obtiene arsenal de pitcheos desde Baseball Savant (Statcast).
    Retorna lista con tipo de lanzamiento, uso, velocidad y BAA por pitch.
    """
    season = datetime.now().year
    url = "https://baseballsavant.mlb.com/statcast_search/csv"
    params = {
        "hfGT": "R|",
        "hfSea": f"{season}|",
        "player_type": "pitcher",
        "pitchers_lookup[]": pitcher_id,
        "group_by": "name-pitch",
        "min_pitches": "20",
        "type": "details",
        "chart": "details",
        "sort_col": "pitches",
        "sort_order": "desc",
    }
    try:
        resp = requests.get(
            url, params=params, timeout=TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        resp.raise_for_status()
        content = resp.text.strip()
        if not content or "pitch_type" not in content:
            return []

        reader = csv.DictReader(io.StringIO(content))
        pitches = []
        for row in reader:
            pitch_type = row.get("pitch_type", "").strip()
            pitch_name = row.get("pitch_name", pitch_type).strip()
            if not pitch_type or pitch_type == "pitch_type":
                continue
            try:
                total_pitches = int(row.get("pitches", 0))
                total_swings = int(row.get("swings", 0))
                total_whiffs = int(row.get("whiffs_swings", 0)) if "whiffs_swings" in row else 0
                hits = int(row.get("hits", 0))
                abs_val = int(row.get("abs", 1)) or 1
                ba = round(hits / abs_val, 3) if abs_val > 0 else None
                whiff_pct = round(total_whiffs / total_swings * 100, 1) if total_swings > 0 else None
                avg_speed = row.get("avg_speed", row.get("release_speed", "-")).strip()
            except (ValueError, TypeError, KeyError):
                ba = None
                whiff_pct = None
                avg_speed = "-"
                total_pitches = 0

            pitches.append({
                "pitch_name":  pitch_name or pitch_type,
                "pitch_type":  pitch_type,
                "total":       total_pitches,
                "avg_speed":   avg_speed,
                "ba":          f".{int(ba*1000):03d}" if ba is not None else "-",
                "whiff_pct":   f"{whiff_pct}%" if whiff_pct is not None else "-",
            })
        return pitches
    except Exception as e:
        print(f"    [!] Baseball Savant error para pitcher {pitcher_id}: {e}")
        return []


# ─────────────────────────────────────────────
#  Funciones principales de la guia MLB
# ─────────────────────────────────────────────

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
            if status in ("Preview", "Pre-Game", "Warmup", "Live", "Final"):
                games.append(game)
    return games


def fetch_pitcher_stats(pitcher_id):
    """
    Obtiene stats de temporada + splits home/away + últimos 3 juegos
    + splits por mano del bateador + arsenal de pitcheos.
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
        "name":       person.get("lastInitName", person.get("fullName", "?")),
        "full_name":  person.get("fullName", "?"),
        "hand":       person.get("pitchHand", {}).get("code", "?"),
        "record":     "0-0",
        "era":        "-",
        "ip":         "0",
        "hits":       "0",
        "runs":       "0",
        "er":         "0",
        "bb":         "0",
        "so":         "0",
        "whip":       "-",
        "k9":         "-",
        "home_era":   "-",
        "away_era":   "-",
        "home_record": "0-0",
        "away_record": "0-0",
        # Nuevos campos
        "last_games":         [],
        "last_games_era":     None,
        "handedness_splits":  {
            "vs_left":  {"avg": "-", "ops": "-", "k": "-", "bb": "-"},
            "vs_right": {"avg": "-", "ops": "-", "k": "-", "bb": "-"},
        },
        "arsenal": [],
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
            result["era"]    = str(s.get("era", "-"))
            result["ip"]     = str(s.get("inningsPitched", "0"))
            result["hits"]   = str(s.get("hits", 0))
            result["runs"]   = str(s.get("runs", 0))
            result["er"]     = str(s.get("earnedRuns", 0))
            result["bb"]     = str(s.get("baseOnBalls", 0))
            result["so"]     = str(s.get("strikeOuts", 0))
            result["whip"]   = str(s.get("whip", "-"))
            result["k9"]     = str(s.get("strikeoutsPer9Inn", "-"))

        elif stat_type == "homeAndAway":
            for split in splits:
                split_desc = split.get("split", {}).get("description", "")
                s = split.get("stat", {})
                if split_desc == "Home":
                    result["home_era"]    = str(s.get("era", "-"))
                    result["home_record"] = f"{s.get('wins', 0)}-{s.get('losses', 0)}"
                elif split_desc == "Away":
                    result["away_era"]    = str(s.get("era", "-"))
                    result["away_record"] = f"{s.get('wins', 0)}-{s.get('losses', 0)}"

    # Estadísticas avanzadas adicionales
    result["last_games"]        = fetch_pitcher_last_games(pitcher_id)
    result["last_games_era"]    = _calc_last_games_era(result["last_games"])
    result["handedness_splits"] = fetch_pitcher_handedness_splits(pitcher_id)
    result["arsenal"]           = fetch_pitch_arsenal(pitcher_id)

    return result


def fetch_team_batting_stats(team_id):
    """Obtiene stats de bateo del equipo en la temporada actual."""
    url = f"{MLB_API}/teams/{team_id}/stats"
    params = {
        "stats": "season",
        "group": "hitting",
        "season": datetime.now().year,
        "sportId": 1,
    }
    data = _get(url, params)
    if not data:
        return None
    for group in data.get("stats", []):
        splits = group.get("splits", [])
        if splits:
            s = splits[0].get("stat", {})
            gp = s.get("gamesPlayed", 1) or 1
            runs = s.get("runs", 0)
            return {
                "avg": s.get("avg", "-"),
                "obp": s.get("obp", "-"),
                "slg": s.get("slg", "-"),
                "ops": s.get("ops", "-"),
                "rpg": round(runs / gp, 2) if gp else "-",
                "hr":  s.get("homeRuns", 0),
                "bb":  s.get("baseOnBalls", 0),
                "so":  s.get("strikeOuts", 0),
            }
    return None


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
    Calcula pick con 7 factores ponderados:
    1. ERA temporada       (20%) - efectividad global
    2. ERA últimos 3 jgs   (20%) - forma reciente del lanzador
    3. WHIP                (15%) - control de base runners
    4. K/BB ratio          (10%) - dominio vs bateadores
    5. Record equipo       (10%) - respaldo ofensivo/defensivo
    6. Splits home/away    (15%) - ERA en el rol que juega hoy
    7. BAA vs mano         (10%) - efectividad vs perfil del lineup
    """
    score_home = 0.0
    score_away = 0.0

    # 1. ERA temporada (20%)
    home_era = _safe_float(home_pitcher["era"])
    away_era = _safe_float(away_pitcher["era"])
    if home_era < away_era:
        score_home += 20 * min((away_era - home_era) / 3.0, 1.0)
    elif away_era < home_era:
        score_away += 20 * min((home_era - away_era) / 3.0, 1.0)

    # 2. ERA últimos 3 juegos (20%) - forma reciente es clave
    h_recent = _safe_float(home_pitcher.get("last_games_era"), default=None)
    a_recent = _safe_float(away_pitcher.get("last_games_era"), default=None)
    if h_recent is not None and a_recent is not None and h_recent != 999.0 and a_recent != 999.0:
        if h_recent < a_recent:
            score_home += 20 * min((a_recent - h_recent) / 4.0, 1.0)
        elif a_recent < h_recent:
            score_away += 20 * min((h_recent - a_recent) / 4.0, 1.0)
    elif h_recent is not None and h_recent != 999.0:
        if h_recent < home_era:
            score_home += 8  # Está mejorando su ERA
    elif a_recent is not None and a_recent != 999.0:
        if a_recent < away_era:
            score_away += 8

    # 3. WHIP (15%)
    home_whip = _safe_float(home_pitcher["whip"])
    away_whip = _safe_float(away_pitcher["whip"])
    if home_whip < away_whip:
        score_home += 15 * min((away_whip - home_whip) / 0.5, 1.0)
    elif away_whip < home_whip:
        score_away += 15 * min((home_whip - away_whip) / 0.5, 1.0)

    # 4. K/BB ratio (10%)
    home_so  = _safe_float(home_pitcher["so"], 0)
    home_bb  = _safe_float(home_pitcher["bb"], 1)
    away_so  = _safe_float(away_pitcher["so"], 0)
    away_bb  = _safe_float(away_pitcher["bb"], 1)
    home_kbb = home_so / max(home_bb, 1)
    away_kbb = away_so / max(away_bb, 1)
    if home_kbb > away_kbb:
        score_home += 10 * min((home_kbb - away_kbb) / 2.0, 1.0)
    elif away_kbb > home_kbb:
        score_away += 10 * min((away_kbb - home_kbb) / 2.0, 1.0)

    # 5. Record equipo (10%)
    hw, hl = _parse_record(home_record)
    aw, al = _parse_record(away_record)
    home_pct = hw / max(hw + hl, 1)
    away_pct = aw / max(aw + al, 1)
    if home_pct > away_pct:
        score_home += 10 * min((home_pct - away_pct) / 0.2, 1.0)
    elif away_pct > home_pct:
        score_away += 10 * min((away_pct - home_pct) / 0.2, 1.0)

    # 6. Splits home/away ERA (15%)
    home_split_era = _safe_float(home_pitcher["home_era"])
    away_split_era = _safe_float(away_pitcher["away_era"])
    if home_split_era < away_split_era:
        score_home += 15 * min((away_split_era - home_split_era) / 3.0, 1.0)
    elif away_split_era < home_split_era:
        score_away += 15 * min((home_split_era - away_split_era) / 3.0, 1.0)

    # 7. BAA promedio vs ambas manos (10%)
    def _avg_baa(pitcher):
        try:
            splits = pitcher.get("handedness_splits", {})
            baa_l = float(splits.get("vs_left", {}).get("avg", "-"))
            baa_r = float(splits.get("vs_right", {}).get("avg", "-"))
            return (baa_l + baa_r) / 2.0
        except (ValueError, TypeError):
            return None

    home_avg_baa = _avg_baa(home_pitcher)
    away_avg_baa = _avg_baa(away_pitcher)
    if home_avg_baa is not None and away_avg_baa is not None:
        if home_avg_baa < away_avg_baa:
            score_home += 10 * min((away_avg_baa - home_avg_baa) / 0.050, 1.0)
        elif away_avg_baa < home_avg_baa:
            score_away += 10 * min((home_avg_baa - away_avg_baa) / 0.050, 1.0)

    return score_home, score_away


def _generate_analysis(matchup):
    """Genera texto de análisis enriquecido con estadísticas avanzadas."""
    hp  = matchup["home_pitcher"]
    ap  = matchup["away_pitcher"]
    pick = matchup["pick"]
    home = matchup["home_abbr"]
    away = matchup["away_abbr"]

    lines = []

    if pick == home:
        fav_p, fav_team, dog_p, fav_abbr, dog_abbr = hp, matchup["home_team"], ap, home, away
    else:
        fav_p, fav_team, dog_p, fav_abbr, dog_abbr = ap, matchup["away_team"], hp, away, home

    # Línea principal del lanzador favorito
    lines.append(
        f"{fav_p['name']} ({fav_p['record']}, {fav_p['era']} ERA) "
        f"lidera el staff de {fav_team} con {fav_p['so']} ponches en {fav_p['ip']} innings."
    )

    # Forma reciente (últimos 3 juegos)
    last_games = fav_p.get("last_games", [])
    last_era   = fav_p.get("last_games_era")
    if last_games:
        salidas = [f"{g['ip']}IP/{g['er']}CL/{g['k']}K" for g in last_games[:3]]
        forma_txt = f"Últimos {len(salidas)} jgs: {', '.join(salidas)}"
        if last_era is not None:
            forma_txt += f" — ERA reciente: {last_era}"
        lines.append(forma_txt + ".")

    # Split relevante (casa/ruta)
    if pick == home and fav_p["home_era"] != "-":
        lines.append(f"En casa: {fav_p['home_era']} ERA ({fav_p['home_record']}).")
    elif pick != home and fav_p["away_era"] != "-":
        lines.append(f"De visitante: {fav_p['away_era']} ERA ({fav_p['away_record']}).")

    # Splits por mano del bateador
    splits = fav_p.get("handedness_splits", {})
    vs_l   = splits.get("vs_left", {}).get("avg", "-")
    vs_r   = splits.get("vs_right", {}).get("avg", "-")
    if vs_l != "-" or vs_r != "-":
        lines.append(f"BAA vs zurdos: {vs_l} | vs derechos: {vs_r}.")

    # WHIP comparativo
    if fav_p["whip"] != "-" and dog_p["whip"] != "-":
        try:
            if float(fav_p["whip"]) < float(dog_p["whip"]):
                lines.append(
                    f"WHIP {fav_p['whip']} vs {dog_p['whip']} de {dog_p['name']} favorece a {fav_abbr}."
                )
        except ValueError:
            pass

    # Records de equipos
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

    home_probable = home_team_data.get("probablePitcher", {})
    away_probable = away_team_data.get("probablePitcher", {})

    home_pitcher_id = home_probable.get("id")
    away_pitcher_id = away_probable.get("id")

    if not home_pitcher_id and not away_pitcher_id:
        return None

    home_pitcher = fetch_pitcher_stats(home_pitcher_id) if home_pitcher_id else None
    away_pitcher = fetch_pitcher_stats(away_pitcher_id) if away_pitcher_id else None

    _empty_splits = {
        "vs_left":  {"avg": "-", "ops": "-", "k": "-", "bb": "-"},
        "vs_right": {"avg": "-", "ops": "-", "k": "-", "bb": "-"},
    }

    if not home_pitcher:
        home_pitcher = {
            "name": home_probable.get("lastInitName", "TBD"),
            "full_name": home_probable.get("fullName", "TBD"),
            "hand": "?", "record": "0-0", "era": "-", "ip": "0",
            "hits": "0", "runs": "0", "er": "0", "bb": "0", "so": "0",
            "whip": "-", "k9": "-", "home_era": "-", "away_era": "-",
            "home_record": "0-0", "away_record": "0-0",
            "last_games": [], "last_games_era": None,
            "handedness_splits": _empty_splits, "arsenal": [],
        }
    if not away_pitcher:
        away_pitcher = {
            "name": away_probable.get("lastInitName", "TBD"),
            "full_name": away_probable.get("fullName", "TBD"),
            "hand": "?", "record": "0-0", "era": "-", "ip": "0",
            "hits": "0", "runs": "0", "er": "0", "bb": "0", "so": "0",
            "whip": "-", "k9": "-", "home_era": "-", "away_era": "-",
            "home_record": "0-0", "away_record": "0-0",
            "last_games": [], "last_games_era": None,
            "handedness_splits": _empty_splits, "arsenal": [],
        }

    home_rec   = home_team_data.get("leagueRecord", {})
    away_rec   = away_team_data.get("leagueRecord", {})
    home_record = f"{home_rec.get('wins', 0)}-{home_rec.get('losses', 0)}"
    away_record = f"{away_rec.get('wins', 0)}-{away_rec.get('losses', 0)}"

    # Hora del juego
    game_date_str = game.get("gameDate", "")
    game_time = ""
    if game_date_str:
        try:
            dt = datetime.fromisoformat(game_date_str.replace("Z", "+00:00"))
            from datetime import timedelta
            dt_local = dt - timedelta(hours=4)  # EDT
            game_time = dt_local.strftime("%-I:%M %p") if hasattr(dt_local, 'strftime') else dt_local.strftime("%I:%M %p")
        except Exception:
            game_time = ""
    if game_time.startswith("0"):
        game_time = game_time[1:]

    venue = game.get("venue", {}).get("name", "")

    home_id   = home_team_info.get("id", "")
    away_id   = away_team_info.get("id", "")
    home_logo = f"https://www.mlbstatic.com/team-logos/{home_id}.svg" if home_id else ""
    away_logo = f"https://www.mlbstatic.com/team-logos/{away_id}.svg" if away_id else ""

    home_abbr = home_team_info.get("abbreviation", "???")
    away_abbr = away_team_info.get("abbreviation", "???")

    home_batting = fetch_team_batting_stats(home_id) if home_id else None
    away_batting = fetch_team_batting_stats(away_id) if away_id else None

    score_home, score_away = _calculate_pick(
        home_pitcher, away_pitcher,
        home_record, away_record,
        home_team_info.get("name", ""),
        away_team_info.get("name", ""),
        True,
    )
    pick = home_abbr if score_home >= score_away else away_abbr

    matchup = {
        "home_team":    home_team_info.get("name", "?"),
        "away_team":    away_team_info.get("name", "?"),
        "home_abbr":    home_abbr,
        "away_abbr":    away_abbr,
        "home_logo":    home_logo,
        "away_logo":    away_logo,
        "home_record":  home_record,
        "away_record":  away_record,
        "game_time":    game_time,
        "venue":        venue,
        "home_pitcher": home_pitcher,
        "away_pitcher": away_pitcher,
        "pick":         pick,
        "score_home":   round(score_home, 1),
        "score_away":   round(score_away, 1),
        "analysis":     "",
        "home_batting": home_batting,
        "away_batting": away_batting,
    }

    matchup["analysis"] = _generate_analysis(matchup)
    return matchup


def generate_mlb_guide(date=None):
    """
    Funcion principal: genera la guia MLB completa del dia.
    Retorna lista de matchups con stats avanzados de lanzadores y picks.
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

    print(f"\n{'='*110}")
    print(f"  GUIA MLB - {datetime.now().strftime('%d/%m/%Y')}")
    print(f"{'='*110}")

    print(
        f"\n{'Hora':<10} {'Matchup':<28} {'Lanzador Local':<18} {'ERA':>5} "
        f"{'ERA-3':>6} {'SO':>4} {'WHIP':>6} {'vs-Z':>6} {'vs-D':>6} | "
        f"{'Lanzador Visita':<18} {'ERA':>5} {'ERA-3':>6} {'SO':>4} "
        f"{'WHIP':>6} {'vs-Z':>6} {'vs-D':>6} | {'Pick':>5}"
    )
    print(f"{'-'*200}")

    for m in matchups:
        hp = m["home_pitcher"]
        ap = m["away_pitcher"]
        h_splits = hp.get("handedness_splits", {})
        a_splits = ap.get("handedness_splits", {})
        matchup_str = f"{m['away_abbr']} @ {m['home_abbr']}"
        print(
            f"{m['game_time']:<10} {matchup_str:<28} "
            f"{hp['name']:<18} {hp['era']:>5} "
            f"{str(hp.get('last_games_era') or '-'):>6} {hp['so']:>4} {hp['whip']:>6} "
            f"{h_splits.get('vs_left', {}).get('avg', '-'):>6} "
            f"{h_splits.get('vs_right', {}).get('avg', '-'):>6} | "
            f"{ap['name']:<18} {ap['era']:>5} "
            f"{str(ap.get('last_games_era') or '-'):>6} {ap['so']:>4} {ap['whip']:>6} "
            f"{a_splits.get('vs_left', {}).get('avg', '-'):>6} "
            f"{a_splits.get('vs_right', {}).get('avg', '-'):>6} | "
            f"{'>>'+m['pick'] if m['pick'] else 'N/A':>5}"
        )

    print(f"\n{'='*110}")
    print("\nANALISIS:")
    print(f"{'='*110}")

    for m in matchups:
        print(f"\n{m['away_abbr']} @ {m['home_abbr']} ({m['venue']})")
        print(f"  {m['analysis']}")

        for side, pitcher in [("LOCAL", m["home_pitcher"]), ("VISITA", m["away_pitcher"])]:
            games = pitcher.get("last_games", [])
            if games:
                print(f"\n  {side} - Últimos {len(games)} juegos:")
                for g in games:
                    print(f"    {g['date']} vs {g['opponent']}: {g['ip']}IP, {g['h']}H, {g['er']}CL, {g['bb']}BB, {g['k']}K")

            arsenal = pitcher.get("arsenal", [])
            if arsenal:
                print(f"\n  {side} - Arsenal de pitcheos:")
                for p in arsenal:
                    print(f"    {p['pitch_name']}: {p['avg_speed']} mph | BAA: {p['ba']} | Whiff: {p['whiff_pct']}")
