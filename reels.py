"""
Genera Reels educativos para Instagram (MP4 1080x1920).
Usa Playwright para slides y FFmpeg para ensamblar el video.
"""

import os
import json
import subprocess
import shutil
import tempfile
from datetime import datetime

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "instagram", "reels")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ROTATION_FILE = os.path.join(DATA_DIR, "reel_rotation.json")
SITE_URL = "parleysports90.github.io/sports-blog"

# ─── Temas educativos ────────────────────────────────────────────────────────

TOPICS = [
    {
        "id": "run_line",
        "title": "Run Line",
        "subtitle": "La apuesta del béisbol",
        "emoji": "⚾",
        "color": "#1565c0",
        "color_rgb": "21,101,192",
        "slides": [
            {"type": "hook",    "headline": "¿Sabes qué es",    "highlight": "el RUN LINE?",          "body": "La apuesta más popular del béisbol"},
            {"type": "explain", "headline": "Es el SPREAD",      "highlight": "del béisbol",            "body": "Una ventaja de ±1.5 carreras\naplicada al resultado final"},
            {"type": "example", "headline": "Ejemplo real:",     "highlight": "LAD −1.5",               "body": "Los Dodgers deben ganar\npor 2 o más carreras"},
            {"type": "win",     "headline": "LAD gana 5−3",      "highlight": "✅ GANAS",               "body": "Ganó por 2 carreras ≥ 1.5\n¡El run line cubrió!"},
            {"type": "lose",    "headline": "LAD gana 3−2",      "highlight": "❌ PIERDES",             "body": "Ganó por 1 carrera < 1.5\nEl run line no cubrió"},
            {"type": "tip",     "headline": "Úsalo cuando",      "highlight": "el favorito es claro",   "body": "Mejor pago que el ML\ncon riesgo controlado"},
            {"type": "cta",     "headline": "Síguenos para",     "highlight": "más tips 🔔",            "body": "Picks diarios gratis\nParleySports90"},
        ],
    },
    {
        "id": "money_line",
        "title": "Money Line",
        "subtitle": "La apuesta más directa",
        "emoji": "💵",
        "color": "#6a1b9a",
        "color_rgb": "106,27,154",
        "slides": [
            {"type": "hook",    "headline": "¿Qué es",           "highlight": "el MONEY LINE?",         "body": "La apuesta más simple en deportes"},
            {"type": "explain", "headline": "Apuestas",          "highlight": "quién gana",             "body": "Sin spreads ni ventajas\nSolo el resultado directo"},
            {"type": "example", "headline": "Ejemplo:",          "highlight": "NYY −150",               "body": "Yankees favoritos\nArriesgas $150 para ganar $100"},
            {"type": "example", "headline": "Otro lado:",        "highlight": "BOS +130",               "body": "Red Sox underdogs\nArriesgas $100 para ganar $130"},
            {"type": "tip",     "headline": "Señal negativa",    "highlight": "= favorito",             "body": "Señal positiva = underdog\nMayor riesgo, mayor premio"},
            {"type": "tip",     "headline": "Cuándo usarlo:",    "highlight": "underdogs con valor",    "body": "Busca equipos subvalorados\ncon buen rendimiento reciente"},
            {"type": "cta",     "headline": "Te damos los",      "highlight": "mejores picks 🎯",       "body": "Análisis estadístico diario\nParleySports90"},
        ],
    },
    {
        "id": "over_under",
        "title": "Over / Under",
        "subtitle": "Alta o Baja",
        "emoji": "📊",
        "color": "#e65100",
        "color_rgb": "230,81,0",
        "slides": [
            {"type": "hook",    "headline": "¿Sabes apostar",    "highlight": "OVER / UNDER?",          "body": "No importa quién gana"},
            {"type": "explain", "headline": "El casino pone",    "highlight": "un número total",        "body": "Tú decides si el marcador\nfinal será mayor o menor"},
            {"type": "example", "headline": "Béisbol:",          "highlight": "O/U 8.5 Carreras",       "body": "OVER: el juego termina 9+ carreras\nUNDER: termina 8 o menos"},
            {"type": "example", "headline": "NBA:",              "highlight": "O/U 225.5 Puntos",       "body": "OVER: ambos equipos suman 226+\nUNDER: suman 225 o menos"},
            {"type": "tip",     "headline": "Factores clave:",   "highlight": "clima y pitcheo",        "body": "Viento en contra = UNDER\nPitchers dominantes = UNDER"},
            {"type": "tip",     "headline": "Qué buscar:",       "highlight": "tendencias recientes",   "body": "¿El equipo juega partidos\nde muchas o pocas carreras?"},
            {"type": "cta",     "headline": "Incluimos O/U",     "highlight": "en cada análisis 📈",    "body": "Picks con contexto completo\nParleySports90"},
        ],
    },
    {
        "id": "parlays",
        "title": "¿Qué es un Parlay?",
        "subtitle": "Combina tus picks",
        "emoji": "🎰",
        "color": "#1b5e20",
        "color_rgb": "27,94,32",
        "slides": [
            {"type": "hook",    "headline": "¿Quieres",          "highlight": "multiplicar ganancias?", "body": "El PARLAY es tu herramienta"},
            {"type": "explain", "headline": "Combinas",          "highlight": "2 o más picks",          "body": "Todos deben ganar\nEl pago se multiplica"},
            {"type": "example", "headline": "Parlay 3 picks:",   "highlight": "×6 de retorno",          "body": "Pick 1: LAD ML (−120)\nPick 2: NYY ML (−110)\nPick 3: MIL ML (−115)"},
            {"type": "win",     "headline": "Los 3 ganan",       "highlight": "✅ ×6 tu dinero",        "body": "$50 se convierten en $300\nAlto riesgo, alta recompensa"},
            {"type": "lose",    "headline": "1 falla",           "highlight": "❌ pierdes todo",        "body": "Es el riesgo del parlay\nUn pick malo lo cancela todo"},
            {"type": "tip",     "headline": "Regla de oro:",     "highlight": "máximo 3 picks",         "body": "Más picks = menos probabilidad\nMantenlo simple y selectivo"},
            {"type": "cta",     "headline": "Nuestros picks",    "highlight": "son ideales para parlay","body": "Picks FIJO ≥75% confianza\nParleySports90"},
        ],
    },
    {
        "id": "leer_lineas",
        "title": "Cómo leer líneas",
        "subtitle": "Entiende los números",
        "emoji": "📈",
        "color": "#b71c1c",
        "color_rgb": "183,28,28",
        "slides": [
            {"type": "hook",    "headline": "¿Los números",      "highlight": "te confunden?",          "body": "En 60 segundos lo entiendes todo"},
            {"type": "explain", "headline": "Una línea típica:", "highlight": "LAD −1.5 (−120)",        "body": "Equipo / Spread / Precio"},
            {"type": "example", "headline": "El PRECIO",         "highlight": "−120 significa:",        "body": "Apuesta $120 para ganar $100\nEs el \"costo\" de apostar"},
            {"type": "example", "headline": "Precio positivo",   "highlight": "+140 significa:",        "body": "Apuesta $100 para ganar $140\nSiempre es el underdog"},
            {"type": "explain", "headline": "El SPREAD",         "highlight": "−1.5 / +1.5",            "body": "Negativo = favorito\nPositivo = underdog\nSiempre suman ~0"},
            {"type": "tip",     "headline": "Busca valor en",    "highlight": "+130 a +160",            "body": "Underdogs con buenas stats\nson la mejor oportunidad"},
            {"type": "cta",     "headline": "Nosotros hacemos",  "highlight": "el análisis por ti 🧠", "body": "Picks diarios gratuitos\nParleySports90"},
        ],
    },
]


# ─── Rotación de temas ────────────────────────────────────────────────────────

def _get_next_topic():
    """Selecciona el topic siguiente en rotacion ciclica."""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(ROTATION_FILE, "r") as f:
            data = json.load(f)
        last_idx = data.get("last_index", -1)
    except (FileNotFoundError, json.JSONDecodeError):
        last_idx = -1

    next_idx = (last_idx + 1) % len(TOPICS)
    with open(ROTATION_FILE, "w") as f:
        json.dump({"last_index": next_idx, "date": datetime.now().strftime("%Y-%m-%d")}, f)
    return TOPICS[next_idx]


def get_topic_by_id(topic_id):
    for t in TOPICS:
        if t["id"] == topic_id:
            return t
    return None


# ─── HTML de cada slide ───────────────────────────────────────────────────────

_SLIDE_TYPE_STYLES = {
    "hook":    {"bg_extra": "rgba(255,255,255,0.02)", "num_color": "rgba(255,255,255,0.25)"},
    "explain": {"bg_extra": "rgba(255,255,255,0.02)", "num_color": "rgba(255,255,255,0.25)"},
    "example": {"bg_extra": "rgba(255,255,255,0.03)", "num_color": "rgba(255,255,255,0.25)"},
    "win":     {"bg_extra": "rgba(76,175,80,0.06)",   "num_color": "rgba(76,175,80,0.5)"},
    "lose":    {"bg_extra": "rgba(233,69,96,0.06)",   "num_color": "rgba(233,69,96,0.5)"},
    "tip":     {"bg_extra": "rgba(255,183,77,0.05)",  "num_color": "rgba(255,183,77,0.4)"},
    "cta":     {"bg_extra": "rgba(255,255,255,0.02)", "num_color": "rgba(255,255,255,0.25)"},
}

_HIGHLIGHT_COLORS = {
    "win":  "#4caf50",
    "lose": "#e94560",
    "tip":  "#ffb74d",
    "cta":  "#64b5f6",
}


def _build_slide_html(slide, topic, slide_num, total):
    color = topic["color"]
    color_rgb = topic["color_rgb"]
    emoji = topic["emoji"]
    topic_title = topic["title"]
    stype = slide.get("type", "explain")

    style = _SLIDE_TYPE_STYLES.get(stype, _SLIDE_TYPE_STYLES["explain"])
    highlight_color = _HIGHLIGHT_COLORS.get(stype, color)

    headline = slide.get("headline", "")
    highlight = slide.get("highlight", "")
    body = slide.get("body", "").replace("\n", "<br>")

    # Dots de progreso
    dots = ""
    for i in range(total):
        active = "active" if i == slide_num else ""
        dots += f'<div class="dot {active}"></div>'

    # Icono especial para tipo
    type_icon = {"win": "✅", "lose": "❌", "tip": "💡", "cta": "🔔", "hook": "🎯"}.get(stype, "")

    css = f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    width:1080px; height:1920px;
    background:linear-gradient(160deg,#080d14 0%,#0d1520 45%,#080d14 100%);
    font-family:'Inter',-apple-system,sans-serif;
    color:#e6edf3;
    display:flex; flex-direction:column;
    align-items:center; justify-content:center;
    padding:100px 80px 80px;
    position:relative; overflow:hidden;
}}
body::before {{
    content:""; position:absolute;
    top:-300px; right:-300px;
    width:900px; height:900px;
    background:radial-gradient(circle,rgba({color_rgb},0.12) 0%,transparent 60%);
    pointer-events:none;
}}
body::after {{
    content:""; position:absolute;
    bottom:-250px; left:-250px;
    width:700px; height:700px;
    background:radial-gradient(circle,rgba({color_rgb},0.07) 0%,transparent 60%);
    pointer-events:none;
}}
.header {{
    position:absolute; top:80px; left:80px; right:80px;
    display:flex; justify-content:space-between; align-items:center;
}}
.topic-badge {{
    display:flex; align-items:center; gap:12px;
    background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.08);
    border-radius:40px; padding:10px 20px;
    font-size:0.9rem; color:rgba(255,255,255,0.5); letter-spacing:0.5px;
}}
.topic-emoji {{ font-size:1.1rem; }}
.slide-counter {{
    font-size:0.85rem; letter-spacing:1px;
    color:{style['num_color']};
    font-weight:600;
}}
.content {{
    width:100%; display:flex; flex-direction:column;
    align-items:center; text-align:center; gap:0;
}}
.type-icon {{
    font-size:4rem; margin-bottom:36px; line-height:1;
}}
.headline {{
    font-family:'Oswald',sans-serif;
    font-size:3.2rem; font-weight:400;
    color:rgba(255,255,255,0.6);
    letter-spacing:1px; line-height:1.15;
    margin-bottom:12px;
    text-transform:uppercase;
}}
.highlight {{
    font-family:'Oswald',sans-serif;
    font-size:4.8rem; font-weight:700;
    color:{highlight_color};
    letter-spacing:1px; line-height:1.1;
    margin-bottom:40px;
    text-transform:uppercase;
}}
.body-text {{
    font-size:1.55rem; color:rgba(255,255,255,0.55);
    line-height:1.7; max-width:840px;
    font-weight:400;
}}
.divider {{
    width:80px; height:4px;
    background:linear-gradient(90deg,transparent,{color},{color},transparent);
    border-radius:2px; margin:44px auto;
}}
.footer {{
    position:absolute; bottom:70px; left:80px; right:80px;
    display:flex; flex-direction:column; align-items:center; gap:20px;
}}
.dots {{ display:flex; gap:10px; align-items:center; }}
.dot {{
    width:8px; height:8px; border-radius:50%;
    background:rgba(255,255,255,0.2); transition:all 0.3s;
}}
.dot.active {{
    width:28px; border-radius:4px;
    background:{color};
}}
.brand {{
    font-family:'Oswald',sans-serif; font-size:1.1rem;
    font-weight:600; color:rgba(255,255,255,0.2);
    letter-spacing:2px; text-transform:uppercase;
}}
"""

    type_icon_html = f'<div class="type-icon">{type_icon}</div>' if type_icon else ""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
    <div class="header">
        <div class="topic-badge">
            <span class="topic-emoji">{emoji}</span>
            <span>{topic_title}</span>
        </div>
        <span class="slide-counter">{slide_num + 1} / {total}</span>
    </div>

    <div class="content">
        {type_icon_html}
        <div class="headline">{headline}</div>
        <div class="highlight">{highlight}</div>
        <div class="divider"></div>
        <div class="body-text">{body}</div>
    </div>

    <div class="footer">
        <div class="dots">{dots}</div>
        <div class="brand">@parleysports90</div>
    </div>
</body>
</html>"""


# ─── Generación del Reel ─────────────────────────────────────────────────────

def generate_reel(topic_id=None, output_dir=OUTPUT_DIR):
    """
    Genera un Reel educativo MP4.
    Si topic_id es None usa el siguiente en rotacion.
    Retorna (ruta_mp4, topic) o (None, None).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [Reels] Playwright no disponible.")
        return None, None

    if shutil.which("ffmpeg") is None:
        print("  [Reels] FFmpeg no disponible.")
        return None, None

    topic = get_topic_by_id(topic_id) if topic_id else _get_next_topic()
    if not topic:
        print(f"  [Reels] Topic '{topic_id}' no encontrado.")
        return None, None

    slides = topic["slides"]
    total = len(slides)
    os.makedirs(output_dir, exist_ok=True)

    print(f"  [Reels] Generando: {topic['emoji']} {topic['title']} ({total} slides)...")

    # ── Paso 1: capturar slides con Playwright ──────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="reel_")
    slide_paths = []

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1080, "height": 1920})

            for i, slide in enumerate(slides):
                html = _build_slide_html(slide, topic, i, total)
                page.set_content(html, wait_until="networkidle")
                path = os.path.join(tmp_dir, f"slide_{i:02d}.png")
                page.screenshot(path=path, full_page=False)
                slide_paths.append(path)
                print(f"    Slide {i+1}/{total} capturada")

            browser.close()

        # ── Paso 2: ensamblar video con FFmpeg ──────────────────────────────
        concat_file = os.path.join(tmp_dir, "slides.txt")
        with open(concat_file, "w") as f:
            for path in slide_paths:
                f.write(f"file '{path}'\n")
                f.write("duration 4\n")
            # Repetir ultimo frame para evitar corte brusco
            f.write(f"file '{slide_paths[-1]}'\n")

        out_path = os.path.join(output_dir, f"{topic['id']}.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-vf", "scale=1080:1920:flags=lanczos,fps=30",
            "-c:v", "libx264", "-preset", "fast",
            "-crf", "22", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  [Reels ERROR] FFmpeg: {result.stderr[-300:]}")
            return None, None

        size_mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"  [Reels OK] {out_path} ({size_mb:.1f} MB)")
        return out_path, topic

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
