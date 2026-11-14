import base64
from pathlib import Path

import streamlit as st

LOGO_FILE = Path(__file__).resolve().parent / "assets" / "logo.svg"

# Midnight Metro palette
BG = "#111827"          # page
SIDEBAR = "#172033"     # sidebar
SURFACE = "#1F2937"     # cards and charts
BORDER = "#374151"
TEAL = "#2DD4BF"
BLUE = "#38BDF8"
WHITE = "#F9FAFB"
GREY = "#94A3B8"
AMBER = "#F59E0B"       # warning
CORAL = "#F87171"       # error
GREEN = "#34D399"       # success
INK = "#0B1220"         # dark text on the bright teal and blue fills

COLOUR_A = TEAL         # Compare page: left side
COLOUR_B = AMBER        # Compare page: right side

# A small icon in the corner of each card, chosen by the card label
ICONS = {
    "Total rentals": "🚲",
    "Average per day": "📊",
    "Busiest hour": "⏰",
    "Peak month": "🏆",
    "Lowest month": "❄️",
    "Busiest day": "🏆",
    "Quietest day": "😴",
    "Model error (MAE)": "🎯",
    "Predicted demand": "✨",
    "Typical miss": "📏",
}

CSS = f"""
<style>
/* Page and sidebar */
.stApp {{
    background: linear-gradient(160deg, {BG} 0%, #131C30 60%, #182138 100%);
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{ background: {SIDEBAR}; border-right: 1px solid {BORDER}; }}

/* Top navigation: pill links on the right, below Streamlit's own header */
[data-testid="stPageLink"] a {{
    justify-content: center;
    border-radius: 999px;
    padding: 6px 14px;
    border: 1px solid {BORDER};
    background: {SURFACE};
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}}
[data-testid="stPageLink"] a:hover {{ border-color: {TEAL}; box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.25); }}
[data-testid="stPageLink"] a[aria-current="page"] {{
    background: linear-gradient(90deg, {TEAL}, {BLUE});
    border-color: transparent;
}}
[data-testid="stPageLink"] a[aria-current="page"] * {{ color: {INK} !important; font-weight: 700; }}
[data-testid="stPageLink"] a, [data-testid="stPageLink"] a * {{ cursor: pointer !important; }}

/* Banner: a soft teal and blue glow on a dark surface, with a gradient title */
.banner {{
    background:
        radial-gradient(circle at 92% 0%, rgba(56, 189, 248, 0.40), transparent 45%),
        radial-gradient(circle at 0% 115%, rgba(45, 212, 191, 0.30), transparent 45%),
        linear-gradient(120deg, {SIDEBAR} 0%, {SURFACE} 100%);
    border: 1px solid {BORDER};
    border-radius: 24px;
    padding: 28px 32px;
    display: flex;
    align-items: center;
    gap: 24px;
    margin-bottom: 24px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
}}
.banner img {{ width: 96px; height: 96px; }}
.banner h1 {{
    margin: 0;
    padding: 0;
    font-size: 2.3rem;
    background: linear-gradient(90deg, {TEAL}, {BLUE});
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
}}
.banner p {{ color: #CBD5E1; margin: 6px 0 0 0; font-size: 1.05rem; }}

/* Number cards: a coloured edge, a corner icon, a lift and a teal glow on hover */
.card {{
    position: relative;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-left: 6px solid {TEAL};
    border-radius: 20px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    padding: 18px 20px;
    min-height: 130px;
    margin-bottom: 16px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(45, 212, 191, 0.20);
}}
.card .icon {{ position: absolute; top: 14px; right: 18px; font-size: 1.4rem; }}
.card .label {{ color: {GREY}; font-size: 0.85rem; }}
.card .value {{ color: {WHITE}; font-size: 1.9rem; font-weight: 700; }}
.card .note {{ color: {GREY}; font-size: 0.8rem; }}

/* The model card: filled with teal and blue */
.card.hero {{
    background: linear-gradient(135deg, {TEAL}, {BLUE});
    border: none;
}}
.card.hero .label, .card.hero .note {{ color: #0F3D4A; }}
.card.hero .value {{ color: {INK}; }}

.notice {{
    background: rgba(245, 158, 11, 0.12);
    border-left: 6px solid {AMBER};
    border-radius: 14px;
    padding: 12px 16px;
    color: {WHITE};
    margin: 12px 0;
}}

/* Boxes that hold a chart */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-color: {BORDER};
    border-radius: 20px;
    background: {SURFACE};
}}

/* Dropdowns, radio buttons and buttons: pointer cursor, rounded, teal glow on hover */
[data-testid="stSelectbox"] * {{ cursor: pointer !important; }}
[data-testid="stSelectbox"] input {{ caret-color: transparent; }}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    border-radius: 14px;
    transition: box-shadow 0.15s ease, border-color 0.15s ease;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {{
    border-color: {TEAL};
    box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.25);
}}
[data-baseweb="popover"] li {{ cursor: pointer !important; }}
[data-testid="stRadio"] label {{ cursor: pointer !important; }}
button {{ cursor: pointer !important; }}
.stButton > button {{ border-radius: 999px; font-weight: 600; }}
.stButton > button[kind="primary"] {{
    background: linear-gradient(90deg, {TEAL}, {BLUE});
    color: {INK};
    border: none;
}}

/* Navigation cards on the Landing page */
.nav-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 18px 20px;
    min-height: 110px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.nav-card:hover {{
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(56, 189, 248, 0.22);
}}
.nav-card h3 {{ margin: 0 0 6px 0; padding: 0; color: {WHITE}; font-size: 1.15rem; }}
.nav-card p {{ margin: 0; color: {GREY}; font-size: 0.9rem; }}

/* Compare page: name tags and butterfly bars */
.vs-row {{
    display: grid;
    grid-template-columns: 1fr 90px 1fr;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}}
.vs-tag {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    color: {WHITE};
    border-radius: 40px;
    padding: 8px 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-weight: 700;
    font-size: 1.05rem;
}}
.vs-tag.b {{ flex-direction: row-reverse; }}
.vs-tag .letter {{
    border-radius: 50%;
    width: 34px;
    height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: {INK};
}}
.vs-tag.a .letter {{ background: linear-gradient(135deg, {TEAL}, {BLUE}); }}
.vs-tag.b .letter {{ background: linear-gradient(135deg, {AMBER}, {CORAL}); }}
.vs-mid {{ text-align: center; font-weight: 800; font-size: 1.3rem; color: {WHITE}; }}
.vs-metric {{ text-align: center; color: {GREY}; font-size: 0.85rem; margin: 14px 0 4px 0; }}
.vs-line {{
    display: grid;
    grid-template-columns: 1fr 56px 1fr;
    align-items: center;
    gap: 10px;
}}
.vs-left {{ display: flex; justify-content: flex-end; }}
.vs-right {{ display: flex; justify-content: flex-start; }}
.vs-bar {{
    height: 36px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    font-weight: 700;
    font-size: 0.95rem;
    padding: 0 16px;
    white-space: nowrap;
    color: {INK};
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.30);
}}
.vs-bar.a {{ background: linear-gradient(90deg, {BLUE}, {TEAL}); justify-content: flex-end; }}
.vs-bar.b {{ background: linear-gradient(90deg, {AMBER}, {CORAL}); justify-content: flex-start; }}
.vs-badge {{
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: {SURFACE};
    border: 2px solid {TEAL};
    color: {WHITE};
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    margin: 0 auto;
}}
</style>
"""


def setup(title):
    """Set the page title and add the styling. Call this first on every page."""
    st.set_page_config(page_title=title, page_icon="🚲", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    top_nav()


def top_nav():
    """Page links in a row at the top right. The first column is empty and pushes them right."""
    _, home, explore, compare, predict = st.columns([6, 1, 1, 1, 1])
    home.page_link("Home.py", label="Home")
    explore.page_link("pages/1_Explore.py", label="Explore")
    compare.page_link("pages/2_Compare.py", label="Compare")
    predict.page_link("pages/3_Predict.py", label="Predict")


def logo_tag():
    """The logo as an image tag the banner holds."""
    data = base64.b64encode(LOGO_FILE.read_bytes()).decode()
    return f'<img src="data:image/svg+xml;base64,{data}">'


def banner(title, subtitle):
    st.markdown(
        f'<div class="banner">{logo_tag()}<div><h1>{title}</h1><p>{subtitle}</p></div></div>',
        unsafe_allow_html=True,
    )


def number_card(label, value, note="", colour=TEAL, hero=False):
    css_class = "card hero" if hero else "card"
    icon = ICONS.get(label, "")
    st.markdown(
        f'<div class="{css_class}" style="border-left-color:{colour}">'
        f'<div class="icon">{icon}</div>'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def notice(text):
    st.markdown(f'<div class="notice">{text}</div>', unsafe_allow_html=True)


def nav_card(title, text):
    st.markdown(f'<div class="nav-card"><h3>{title}</h3><p>{text}</p></div>', unsafe_allow_html=True)


def versus_header(label_a, label_b):
    """The two name tags with VS between them."""
    st.markdown(
        f'<div class="vs-row"><div class="vs-tag a"><span class="letter">A</span>{label_a}</div>'
        f'<div class="vs-mid">VS</div>'
        f'<div class="vs-tag b"><span class="letter">B</span>{label_b}</div></div>',
        unsafe_allow_html=True,
    )


def versus_rows(rows):
    """Butterfly bars. Each row holds: metric name, text A, text B, width A, width B (percent)."""
    html = ""
    for number, (metric, text_a, text_b, width_a, width_b) in enumerate(rows, start=1):
        html += (
            f'<div class="vs-metric">{metric}</div>'
            f'<div class="vs-line">'
            f'<div class="vs-left"><div class="vs-bar a" style="width:{width_a:.0f}%">{text_a}</div></div>'
            f'<div class="vs-badge">{number:02d}</div>'
            f'<div class="vs-right"><div class="vs-bar b" style="width:{width_b:.0f}%">{text_b}</div></div>'
            f'</div>'
        )
    st.markdown(f'<div>{html}</div>', unsafe_allow_html=True)
