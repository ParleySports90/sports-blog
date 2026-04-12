"""
Modulo de scraping RSS para obtener noticias deportivas en espanol.
Ordena por tendencia (prioridad del feed) y luego por fecha.
"""

import re
import feedparser
import hashlib
from datetime import datetime, timezone
from dateutil import parser as dateparser
import config


def fetch_feed(feed_info):
    """Obtiene articulos de un feed RSS."""
    articles = []
    try:
        feed = feedparser.parse(feed_info["url"])
        for entry in feed.entries[: config.MAX_ARTICLES_PER_FEED]:
            # Extraer fecha
            pub_date = None
            if hasattr(entry, "published"):
                try:
                    pub_date = dateparser.parse(entry.published)
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                except Exception:
                    pub_date = datetime.now(timezone.utc)
            else:
                pub_date = datetime.now(timezone.utc)

            # Extraer resumen/descripcion
            summary = ""
            if hasattr(entry, "summary"):
                summary = entry.summary
            elif hasattr(entry, "description"):
                summary = entry.description

            # Limpiar HTML basico del summary
            summary = clean_html(summary)

            # Extraer imagen si existe
            image = extract_image(entry)

            # Generar ID unico
            article_id = hashlib.md5(entry.link.encode()).hexdigest()[:12]

            articles.append({
                "id": article_id,
                "title": entry.title,
                "link": entry.link,
                "summary": summary[:400],
                "image": image,
                "date": pub_date,
                "source": feed_info["name"],
                "category": feed_info["category"],
                "priority": feed_info.get("priority", 3),
            })

        print(f"  [OK] {feed_info['name']}: {len(articles)} articulos")
    except Exception as e:
        print(f"  [ERROR] {feed_info['name']}: {e}")

    return articles


def extract_image(entry):
    """Extrae la imagen de un entry RSS de varias maneras."""
    # media:content
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url", "")
    # media:thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    # enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href", "")
    # Buscar imagen en el contenido HTML
    content = ""
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")
    elif hasattr(entry, "summary"):
        content = entry.summary
    if content:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
        if img_match:
            return img_match.group(1)
    return ""


def clean_html(text):
    """Remueve tags HTML basicos de un texto."""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = clean.replace("&nbsp;", " ")
    clean = clean.replace("&amp;", "&")
    clean = clean.replace("&lt;", "<")
    clean = clean.replace("&gt;", ">")
    clean = clean.replace("&quot;", '"')
    clean = clean.replace("&#039;", "'")
    return clean.strip()


def deduplicate(articles):
    """Elimina articulos duplicados basado en titulo similar."""
    seen_titles = set()
    unique = []
    for article in articles:
        # Normalizar titulo para detectar duplicados
        normalized = re.sub(r'[^a-z0-9\s]', '', article["title"].lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        # Usar las primeras 8 palabras como clave
        key = " ".join(normalized.split()[:8])
        if key not in seen_titles:
            seen_titles.add(key)
            unique.append(article)
    return unique


def fetch_all_feeds():
    """Obtiene articulos de todos los feeds, ordena por tendencia y fecha."""
    print("[*] Obteniendo noticias deportivas (espanol)...\n")
    all_articles = []

    for feed_info in config.RSS_FEEDS:
        articles = fetch_feed(feed_info)
        all_articles.extend(articles)

    # Eliminar duplicados
    all_articles = deduplicate(all_articles)

    # Ordenar: primero por prioridad (1=tendencia alta), luego por fecha reciente
    all_articles.sort(key=lambda x: (x["priority"], -x["date"].timestamp()))

    # Limitar total
    all_articles = all_articles[: config.MAX_ARTICLES_HOME]

    print(f"\n[OK] Total: {len(all_articles)} articulos (sin duplicados).")
    return all_articles
