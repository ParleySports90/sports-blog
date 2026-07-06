"""
Publica en Instagram via Make.com webhook.
Requiere: MAKE_WEBHOOK_URL en variables de entorno.
"""

import os
import requests
from datetime import datetime

SITE_URL = "https://parleysports90.github.io/sports-blog"
PICK_IMAGE_URL = f"{SITE_URL}/instagram/pick_del_dia.png"
STATS_IMAGE_URL = f"{SITE_URL}/instagram/stats_card.png"


def _best_pick(predictions):
    best = None
    best_conf = 0
    for sport_key, sport_data in predictions.items():
        for pick in sport_data.get("picks", []):
            conf = pick.get("confidence", 0)
            if conf > best_conf:
                best_conf = conf
                best = {"pick": pick, "sport_key": sport_key, "sport_data": sport_data}
    return best


def _build_pick_caption(pick, sport_key, sport_data):
    sport_icon = sport_data.get("icon", "🎯")
    home = pick.get("home_team", "")
    away = pick.get("away_team", "")
    label = pick.get("pick_label", "")
    conf = pick.get("confidence", 0)
    league = pick.get("league", sport_data.get("name", "Deportes"))

    if conf >= 75:
        conf_badge = "🔥 FIJO"
    elif conf >= 62:
        conf_badge = "✅ PICK SÓLIDO"
    else:
        conf_badge = "📊 ANÁLISIS"

    today = datetime.now().strftime("%d/%m/%Y")
    factors = pick.get("factors", [])
    factor_line = f"\n💡 {factors[0][:90]}" if factors else ""

    hashtags_map = {
        "baseball": "#MLB #Beisbol #PickMLB #PronosticosMLB",
        "basketball": "#NBA #Basketball #PickNBA",
        "futbol": "#Futbol #Soccer #PronosticosFutbol #Mundial2026",
        "hockey": "#NHL #Hockey #PickNHL",
    }
    hashtags = hashtags_map.get(sport_key, "#Deportes #Pronosticos")

    return f"""{sport_icon} PICK DEL DÍA — {league.upper()}
📅 {today}
━━━━━━━━━━━━━━━━━━━━
⚔️ {away} vs {home}
🎯 Pick: {label}
📊 Confianza: {conf}% — {conf_badge}
{factor_line}
━━━━━━━━━━━━━━━━━━━━
🔗 Análisis completo en bio
👉 {SITE_URL}

{hashtags} #ParleySports #Pronosticos #PickDelDia #Apuestas""".strip()


def _build_stats_caption(stats):
    today = datetime.now().strftime("%d/%m/%Y")
    w = stats.get("wins", 0)
    l = stats.get("losses", 0)
    total = stats.get("total", 0)
    pct = stats.get("win_pct", 0)
    streak = stats.get("current_streak", "—")

    return f"""📊 ESTADÍSTICAS DE ACIERTOS
📅 Actualizado: {today}
━━━━━━━━━━━━━━━━━━━━
✅ Ganados: {w}
❌ Perdidos: {l}
🎯 Total picks: {total}
📈 Porcentaje de acierto: {pct}%
🔥 Racha actual: {streak}
━━━━━━━━━━━━━━━━━━━━
🔗 Ver todos los picks en bio
👉 {SITE_URL}

#ParleySports #Estadisticas #Pronosticos #Aciertos #PickDelDia""".strip()


def _send_webhook(webhook_url, payload):
    try:
        r = requests.post(webhook_url, json=payload, timeout=30)
        if r.status_code == 200:
            print(f"  [IG OK] Make.com recibio el webhook correctamente!")
            return True
        print(f"  [IG ERROR] Status {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"  [IG ERROR] {e}")
        return False


def publish_pick_del_dia(predictions):
    """Publica el pick con mayor confianza del dia."""
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "")
    if not webhook_url:
        print("  [IG] MAKE_WEBHOOK_URL no configurada.")
        return False

    best = _best_pick(predictions)
    if not best:
        print("  [IG] Sin picks disponibles para publicar.")
        return False

    pick = best["pick"]
    sport_key = best["sport_key"]
    sport_data = best["sport_data"]
    caption = _build_pick_caption(pick, sport_key, sport_data)

    print(f"  [IG] Pick del Dia: {pick.get('pick_label')} — {pick.get('confidence')}%")
    print(f"  [IG] Enviando a Make.com...")

    return _send_webhook(webhook_url, {
        "image_url": PICK_IMAGE_URL,
        "caption": caption,
        "type": "pick",
        "sport": sport_key,
        "confidence": pick.get("confidence", 0),
        "pick_label": pick.get("pick_label", ""),
        "home_team": pick.get("home_team", ""),
        "away_team": pick.get("away_team", ""),
    })


POLL_IMAGE_URL = f"{SITE_URL}/instagram/poll.png"


def _best_game_for_poll(predictions):
    """Elige el partido mas importante del dia para la encuesta."""
    best = None
    best_conf = 0
    for sport_key, sport_data in predictions.items():
        for pick in sport_data.get("picks", []):
            conf = pick.get("confidence", 0)
            if conf > best_conf:
                best_conf = conf
                best = {
                    "sport_icon": sport_data.get("icon", "🎯"),
                    "sport_name": sport_data.get("name", sport_key),
                    "league": pick.get("league", sport_data.get("name", "")),
                    "home_team": pick.get("home_team", ""),
                    "away_team": pick.get("away_team", ""),
                    "home_abbr": pick.get("home_abbr", ""),
                    "away_abbr": pick.get("away_abbr", ""),
                    "home_logo": pick.get("home_logo", ""),
                    "away_logo": pick.get("away_logo", ""),
                    "sport_key": sport_key,
                }
    return best


def publish_poll(predictions):
    """Publica encuesta del partido mas importante del dia."""
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "")
    if not webhook_url:
        print("  [IG] MAKE_WEBHOOK_URL no configurada.")
        return False

    game = _best_game_for_poll(predictions)
    if not game:
        print("  [IG] Sin partidos para encuesta.")
        return False

    today = datetime.now().strftime("%d/%m/%Y")
    away = game["away_team"]
    home = game["home_team"]
    league = game["league"]
    sport_icon = game["sport_icon"]

    hashtags_map = {
        "baseball": "#MLB #Beisbol #PickMLB",
        "basketball": "#NBA #Basketball",
        "futbol": "#Futbol #Soccer #Mundial2026",
        "hockey": "#NHL #Hockey",
    }
    hashtags = hashtags_map.get(game["sport_key"], "#Deportes")

    caption = f"""{sport_icon} ¿QUIÉN GANA HOY? — {league.upper()}
📅 {today}
━━━━━━━━━━━━━━━━━━━━
⚔️ {away} vs {home}

Comenta 👇
🔵 A — {away}
🔴 B — {home}
━━━━━━━━━━━━━━━━━━━━
Nuestro análisis ya está publicado 👆
🔗 {SITE_URL}

{hashtags} #ParleySports #Encuesta #Pronosticos #PickDelDia""".strip()

    print(f"  [IG] Encuesta: {away} vs {home} ({league})")

    return _send_webhook(webhook_url, {
        "image_url": POLL_IMAGE_URL,
        "caption": caption,
        "type": "poll",
        "home_team": home,
        "away_team": away,
    })


def publish_results(results, stats):
    """Publica card de resultados del dia anterior."""
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "")
    if not webhook_url:
        print("  [IG] MAKE_WEBHOOK_URL no configurada.")
        return False
    if not results:
        print("  [IG] Sin resultados nuevos para publicar.")
        return False

    day_wins = sum(1 for r in results if r["status"] == "won")
    day_losses = sum(1 for r in results if r["status"] == "lost")
    total_w = stats.get("wins", 0)
    total_l = stats.get("losses", 0)
    pct = stats.get("win_pct", 0)
    streak = stats.get("current_streak", "—")
    today = datetime.now().strftime("%d/%m/%Y")

    lines = []
    for r in results:
        icon = "✅" if r["status"] == "won" else "❌"
        label = r.get("pick_label", "")
        hs = r.get("home_score")
        as_ = r.get("away_score")
        ha = r.get("home_abbr") or r.get("home_team", "")[:3].upper()
        aa = r.get("away_abbr") or r.get("away_team", "")[:3].upper()
        score = f"{aa} {as_}-{hs} {ha}" if hs is not None else f"{aa} vs {ha}"
        lines.append(f"{icon} {label} | {score}")

    result_list = "\n".join(lines)
    caption = f"""📊 RESULTADOS — {today}
━━━━━━━━━━━━━━━━━━━━
{result_list}
━━━━━━━━━━━━━━━━━━━━
Día: {day_wins}W — {day_losses}L
Acumulado: {total_w}W-{total_l}L ({pct}%) 🎯
Racha: {streak}
━━━━━━━━━━━━━━━━━━━━
🔗 Picks de hoy ya publicados 👆
👉 {SITE_URL}

#ParleySports #Resultados #PickDelDia #Pronosticos #Aciertos""".strip()

    image_url = f"{SITE_URL}/instagram/resultados.png"
    print(f"  [IG] Publicando resultados: {day_wins}W-{day_losses}L")

    return _send_webhook(webhook_url, {
        "image_url": image_url,
        "caption": caption,
        "type": "results",
        "day_wins": day_wins,
        "day_losses": day_losses,
    })


def publish_reel(video_url, topic):
    """Publica un Reel educativo via Make.com webhook."""
    webhook_url = os.environ.get("MAKE_VIDEO_WEBHOOK_URL", "")
    if not webhook_url:
        print("  [IG] MAKE_VIDEO_WEBHOOK_URL no configurada.")
        return False

    emoji = topic.get("emoji", "🎯")
    title = topic.get("title", "")
    subtitle = topic.get("subtitle", "")
    today = datetime.now().strftime("%d/%m/%Y")
    slides = topic.get("slides", [])
    bullet_lines = "\n".join(
        f"▸ {s['headline']} {s['highlight']}"
        for s in slides if s.get("type") not in ("hook", "cta")
    )

    caption = f"""{emoji} {title.upper()}
{subtitle} — {today}
━━━━━━━━━━━━━━━━━━━━
{bullet_lines}
━━━━━━━━━━━━━━━━━━━━
Guarda este video para referencia 🔖
Síguenos para picks diarios gratuitos 🎯

🔗 {SITE_URL}

#ApuestasDeportivas #Educacion #Beisbol #MLB #Pronosticos #ParleySports #TipsDeApuestas #PickDelDia #ApuestaResponsable""".strip()

    print(f"  [IG] Publicando Reel: {emoji} {title}")

    return _send_webhook(webhook_url, {
        "video_url": video_url,
        "caption": caption,
        "type": "reel",
        "topic_id": topic.get("id", ""),
        "topic_title": title,
    })


def publish_stats(tracking_data):
    """Publica card de estadisticas de aciertos."""
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "")
    if not webhook_url:
        print("  [IG] MAKE_WEBHOOK_URL no configurada.")
        return False

    stats = tracking_data.get("stats", {})
    if not stats or stats.get("total", 0) == 0:
        print("  [IG] Sin estadisticas disponibles para publicar.")
        return False

    caption = _build_stats_caption(stats)
    print(f"  [IG] Publicando estadisticas: {stats.get('wins')}W-{stats.get('losses')}L ({stats.get('win_pct')}%)")
    print(f"  [IG] Enviando a Make.com...")

    return _send_webhook(webhook_url, {
        "image_url": STATS_IMAGE_URL,
        "caption": caption,
        "type": "stats",
    })
