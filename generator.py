"""
Generador de sitio estatico a partir de los articulos y resultados obtenidos.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import config


def generate_site(articles, scores=None, predictions=None):
    """Genera el HTML estatico del blog."""
    print("[*] Generando sitio web...")

    # Configurar Jinja2
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("index.html")

    # Preparar datos para el template
    categories = sorted(set(a["category"] for a in articles))

    for article in articles:
        if article["date"]:
            article["date_str"] = article["date"].strftime("%d %b %Y - %H:%M")
        else:
            article["date_str"] = "Sin fecha"

    html = template.render(
        blog_title=config.BLOG_TITLE,
        blog_description=config.BLOG_DESCRIPTION,
        articles=articles,
        categories=categories,
        scores=scores or {},
        predictions=predictions or {},
        last_updated=datetime.now().strftime("%d/%m/%Y %H:%M"),
        year=datetime.now().year,
    )

    # Guardar archivo (encode/decode para limpiar surrogates)
    output_path = os.path.join(config.OUTPUT_DIR, "index.html")
    clean_html = html.encode("utf-8", errors="replace").decode("utf-8")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(clean_html)

    print(f"[OK] Sitio generado: {os.path.abspath(output_path)}")
    return output_path
