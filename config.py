# Configuracion del blog
BLOG_TITLE = "Parley Sports - Resumen Deportivo"
BLOG_DESCRIPTION = "Noticias, pronosticos y analisis de apuestas deportivas"
BLOG_AUTHOR = "Parley Sports"

# Directorio de salida para el HTML generado
OUTPUT_DIR = "output"

# Feeds RSS - SOLO en espanol, ordenados por prioridad/tendencia
RSS_FEEDS = [
    # === Alta tendencia - Grandes medios deportivos en espanol ===
    {
        "name": "Marca",
        "url": "https://e00-marca.uecdn.es/rss/portada.xml",
        "category": "General",
        "priority": 1,
    },
    {
        "name": "Marca Futbol",
        "url": "https://e00-marca.uecdn.es/rss/futbol/futbol-internacional.xml",
        "category": "Futbol",
        "priority": 1,
    },
    {
        "name": "AS",
        "url": "https://feeds.as.com/mrss-s/pages/as/site/as.com/portada",
        "category": "General",
        "priority": 1,
    },
    {
        "name": "AS Futbol",
        "url": "https://feeds.as.com/mrss-s/pages/as/site/as.com/futbol",
        "category": "Futbol",
        "priority": 1,
    },
    {
        "name": "ESPN Deportes",
        "url": "https://espndeportes.espn.com/espn/rss/noticias",
        "category": "General",
        "priority": 1,
    },
    {
        "name": "Mundo Deportivo",
        "url": "https://www.mundodeportivo.com/feed/rss/home",
        "category": "General",
        "priority": 1,
    },
    # === Media tendencia - Fuentes especializadas ===
    {
        "name": "Marca NBA",
        "url": "https://e00-marca.uecdn.es/rss/baloncesto/nba.xml",
        "category": "NBA",
        "priority": 2,
    },
    {
        "name": "Marca Tenis",
        "url": "https://e00-marca.uecdn.es/rss/tenis.xml",
        "category": "Tenis",
        "priority": 2,
    },
    {
        "name": "AS NBA",
        "url": "https://feeds.as.com/mrss-s/pages/as/site/as.com/baloncesto/nba",
        "category": "NBA",
        "priority": 2,
    },
    {
        "name": "Sport",
        "url": "https://www.sport.es/es/rss/home.xml",
        "category": "General",
        "priority": 2,
    },
    # === Fuentes Latinoamerica ===
    {
        "name": "Ole",
        "url": "https://www.ole.com.ar/rss/ultimas-noticias/",
        "category": "Futbol",
        "priority": 1,
    },
    {
        "name": "TyC Sports",
        "url": "https://www.tycsports.com/rss/futbol",
        "category": "Futbol",
        "priority": 2,
    },
]

# Maximo de articulos por feed
MAX_ARTICLES_PER_FEED = 10

# Total de articulos en la pagina principal
MAX_ARTICLES_HOME = 50

# Horarios para regenerar el blog automaticamente (HH:MM)
SCHEDULE_TIMES = ["06:00", "12:00", "18:00", "22:00"]

# Pronosticos
MIN_PICKS_PER_SPORT = 3
CONFIDENCE_THRESHOLD = 55
