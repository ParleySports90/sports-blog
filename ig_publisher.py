"""
Publica el Pick del Dia en Instagram via Make.com webhook.
Requiere: MAKE_WEBHOOK_URL en variables de entorno.
"""

import os
import requests
from datetime import datetime

SITE_URL = "https://parleysports90.github.io/sports-blog"
PICK_IMAGE_URL = f"{SITE_URL}/instagram/pick_del_dia.png"


def _best_pick(predictions):
    """Retorna el pick con mayor confianza de todos los deportes."""
    best = None
    best_conf = 0
    for sport_key, sport_data in predictions.items():
        for pick in sport_data.get("picks", []):
            conf = pick.get("confidence", 0)
            if conf > best_conf:
                best_conf = conf
                best = {
                    "pick": pick,
                    "sport_key": sport_key,
                    "sport_data": sport_data,
                }
    return best


def _build_caption(pick, sport_key, sport_data):
    """Genera caption optimizado para Instagram."""
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

    caption = f"""{sport_icon} PICK DEL DÍA — {league.upper()}
📅 {today}
━━━━━━━━━━━━━━━━━━━━
⚔️ {away} vs {home}
🎯 Pick: {label}
📊 Confianza: {conf}% — {conf_badge}
{factor_line}
━━━━━━━━━━━━━━━━━━━━
🔗 Análisis completo en bio
👉 {SITE_URL}

{hashtags} #ParleySports #Pronosticos #PickDelDia #Apuestas"""

    return caption.strip()


def publish_pick_del_dia(predictions):
    """Publica el Pick del Dia en Instagram via Make.com webhook."""
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL", "")

    if not webhook_url:
        print("  [IG] MAKE_WEBHOOK_URL no configurada. Saltando publicacion.")
        return False

    best = _best_pick(predictions)
    if not best:
        print("  [IG] Sin picks disponibles para publicar.")
        return False

    pick = best["pick"]
    sport_key = best["sport_key"]
    sport_data = best["sport_data"]
    caption = _build_caption(pick, sport_key, sport_data)

    print(f"  [IG] Pick del Dia: {pick.get('pick_label')} — {pick.get('confidence')}%")
    print(f"  [IG] Imagen: {PICK_IMAGE_URL}")
    print(f"  [IG] Enviando a Make.com...")

    payload = {
        "image_url": PICK_IMAGE_URL,
        "caption": caption,
        "sport": sport_key,
        "confidence": pick.get("confidence", 0),
        "pick_label": pick.get("pick_label", ""),
        "home_team": pick.get("home_team", ""),
        "away_team": pick.get("away_team", ""),
    }

    try:
        r = requests.post(webhook_url, json=payload, timeout=30)
        if r.status_code == 200:
            print(f"  [IG OK] Make.com recibio el webhook correctamente!")
            return True
        else:
            print(f"  [IG ERROR] Status {r.status_code}: {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  [IG ERROR] {e}")
        return False
