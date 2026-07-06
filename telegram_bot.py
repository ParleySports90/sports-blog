"""
Bot de Telegram para ParleySports90.
Envia pronosticos diarios y notificaciones de Reels educativos.
Requiere: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID en variables de entorno.
"""

import os
import requests
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
API = f"https://api.telegram.org/bot{TOKEN}"
SITE_URL = "https://parleysports90.github.io/sports-blog"


def _send(method, data):
    if not TOKEN or not CHAT_ID:
        print("  [Telegram] TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados.")
        return False
    try:
        r = requests.post(f"{API}/{method}", json=data, timeout=15)
        if r.status_code == 200:
            return True
        print(f"  [Telegram ERROR] {r.status_code}: {r.text[:200]}")
        return False
    except Exception as e:
        print(f"  [Telegram ERROR] {e}")
        return False


def send_message(text, parse_mode="HTML"):
    return _send("sendMessage", {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    })


def send_reel_notification(video_url, topic, caption):
    """Notifica que un Reel educativo esta listo para publicar."""
    emoji = topic.get("emoji", "🎬")
    title = topic.get("title", "Reel educativo")
    today = datetime.now().strftime("%d/%m/%Y")

    msg = f"""🎬 <b>REEL EDUCATIVO LISTO — {today}</b>

{emoji} <b>{title}</b>

<b>Pasos para publicar:</b>
1. Descarga el video 👇
2. Abre Instagram → Reels
3. Sube el video
4. Agrega música de tendencia 🎵
5. Copia y pega el caption de abajo
6. Publica

━━━━━━━━━━━━━━━━━━━━
📥 <b>DESCARGAR VIDEO:</b>
{video_url}
━━━━━━━━━━━━━━━━━━━━"""

    ok = send_message(msg)

    if ok:
        # Enviar el caption por separado para facil copia
        caption_msg = f"📝 <b>CAPTION PARA COPIAR:</b>\n\n<code>{caption}</code>"
        send_message(caption_msg)
        print(f"  [Telegram OK] Notificacion de Reel enviada")

    return ok


def generate_and_send():
    """Envia pronosticos del dia a Telegram."""
    try:
        from predictions import fetch_all_predictions
        import config

        predictions = fetch_all_predictions(
            min_picks=config.MIN_PICKS_PER_SPORT,
            confidence_threshold=config.CONFIDENCE_THRESHOLD,
        )
    except Exception as e:
        print(f"  [Telegram] Error obteniendo predicciones: {e}")
        return False

    if not predictions:
        print("  [Telegram] Sin predicciones para enviar.")
        return False

    today = datetime.now().strftime("%d/%m/%Y")
    lines = [f"🎯 <b>PICKS DEL DÍA — {today}</b>\n"]

    for sport_key, sport_data in predictions.items():
        picks = sport_data.get("picks", [])
        if not picks:
            continue
        icon = sport_data.get("icon", "⚽")
        name = sport_data.get("name", sport_key.upper())
        lines.append(f"\n{icon} <b>{name}</b>")

        for pick in picks:
            conf = pick.get("confidence", 0)
            label = pick.get("pick_label", "")
            home = pick.get("home_team", "")
            away = pick.get("away_team", "")
            conf_icon = "🔥" if conf >= 75 else ("✅" if conf >= 62 else "📊")
            lines.append(f"{conf_icon} {away} vs {home}\n   ➤ <b>{label}</b> ({conf}%)")

    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"🔗 Análisis completo:\n{SITE_URL}")

    msg = "\n".join(lines)
    ok = send_message(msg)
    if ok:
        print(f"  [Telegram OK] Picks enviados al canal")
    return ok


def telegram_setup():
    """Guia interactiva para configurar el bot."""
    print("""
╔══════════════════════════════════════════════════╗
║      CONFIGURACION BOT DE TELEGRAM               ║
╚══════════════════════════════════════════════════╝

PASO 1 — Crear el bot:
  1. Abre Telegram → busca @BotFather
  2. Escribe /newbot
  3. Nombre: ParleySports Bot
  4. Username: parleysports90_bot (o similar)
  5. Copia el TOKEN que te da BotFather

PASO 2 — Obtener tu Chat ID:
  1. Escribe cualquier mensaje a tu nuevo bot
  2. Visita esta URL en tu navegador:
     https://api.telegram.org/bot{TU_TOKEN}/getUpdates
  3. Busca "chat":{"id": XXXXXXX}
  4. Ese numero es tu CHAT_ID

PASO 3 — Agregar secrets en GitHub:
  github.com/ParleySports90/sports-blog
  → Settings → Secrets → Actions
  → TELEGRAM_BOT_TOKEN = el token del paso 1
  → TELEGRAM_CHAT_ID   = el id del paso 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Para probar localmente ejecuta:
  set TELEGRAM_BOT_TOKEN=tu_token
  set TELEGRAM_CHAT_ID=tu_chat_id
  python main.py telegram
""")
