"""
Sports Blog Generator
=====================
Uso:
    python main.py build          - Obtiene noticias + resultados + pronosticos y genera el blog
    python main.py scores         - Solo actualiza resultados deportivos
    python main.py news           - Solo actualiza noticias
    python main.py predictions    - Solo genera pronosticos deportivos
    python main.py mlb            - Muestra Guia MLB en consola
    python main.py tracking       - Muestra estadisticas de aciertos en consola
    python main.py schedule       - Regenera automaticamente en horarios definidos
    python main.py open           - Abre el blog en el navegador
    python main.py telegram       - Genera y envia pronosticos a Telegram
    python main.py telegram-setup - Guia interactiva para configurar el bot
"""

import os
import sys
import time
import webbrowser
import schedule as sched
import config
from scraper import fetch_all_feeds
from scores import fetch_all_scores
from predictions import fetch_all_predictions, print_predictions
from generator import generate_site
from tracker import check_results, print_tracking_stats


def cmd_build():
    """Obtiene noticias, resultados y pronosticos, genera el sitio completo."""
    # Verificar resultados de picks pendientes antes de generar
    print("[*] Verificando resultados de picks pendientes...")
    check_results()

    articles = fetch_all_feeds()
    scores = fetch_all_scores()
    predictions = fetch_all_predictions(
        min_picks=config.MIN_PICKS_PER_SPORT,
        confidence_threshold=config.CONFIDENCE_THRESHOLD,
    )

    if articles or scores or predictions:
        output = generate_site(articles, scores, predictions)
        print(f"\n[OK] Blog listo. Abre el archivo en tu navegador:")
        print(f"     {os.path.abspath(output)}")
    else:
        print("[!] No se obtuvo contenido.")


def cmd_scores():
    """Solo obtiene resultados y regenera."""
    scores = fetch_all_scores()
    articles = []  # Sin noticias
    if scores:
        output = generate_site(articles, scores)
        print(f"\n[OK] Resultados actualizados: {os.path.abspath(output)}")


def cmd_news():
    """Solo obtiene noticias y regenera."""
    articles = fetch_all_feeds()
    if articles:
        output = generate_site(articles, {})
        print(f"\n[OK] Noticias actualizadas: {os.path.abspath(output)}")


def cmd_schedule():
    """Regenera el blog automaticamente."""
    print(f"[*] Scheduler activo. Horarios: {config.SCHEDULE_TIMES}")
    print("[*] Generando primera version ahora...\n")
    cmd_build()

    for t in config.SCHEDULE_TIMES:
        sched.every().day.at(t).do(cmd_build)

    # Actualizar resultados cada 1 minuto
    sched.every(1).minutes.do(cmd_scores_silent)

    print(f"\n[*] Resultados se actualizan cada 1 minuto.")
    print(f"[*] Build completo a las: {', '.join(config.SCHEDULE_TIMES)}")
    print(f"[*] Esperando... (Ctrl+C para detener)")

    while True:
        sched.run_pending()
        time.sleep(30)


def cmd_predictions():
    """Solo genera pronosticos deportivos."""
    predictions = fetch_all_predictions(
        min_picks=config.MIN_PICKS_PER_SPORT,
        confidence_threshold=config.CONFIDENCE_THRESHOLD,
    )
    print_predictions(predictions)
    # Generar sitio con pronosticos
    articles = fetch_all_feeds()
    scores = fetch_all_scores()
    output = generate_site(articles, scores, predictions)
    print(f"\n[OK] Pronosticos actualizados: {os.path.abspath(output)}")


def cmd_scores_silent():
    """Actualiza resultados sin mucho output."""
    try:
        scores = fetch_all_scores()
        articles = fetch_all_feeds()
        predictions = fetch_all_predictions(
            min_picks=config.MIN_PICKS_PER_SPORT,
            confidence_threshold=config.CONFIDENCE_THRESHOLD,
        )
        generate_site(articles, scores, predictions)
    except Exception as e:
        print(f"[ERROR] Actualizacion fallida: {e}")


def cmd_mlb():
    """Muestra la Guia MLB del dia en consola."""
    from mlb_guide import generate_mlb_guide, print_mlb_guide
    matchups = generate_mlb_guide()
    print_mlb_guide(matchups)


def cmd_tracking():
    """Muestra estadisticas de tracking de aciertos."""
    check_results()
    print_tracking_stats()


def cmd_open():
    """Abre el blog en el navegador."""
    path = os.path.abspath(os.path.join(config.OUTPUT_DIR, "index.html"))
    if os.path.exists(path):
        webbrowser.open(f"file:///{path}")
        print(f"[OK] Abriendo: {path}")
    else:
        print("[!] El blog no existe. Ejecuta 'python main.py build' primero.")


def cmd_telegram():
    """Genera y envia pronosticos a Telegram."""
    from telegram_bot import generate_and_send
    generate_and_send()


def cmd_telegram_setup():
    """Guia interactiva para configurar el bot de Telegram."""
    from telegram_bot import telegram_setup
    telegram_setup()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "build":
        cmd_build()
    elif command == "scores":
        cmd_scores()
    elif command == "news":
        cmd_news()
    elif command == "predictions":
        cmd_predictions()
    elif command == "mlb":
        cmd_mlb()
    elif command == "tracking":
        cmd_tracking()
    elif command == "schedule":
        cmd_schedule()
    elif command == "open":
        cmd_open()
    elif command == "telegram":
        cmd_telegram()
    elif command == "telegram-setup":
        cmd_telegram_setup()
    else:
        print(f"[ERROR] Comando desconocido: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()
