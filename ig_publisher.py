"""
Publica el Pick del Dia en Instagram via Meta Graph API.
Requiere: INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID en variables de entorno.
"""

import os
import time
import requests
from datetime import datetime

GRAPH_URL = "https://graph.facebook.com/v21.0"
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
    """Publica el Pick del Día en Instagram. Retorna True si éxito."""
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
    account_id = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

    if not access_token or not account_id:
        print("  [IG] Faltan variables: INSTAGRAM_ACCESS_TOKEN o INSTAGRAM_ACCOUNT_ID")
        return False

    best = _best_pick(predictions)
    if not best:
        print("  [IG] Sin picks disponibles para publicar.")
        return False

    pick = best["pick"]
    sport_key = best["sport_key"]
    sport_data = best["sport_data"]
    caption = _build_caption(pick, sport_key, sport_data)

    print(f"  [IG] Pick del Día: {pick.get('pick_label')} — {pick.get('confidence')}%")
    print(f"  [IG] Imagen: {PICK_IMAGE_URL}")

    # Paso 1: crear contenedor de media
    r1 = requests.post(
        f"{GRAPH_URL}/{account_id}/media",
        data={
            "image_url": PICK_IMAGE_URL,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )
    d1 = r1.json()

    if "error" in d1:
        print(f"  [IG ERROR] Crear contenedor: {d1['error'].get('message', d1['error'])}")
        return False

    creation_id = d1.get("id")
    if not creation_id:
        print(f"  [IG ERROR] Respuesta inesperada: {d1}")
        return False

    print(f"  [IG] Contenedor listo ({creation_id}), esperando 5s...")
    time.sleep(5)

    # Paso 2: publicar
    r2 = requests.post(
        f"{GRAPH_URL}/{account_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": access_token,
        },
        timeout=30,
    )
    d2 = r2.json()

    if "error" in d2:
        print(f"  [IG ERROR] Publicar: {d2['error'].get('message', d2['error'])}")
        return False

    print(f"  [IG OK] Publicado en Instagram! Media ID: {d2.get('id')}")
    return True
