"""
app.py — Madame de la Grande Bouche
Consumer-facing Streamlit app.
Upload clothes -> segment -> build wardrobe -> get outfit.
All config lives in .env - users see zero technical details.
"""
import os
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "0"
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
from __future__ import annotations
import os, sys, io, json, base64
import streamlit as st
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import config
import base64 as _b64, os as _os, random as _random

def _load_char():
    p = _os.path.join(_os.path.dirname(__file__), "madame_char.png")
    try:
        with open(p, "rb") as _f: return _b64.b64encode(_f.read()).decode()
    except Exception: return ""
CHAR_B64 = _load_char()
_MQ = ["Darling, fashion is a statement of the soul.", "Every outfit tells a story.", "Style is knowing who you are.", "Dress for the occasion you wish to have.", "A well-chosen outfit is the best armour.", "Confidence is the best accessory."]


# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Madame de la Grande Bouche",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Montserrat:wght@300;400;500;600;700&display=swap');
@keyframes floatChar{0%,100%{transform:translateY(0) rotate(-1deg)}50%{transform:translateY(-12px) rotate(1deg)}}
@keyframes fadeInUp{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(201,160,48,0.2)}50%{box-shadow:0 0 0 10px rgba(201,160,48,0)}}
html,body,[data-testid="stAppViewContainer"]{background:#F5F0E8 !important;color:#2C1F0E !important;}
[data-testid="stHeader"]{background:transparent !important;}
[data-testid="stSidebar"]{display:none !important;}
[data-testid="collapsedControl"]{display:none !important;}
section.main>div{padding-top:0 !important;}
.block-container{padding:0 0 4rem;max-width:100%;background:#F5F0E8 !important;}
[data-testid="stTabsContent"]{background:#F5F0E8 !important;padding:0;}
[data-testid="stVerticalBlock"]{background:transparent !important;}
div[data-testid="column"]{background:transparent !important;}
.hero{background:linear-gradient(160deg,#FFFDF7 0%,#F5F0E8 60%);border-bottom:3px solid #E0D5C0;padding:3rem 4rem 2.5rem;display:flex;align-items:center;justify-content:space-between;gap:2rem;animation:fadeInUp 0.7s ease both;}
.hero-wordmark{font-family:'Playfair Display',serif;font-size:clamp(1.6rem,3vw,2.6rem);font-weight:700;color:#C9A030;line-height:1.15;margin:0 0 0.35rem;}
.hero-sub{font-family:Montserrat,sans-serif;font-size:0.68rem;font-weight:600;letter-spacing:0.32em;text-transform:uppercase;color:#C8A870;margin:0 0 1.25rem;}
.hero-desc{font-family:Montserrat,sans-serif;font-size:0.9rem;color:#5A4A32;line-height:1.8;max-width:480px;margin:0;}
.hero-steps{display:flex;gap:1.5rem;margin-top:1.5rem;flex-wrap:wrap;}
.hero-step{display:flex;align-items:center;gap:0.6rem;font-family:Montserrat,sans-serif;font-size:0.72rem;font-weight:600;color:#8B7050;}
.step-num{width:24px;height:24px;border-radius:50%;background:#EDE7DA;border:2px solid #C8B89A;display:flex;align-items:center;justify-content:center;font-size:0.65rem;color:#C9A030;font-weight:700;flex-shrink:0;transition:all 0.3s;}
.step-num.done{background:#C9A030;color:#fff;border-color:#C9A030;transform:scale(1.1);}
.step-num.active{border-color:#C9A030;color:#C9A030;animation:pulse 2s infinite;}
.content{padding:2.5rem 4rem;animation:fadeInUp 0.5s ease both;}
.sec-title{font-family:'Playfair Display',serif;font-size:1.45rem;font-weight:600;color:#2C1F0E;margin:0 0 0.3rem;line-height:1.2;}
.sec-title em{color:#C9A030;font-style:italic;}
.sec-desc{font-family:Montserrat,sans-serif;font-size:0.88rem;color:#7A6040;line-height:1.75;margin:0 0 1.25rem;}
.eyebrow{font-family:Montserrat,sans-serif;font-size:0.62rem;font-weight:700;letter-spacing:0.22em;text-transform:uppercase;color:#C8A870;margin:1.25rem 0 0.4rem;}
[data-testid="stFileUploader"]{border:2px dashed #C8B89A !important;border-radius:12px !important;background:#FFFDF7 !important;padding:0.5rem !important;transition:all 0.3s;animation:pulse 3s ease-in-out infinite;}
[data-testid="stFileUploader"]:hover{border-color:#C9A030 !important;background:#FDF5E4 !important;}
[data-testid="stFileUploader"] section{background:transparent !important;border:none !important;}
[data-testid="stFileUploader"] label{color:#7A6040 !important;font-family:Montserrat,sans-serif !important;}
.stButton>button{font-family:Montserrat,sans-serif !important;font-size:0.75rem !important;font-weight:700 !important;letter-spacing:0.15em !important;text-transform:uppercase !important;border-radius:6px !important;padding:0.75rem 2rem !important;width:100% !important;transition:all 0.25s !important;}
.stButton>button:not(:disabled){background:linear-gradient(135deg,#C9A030 0%,#A87820 100%) !important;color:#fff !important;border:none !important;box-shadow:0 4px 16px rgba(201,160,48,0.3) !important;}
.stButton>button:not(:disabled):hover{transform:translateY(-2px) !important;box-shadow:0 8px 28px rgba(201,160,48,0.4) !important;}
.stButton>button:disabled{background:#EDE7DA !important;color:#B0A080 !important;border:1px solid #D0C4B0 !important;}
.stTextInput input,.stTextArea textarea{background:#FFFDF7 !important;border:2px solid #D0C4B0 !important;border-radius:6px !important;color:#2C1F0E !important;font-family:Montserrat,sans-serif !important;font-size:0.9rem !important;}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:#C9A030 !important;box-shadow:0 0 0 3px rgba(201,160,48,0.12) !important;}
label{color:#7A6040 !important;font-family:Montserrat,sans-serif !important;font-size:0.82rem !important;font-weight:500 !important;}
.stSelectbox>div>div{background:#FFFDF7 !important;border:2px solid #D0C4B0 !important;border-radius:6px !important;color:#2C1F0E !important;font-family:Montserrat,sans-serif !important;font-size:0.9rem !important;}
.stRadio label{color:#7A6040 !important;font-family:Montserrat,sans-serif !important;font-size:0.85rem !important;}
.stTabs [data-baseweb="tab-list"]{background:#FFFDF7 !important;border-bottom:2px solid #E0D5C0 !important;padding:0 4rem !important;gap:0 !important;}
.stTabs [data-baseweb="tab"]{font-family:Montserrat,sans-serif !important;font-size:0.7rem !important;font-weight:600 !important;letter-spacing:0.16em !important;text-transform:uppercase !important;color:#A09070 !important;padding:0.9rem 1.2rem !important;border-bottom:3px solid transparent !important;background:transparent !important;transition:all 0.2s !important;}
.stTabs [aria-selected="true"]{color:#C9A030 !important;border-bottom-color:#C9A030 !important;background:transparent !important;}
.stProgress [data-testid="stProgressBar"]>div{background:linear-gradient(90deg,#C9A030,#a88535) !important;border-radius:4px !important;}
[data-testid="stImage"] img{border-radius:8px;transition:transform 0.3s;}
[data-testid="stImage"] img:hover{transform:scale(1.02);}
.stExpander{border:1px solid #E0D5C0 !important;border-radius:10px !important;background:#FFFDF7 !important;}
.stExpander summary{font-family:Montserrat,sans-serif !important;font-size:0.8rem !important;color:#8B7050 !important;}
.stCaption{font-family:Montserrat,sans-serif !important;color:#9A8060 !important;}
.stDownloadButton>button{background:transparent !important;border:2px solid #D0C4B0 !important;color:#8B7050 !important;border-radius:6px !important;transition:all 0.2s !important;}
.stDownloadButton>button:hover{border-color:#C9A030 !important;color:#C9A030 !important;background:#FDF5E4 !important;}
.hr{border:none;border-top:1px solid #E0D5C0;margin:1.5rem 0;}
.stat-card{background:#FFFDF7;border:1px solid #E0D5C0;border-radius:10px;padding:1.25rem;text-align:center;transition:all 0.3s;box-shadow:0 2px 8px rgba(201,160,48,0.06);}
.stat-card:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(201,160,48,0.15);}
.stat-num{font-family:'Playfair Display',serif;font-size:1.9rem;color:#C9A030;line-height:1.1;}
.stat-lbl{font-family:Montserrat,sans-serif;font-size:0.65rem;color:#9A8060;text-transform:uppercase;letter-spacing:0.14em;}
.ic-name{font-family:'Playfair Display',serif;font-size:0.9rem;color:#2C1F0E;font-weight:600;text-transform:capitalize;margin-bottom:0.3rem;}
.ic-color{display:flex;align-items:center;gap:6px;margin-bottom:0.4rem;font-family:Montserrat,sans-serif;font-size:0.72rem;color:#7A6040;}
.ic-dot{width:12px;height:12px;border-radius:50%;border:1px solid #C8B89A;flex-shrink:0;}
.ic-badge{display:inline-block;padding:2px 9px;border-radius:12px;margin:2px;font-family:Montserrat,sans-serif;font-size:0.65rem;font-weight:500;background:#F0E8D8;border:1px solid #D0C4B0;color:#6B4F2A;transition:all 0.2s;}
.ic-badge:hover{background:#C9A030;color:#fff;border-color:#C9A030;}
.rec-card{background:linear-gradient(145deg,#FFFDF7 0%,#FDF5E4 100%);border:2px solid rgba(201,160,48,0.3);border-radius:14px;padding:1.75rem 2rem;box-shadow:0 4px 24px rgba(201,160,48,0.1);animation:fadeInUp 0.6s ease both;}
.rec-title{font-family:'Playfair Display',serif;font-size:1.3rem;color:#C9A030;font-weight:600;margin-bottom:0.9rem;}
.rec-row{display:flex;align-items:flex-start;gap:0.7rem;padding:0.6rem 0;border-bottom:1px solid #E8DFD0;font-family:Montserrat,sans-serif;font-size:0.88rem;color:#2C1F0E;line-height:1.5;transition:background 0.2s;border-radius:4px;}
.rec-row:hover{background:#FDF5E4;padding-left:0.4rem;}
.rec-bullet{color:#C9A030;font-size:0.7rem;margin-top:4px;flex-shrink:0;}
.rec-slbl{font-family:Montserrat,sans-serif;font-size:0.62rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#C8A870;margin:1.2rem 0 0.4rem;}
.rec-tip{font-family:Montserrat,sans-serif;font-size:0.86rem;color:#5A4A32;line-height:1.75;background:#FDF5E4;border-left:3px solid #C9A030;padding:0.65rem 0.9rem;border-radius:0 6px 6px 0;}
.rain-alert{background:#FFF8EC;border:1px solid #D4A060;border-radius:6px;padding:0.55rem 0.9rem;font-family:Montserrat,sans-serif;font-size:0.78rem;color:#8B5A20;margin-top:0.75rem;}
.event-tag{display:inline-block;background:#FFF8EC;border:1px solid #D4A060;border-radius:4px;padding:4px 14px;font-family:Montserrat,sans-serif;font-size:0.65rem;font-weight:700;letter-spacing:0.18em;text-transform:uppercase;color:#8B5A20;margin-bottom:0.75rem;}
.wx{display:flex;align-items:center;gap:1.25rem;background:#FFFDF7;border:1px solid #E0D5C0;border-radius:10px;padding:1rem 1.4rem;margin-bottom:1.25rem;box-shadow:0 2px 8px rgba(0,0,0,0.04);}
.wx-temp{font-family:'Playfair Display',serif;font-size:2.2rem;color:#C9A030;line-height:1;}
.wx-city{font-family:Montserrat,sans-serif;font-size:0.8rem;color:#5A4A32;font-weight:500;}
.wx-desc{font-family:Montserrat,sans-serif;font-size:0.72rem;color:#9A8060;margin-top:2px;}
.wx-adv{font-family:Montserrat,sans-serif;font-size:0.7rem;color:#7A6040;margin-left:auto;text-align:right;max-width:200px;line-height:1.6;}
.model-card{background:#FFFDF7;border:1px solid #E0D5C0;border-radius:10px;height:100%;overflow:hidden;transition:all 0.3s;}
.model-card:hover{transform:translateY(-4px);box-shadow:0 12px 32px rgba(201,160,48,0.15);}
.model-card.chosen{border-color:#C9A030;border-width:2px;}
.model-banner{background:linear-gradient(135deg,#C9A030,#A87820);color:#fff;font-family:Montserrat,sans-serif;font-size:0.6rem;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;padding:5px 0;text-align:center;}
.model-body{padding:1.2rem;}
.model-name{font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:600;color:#2C1F0E;margin-bottom:0.15rem;}
.model-sub{font-family:Montserrat,sans-serif;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.1em;color:#A09070;margin-bottom:0.8rem;}
.model-slim{font-family:Montserrat,sans-serif;font-size:0.62rem;text-transform:uppercase;letter-spacing:0.12em;color:#B0A080;margin-bottom:0.3rem;}
.pro-item{font-family:Montserrat,sans-serif;font-size:0.75rem;color:#2A7A4A;padding:2px 0;}
.con-item{font-family:Montserrat,sans-serif;font-size:0.75rem;color:#9A8060;padding:2px 0;}
.pipe-step{display:flex;gap:0.75rem;align-items:flex-start;border-radius:8px;padding:0.65rem 0.9rem;margin-bottom:0.4rem;background:#FFFDF7;border:1px solid #E0D5C0;transition:all 0.25s;}
.pipe-step:hover{background:#FDF5E4;border-color:#C9A030;transform:translateX(4px);}
.pipe-num{font-family:'Playfair Display',serif;font-size:0.95rem;color:#C9A030;font-weight:700;min-width:18px;margin-top:1px;}
.pipe-title{font-family:Montserrat,sans-serif;font-size:0.8rem;color:#2C1F0E;font-weight:600;}
.pipe-desc{font-family:Montserrat,sans-serif;font-size:0.71rem;color:#8B7050;margin-top:2px;line-height:1.5;}
.unavail{max-width:460px;margin:8rem auto;text-align:center;padding:0 2rem;}
.unavail-title{font-family:'Playfair Display',serif;font-size:1.4rem;color:#5A4A32;margin-bottom:0.75rem;}
.unavail-desc{font-family:Montserrat,sans-serif;font-size:0.84rem;color:#8B7050;line-height:1.7;}
.footer{border-top:2px solid #E0D5C0;padding:1.4rem 4rem;margin-top:2rem;display:flex;align-items:center;justify-content:space-between;background:#FFFDF7;}
.footer-brand{font-family:'Playfair Display',serif;font-size:0.85rem;color:#C9A030;}
.footer-uni{font-family:Montserrat,sans-serif;font-size:0.62rem;color:#A09070;letter-spacing:0.12em;text-transform:uppercase;}
.stAlert{background:#FFF8EC !important;border-color:#D4A060 !important;color:#8B5A20 !important;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def md(html: str) -> None:
    st.markdown(html, unsafe_allow_html=True)

def hr() -> None:
    md('<hr class="hr">')

def eyebrow(t: str) -> None:
    md(f'<p class="eyebrow">{t}</p>')

def b64_to_pil(b64: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(b64)))

def item_card(item: dict) -> None:
    name  = item.get("class_name","item").replace("_"," ").title()
    color = item.get("color",{})
    attrs = item.get("attributes",{})
    conf  = item.get("confidence",0)
    badges = "".join(
        f'<span class="ic-badge">{v["label"]}</span>'
        for v in attrs.values()
        if isinstance(v, dict) and v.get("label")
    )
    md(
        f'<div style="background:#0e0e0e;border:1px solid #161616;border-radius:6px;padding:0.75rem">'
        f'<div class="ic-name">{name}</div>'
        f'<div class="ic-color">'
        f'<span class="ic-dot" style="background:{color.get("hex","#888")}"></span>'
        f'{color.get("name","")}</div>'
        f'<div>{badges}</div>'
        f'<div style="font-family:Montserrat,sans-serif;font-size:0.62rem;color:#1e1e1e;'
        f'margin-top:0.35rem">{conf:.0%} confidence</div></div>'
    )

def weather_widget(w: dict, t: dict) -> None:
    icon  = f'<img src="{w["icon_url"]}" width="46" style="filter:brightness(0.85)">' \
            if w.get("icon_url") else '<span style="font-size:2rem;opacity:0.5">🌤️</span>'
    live  = ('<span style="font-size:0.58rem;background:#0c1a10;color:#4aaf7a;'
             'border:1px solid #1a4028;border-radius:10px;padding:1px 7px;'
             'font-family:Montserrat,sans-serif;font-weight:600">LIVE</span>'
             if w.get("live") else "")
    md(
        f'<div class="wx">{icon}'
        f'<div><div class="wx-temp">{w["temp_c"]}°C</div>'
        f'<div class="wx-city">{w["city"]} {live}</div>'
        f'<div class="wx-desc">{w["description"]}</div></div>'
        f'<div class="wx-adv">{w["warmth_advice"]}</div></div>'
    )

def rec_card(rec: dict) -> None:
    rows = "\n".join(
        f'<div class="rec-row"><span class="rec-bullet">◆</span>{p}</div>'
        for p in rec.get("outfit",[])
    )
    rain = rec.get("context",{}).get("weather",{}).get("rain_advice","")
    md(
        f'<div class="rec-card">'
        f'<div class="rec-title">✦ Your Outfit</div>'
        f'{rows}'
        f'<div class="rec-slbl">Why this works</div>'
        f'<div class="rec-tip">{rec.get("reasoning","")}</div>'
        f'<div class="rec-slbl">Styling tips</div>'
        f'<div class="rec-tip">{rec.get("styling_tips","")}</div>'
        f'<div class="rec-slbl">Weather note</div>'
        f'<div class="rec-tip">{rec.get("weather_note","")}</div>'
        + (f'<div class="rain-alert">☂ {rain}</div>' if rain else "")
        + '</div>'
    )

def empty_state(icon: str, msg: str) -> None:
    md(
        f'<div style="display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;padding:5rem 2rem;opacity:0.25">'
        f'<div style="font-size:3rem;margin-bottom:0.9rem">{icon}</div>'
        f'<div style="font-family:Montserrat,sans-serif;font-size:0.82rem;'
        f'color:#777;text-align:center;line-height:1.7">{msg}</div></div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────

_D = {
    "step":             1,
    "wardrobe_items":   [],
    "pipeline_results": [],
    "last_rec":         None,
    "n_analyzed":       0,
}
for _k, _v in _D.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────────────────────
# MODEL LOADING  (cached — runs once)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_models():
    issues = config.validate()
    if issues:
        return None, issues
    try:
        import torch, clip, chromadb, json
        from ultralytics import YOLO
        from pipeline.inference import load_attribute_classifier, init_color_tokens

        device = "cuda" if torch.cuda.is_available() else "cpu"

        id_to_name: dict[int, str] = {}
        if config.ANNOTATION_JSON_PATH and os.path.exists(config.ANNOTATION_JSON_PATH):
            with open(config.ANNOTATION_JSON_PATH) as f:
                ann = json.load(f)
            cats = sorted(ann["categories"], key=lambda x: x["id"])
            id_to_name = {i: c["name"] for i, c in enumerate(cats)}

        yolo = YOLO(config.YOLO_MODEL_PATH)

        clip_model, clip_prep = clip.load("ViT-B/32", device=device)
        clip_model.eval()
        init_color_tokens(clip_model, clip_prep, device)

        attr_model, attr_transform, selected_attrs = load_attribute_classifier(
            config.ATTR_MODEL_PATH, config.ATTR_MAP_PATH, device
        )

        os.makedirs(config.CHROMA_DB_PATH, exist_ok=True)
        client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
        try:
            coll = client.get_collection("wardrobe")
        except Exception:
            coll = client.create_collection("wardrobe", metadata={"hnsw:space": "cosine"})

        return (yolo, clip_model, clip_prep, id_to_name, device,
                coll, attr_model, attr_transform, selected_attrs), []

    except Exception as e:
        return None, [str(e)]


# ─────────────────────────────────────────────────────────────────────────────
# BOOT
# ─────────────────────────────────────────────────────────────────────────────

with st.spinner("\U0001f457 Madame is getting dressed — loading models, please wait…"):
    models_tuple, load_errors = load_models()

if models_tuple is None:
    md("""
    <div class="unavail">
      <div class="unavail-icon">👗</div>
      <div class="unavail-title">Madame is getting dressed</div>
      <div class="unavail-desc">
        The service is temporarily unavailable.<br>
        Please check back shortly or contact the administrator.
      </div>
    </div>
    """)
    if load_errors:
        st.error("Configuration issues: " + " \u00b7 ".join(load_errors))
    st.stop()

(yolo_model, clip_model, clip_preprocess, id_to_name, device,
 chroma_collection, attr_model, attr_transform, selected_attrs) = models_tuple


# ─────────────────────────────────────────────────────────────────────────────
# HERO BANNER
# ─────────────────────────────────────────────────────────────────────────────

step = st.session_state.step
def _sc(n): return "done" if n < step else "active" if n == step else ""

md(f"""
<div class="hero">
  <div>
    <div class="hero-wordmark">Madame de la Grande Bouche</div>
    <div class="hero-sub">AI Fashion Assistant</div>
    <p class="hero-desc">
      Upload photos of your wardrobe. Our AI detects and segments every clothing item,
      analyses colours and attributes, then recommends the perfect outfit for your
      occasion and today's weather.
    </p>
    <div class="hero-steps">
      <div class="hero-step"><div class="step-num {_sc(1)}">1</div>Upload clothes</div>
      <div class="hero-step" style="color:#1e1e1e">›</div>
      <div class="hero-step"><div class="step-num {_sc(2)}">2</div>Review wardrobe</div>
      <div class="hero-step" style="color:#1e1e1e">›</div>
      <div class="hero-step"><div class="step-num {_sc(3)}">3</div>Get your outfit</div>
    </div>
  </div>
  <img src="data:image/png;base64,{CHAR_B64}" style="height:200px;opacity:0.95;flex-shrink:0;filter:drop-shadow(0 8px 32px rgba(201,160,48,0.18));animation:floatChar 4s ease-in-out infinite;">
</div>
""")


# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────

n_items = len(st.session_state.wardrobe_items)
tab1, tab2, tab3, tab4 = st.tabs([
    "📸   Upload",
    f"👚   Wardrobe{f'  ({n_items})' if n_items else ''}",
    "✨   Get Outfit",
    "🔬   About the Model",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — UPLOAD & SEGMENT
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    md('<div class="content">')
    col_up, col_res = st.columns([1, 1.1], gap="large")

    with col_up:
        md('<div class="sec-title">Upload your <em>wardrobe</em></div>')
        md('<p class="sec-desc">Take photos of individual outfits or flat-lays. '
           'Good lighting and an unobstructed view give the best results. '
           'You can upload multiple photos at once.</p>')

        files = st.file_uploader(
            "Drop photos here, or click to browse",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True,
            label_visibility="visible",
        )

        if files:
            # thumbnail preview
            tcols = st.columns(min(len(files), 5))
            for col, f in zip(tcols, files[:5]):
                with col:
                    f.seek(0)
                    st.image(Image.open(f), use_container_width=True)
                    st.caption(f.name[:14] + ("…" if len(f.name)>14 else ""))
            if len(files) > 5:
                st.caption(f"+ {len(files)-5} more selected")

            hr()

            if st.button(f"🔍  Analyse {len(files)} Photo{'s' if len(files)>1 else ''}",
                         use_container_width=True):
                from pipeline.inference import run_pipeline

                prog   = st.progress(0.0)
                status = st.empty()
                new_results: list[dict] = []
                new_items:   list[dict] = []

                for i, uf in enumerate(files):
                    status.markdown(
                        f'<p style="font-family:Montserrat,sans-serif;font-size:0.8rem;'
                        f'color:#444;margin:0.25rem 0">Analysing '
                        f'<strong style="color:#888">{uf.name}</strong>…</p>',
                        unsafe_allow_html=True,
                    )
                    uf.seek(0)
                    result = run_pipeline(
                        image_pil         = Image.open(uf).convert("RGB"),
                        yolo_model        = yolo_model,
                        clip_model        = clip_model,
                        clip_preprocess   = clip_preprocess,
                        id_to_name        = id_to_name,
                        device            = device,
                        chroma_collection = chroma_collection,
                        attr_model        = attr_model,
                        attr_transform    = attr_transform,
                        selected_attrs    = selected_attrs or [],
                        conf_threshold    = config.CONF_THRESHOLD,
                        iou_threshold     = config.IOU_THRESHOLD,
                    )
                    result["filename"] = uf.name
                    new_results.append(result)
                    if result["segmentable"]:
                        new_items.extend(result["items"])
                    prog.progress((i+1)/len(files))

                st.session_state.pipeline_results.extend(new_results)
                st.session_state.wardrobe_items.extend(new_items)
                st.session_state.n_analyzed += len(files)

                prog.empty(); status.empty()

                ok_n   = sum(1 for r in new_results if r["segmentable"])
                item_n = len(new_items)
                skip_n = len(new_results) - ok_n

                if item_n:
                    st.session_state.step = max(st.session_state.step, 2)
                    st.success(
                        f"✓  Found **{item_n} clothing item{'s' if item_n!=1 else ''}** "
                        f"across {ok_n} photo{'s' if ok_n!=1 else ''}."
                        + (f" {skip_n} photo(s) skipped — clothes weren't clearly visible." if skip_n else "")
                    )
                else:
                    st.warning("No clothing items detected. Try photos with clear, well-lit garments.")

        else:
            md("""
            <div style="background:#0e0e0e;border:1px solid #161616;border-radius:8px;
                        padding:1.5rem;margin-top:0.75rem">
              <div style="font-family:Montserrat,sans-serif;font-size:0.62rem;font-weight:700;
                          letter-spacing:0.2em;text-transform:uppercase;color:#3a3020;
                          margin-bottom:0.75rem">Tips for best results</div>
              <div style="font-family:Montserrat,sans-serif;font-size:0.82rem;
                          color:#888;line-height:2.2">
                <span style="color:#C9A84C;font-weight:700">—</span>&nbsp; Shoot in natural daylight<br>
                <span style="color:#C9A84C;font-weight:700">—</span>&nbsp; Lay clothes flat or hang them up<br>
                <span style="color:#C9A84C;font-weight:700">—</span>&nbsp; Avoid heavy shadows or cropped garments<br>
                <span style="color:#C9A84C;font-weight:700">—</span>&nbsp; Upload multiple photos at once to build your wardrobe<br>
                <span style="color:#C9A84C;font-weight:700">—</span>&nbsp; You can always upload more later
              </div>
            </div>
            """)

        if st.session_state.wardrobe_items:
            hr()
            if st.button("🗑️  Clear wardrobe & start over", use_container_width=True):
                try:
                    ids = chroma_collection.get()["ids"]
                    if ids: chroma_collection.delete(ids=ids)
                except Exception:
                    pass
                for k, v in _D.items():
                    st.session_state[k] = v
                st.rerun()

    with col_res:
        if not st.session_state.pipeline_results:
            empty_state("🔍", "Segmentation results will appear here<br>after you analyse your photos.")
        else:
            md('<div class="sec-title">Segmentation <em>results</em></div>')
            md('<p class="sec-desc">YOLOv26s detected and outlined each clothing item. '
               'CLIP extracted embeddings for retrieval.</p>')

            for res in reversed(st.session_state.pipeline_results[-6:]):
                fname = res.get("filename","photo")
                if not res["segmentable"]:
                    st.warning(f"**{fname}** — {res['reason']}")
                    continue
                n = len(res["items"])
                with st.expander(f"✓  {fname}  ·  {n} item{'s' if n!=1 else ''}", expanded=(n>0)):
                    if res.get("annotated_image"):
                        st.image(res["annotated_image"], use_container_width=True,
                                 caption="Items detected by YOLOv26s")
                    if res["items"]:
                        eyebrow("Detected items")
                        ic = st.columns(min(n,3), gap="small")
                        for col, it in zip(ic, res["items"][:3]):
                            with col:
                                if it.get("crop_b64"):
                                    st.image(b64_to_pil(it["crop_b64"]), use_container_width=True)
                                item_card(it)
                        if n > 3:
                            st.caption(f"+ {n-3} more items in the Wardrobe tab")
    md('</div>')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — WARDROBE
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    md('<div class="content">')
    items = st.session_state.wardrobe_items

    if not items:
        empty_state("👗", "Your wardrobe is empty.<br>Upload photos in the Upload tab to get started.")
    else:
        cats: dict[str,int] = {}
        for it in items:
            c = it["class_name"]; cats[c] = cats.get(c,0)+1

        # stats
        sc = st.columns(3, gap="small")
        for col, (icon,val,lbl) in zip(sc, [
            ("👔", len(items),                   "Clothing items"),
            ("🏷️", len(cats),                    "Categories found"),
            ("📸", st.session_state.n_analyzed,  "Photos analysed"),
        ]):
            with col:
                md(f'<div class="stat-card"><div style="font-size:1.2rem">{icon}</div>'
                   f'<div class="stat-num">{val}</div>'
                   f'<div class="stat-lbl">{lbl}</div></div>')

        hr()

        # category bar chart
        md('<div class="sec-title">What\'s in your <em>wardrobe?</em></div>')
        sorted_cats = sorted(cats.items(), key=lambda x: -x[1])
        total = len(items)
        bars = "".join(
            f'<div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.42rem">'
            f'<div style="font-family:Montserrat,sans-serif;font-size:0.74rem;color:#666;'
            f'width:160px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'
            f'text-transform:capitalize">{cn}</div>'
            f'<div style="flex:1;background:#161616;border-radius:2px;height:5px">'
            f'<div style="width:{cnt/total*100:.1f}%;background:'
            f'{"#C9A84C" if cnt/total>0.20 else "#7a6030" if cnt/total>0.10 else "#3a2a18"}'
            f';height:5px;border-radius:2px"></div></div>'
            f'<div style="font-family:Montserrat,sans-serif;font-size:0.68rem;color:#333;width:20px;'
            f'text-align:right">{cnt}</div></div>'
            for cn, cnt in sorted_cats
        )
        md(f'<div style="background:#0e0e0e;border:1px solid #161616;border-radius:8px;'
           f'padding:1rem 1.25rem;max-height:220px;overflow-y:auto;margin-bottom:1.5rem">{bars}</div>')

        # filter + sort
        fc = st.columns([2,1,1], gap="small")
        with fc[0]:
            cat_opts = ["All categories"] + [c for c,_ in sorted_cats]
            sel_cat  = st.selectbox("Filter", cat_opts, label_visibility="collapsed")
        with fc[1]:
            sort_opt = st.selectbox("Sort", ["Confidence","Category","Colour"],
                                    label_visibility="collapsed")
        with fc[2]:
            view = st.radio("View", ["Grid","List"], horizontal=True,
                            label_visibility="collapsed")

        filtered = items if sel_cat=="All categories" else [i for i in items if i["class_name"]==sel_cat]
        if sort_opt=="Confidence": filtered = sorted(filtered, key=lambda x: -x.get("confidence",0))
        elif sort_opt=="Category": filtered = sorted(filtered, key=lambda x: x.get("class_name",""))
        else:                      filtered = sorted(filtered, key=lambda x: x.get("color",{}).get("name",""))

        md(f'<p style="font-family:Montserrat,sans-serif;font-size:0.7rem;color:#2a2a2a;'
           f'margin:0.2rem 0 1rem">Showing {len(filtered)} of {len(items)} items</p>')

        if view == "Grid":
            for row_start in range(0, len(filtered), 4):
                gcols = st.columns(4, gap="small")
                for col, it in zip(gcols, filtered[row_start:row_start+4]):
                    with col:
                        if it.get("crop_b64"):
                            st.image(b64_to_pil(it["crop_b64"]), use_container_width=True)
                        item_card(it)
        else:
            for it in filtered:
                lc = st.columns([1,4], gap="small")
                with lc[0]:
                    if it.get("crop_b64"):
                        st.image(b64_to_pil(it["crop_b64"]), use_container_width=True)
                with lc[1]:
                    name   = it.get("class_name","").replace("_"," ").title()
                    color  = it.get("color",{})
                    attrs  = it.get("attributes",{})
                    badges = "".join(
                        f'<span class="ic-badge">{v["label"]}</span>'
                        for v in attrs.values() if isinstance(v,dict) and v.get("label")
                    )
                    md(
                        f'<div style="padding:0.2rem 0">'
                        f'<div style="font-family:\'Playfair Display\',serif;font-size:1rem;'
                        f'color:#ccc;margin-bottom:0.25rem">{name}</div>'
                        f'<div class="ic-color"><span class="ic-dot" style="background:'
                        f'{color.get("hex","#888")}"></span>{color.get("name","")}</div>'
                        f'<div>{badges}</div>'
                        f'<div style="font-family:Montserrat,sans-serif;font-size:0.65rem;'
                        f'color:#1e1e1e;margin-top:0.3rem">'
                        f'{it.get("confidence",0):.0%} confidence</div></div>'
                    )
                hr()

    md('</div>')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GET OUTFIT
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    md('<div class="content">')

    if not st.session_state.wardrobe_items:
        empty_state("✨", "Upload your clothes first, then come back here<br>for a personalised outfit recommendation.")
    else:
        fc, rc = st.columns([1, 1.4], gap="large")

        with fc:
            md('<div class="sec-title">Tell us about <em>your day</em></div>')
            md('<p class="sec-desc">We\'ll match your wardrobe to your occasion and today\'s weather.</p>')

            city_val = st.text_input("📍 Your city", value="Beirut",
                                     placeholder="e.g. Paris, London, Dubai…")

            EVENT_OPTS = [
                "👔  Business meeting",   "☕  Casual day out",
                "🌹  First date",         "🎓  University / lecture",
                "💪  Gym workout",        "🏖️  Beach day",
                "🍽️  Evening dinner",     "🎉  Party / social event",
                "✈️  Travel / commute",   "🏠  Work from home",
                "📸  Outdoor photoshoot", "✏️  Something else…",
            ]
            event_sel = st.selectbox("📅 What are you doing?", EVENT_OPTS)
            if event_sel.startswith("✏️"):
                event_val = st.text_input("Describe it", placeholder="hiking, gallery opening…")
            else:
                event_val = event_sel[3:].strip()

            notes_val = st.text_area(
                "💬 Style preferences *(optional)*",
                placeholder="e.g. I prefer dark colours · want to look smart but relaxed…",
                height=90,
            )

            if not config.OPENWEATHER_API_KEY:
                st.info("ℹ️ No weather key — weather will be estimated. Add OPENWEATHER_API_KEY to .env for live data.")

            hr()

            can_rec = bool(event_val and config.GROQ_API_KEY)
            get_btn = st.button("✨  Get My Outfit", use_container_width=True, disabled=not can_rec)
            if not can_rec and not config.GROQ_API_KEY:
                md('<p style="font-family:Montserrat,sans-serif;font-size:0.72rem;'
                   'color:#2a2a2a;text-align:center;margin-top:0.4rem">'
                   'Recommendation service unavailable — contact administrator.</p>')

        with rc:
            md('<div class="sec-title">Your personalised <em>recommendation</em></div>')
            md('<p class="sec-desc">Madame reviews your wardrobe, checks the weather, '
               'and selects the best outfit for your occasion.</p>')

            if get_btn and can_rec:
                with st.spinner("Madame is reviewing your wardrobe…"):
                    try:
                        from groq import Groq
                        from pipeline.recommendation import (
                            build_context, retrieve_wardrobe_items, get_groq_recommendation
                        )
                        groq_client = Groq(api_key=config.GROQ_API_KEY)
                        context     = build_context(city_val, event_val, notes_val,
                                                    config.OPENWEATHER_API_KEY)
                        grouped     = retrieve_wardrobe_items(
                            chroma_collection, clip_model, clip_preprocess,
                            context, device, n_per_category=3
                        )
                        rec = get_groq_recommendation(groq_client, context, grouped)
                        st.session_state.last_rec = rec
                        st.session_state.step = 3
                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

            rec = st.session_state.last_rec

            if rec:
                ctx = rec.get("context",{})
                w   = ctx.get("weather",{})
                t   = ctx.get("time",{})

                md(f'<div class="event-tag">{ctx.get("event","")}</div>')
                weather_widget(w, t)
                rec_card(rec)

                _q = _random.choice(_MQ)
                st.markdown(f'<div style="font-family:Playfair Display,serif;font-style:italic;font-size:0.9rem;color:#C9A030;text-align:center;padding:1rem 1.5rem;background:#FFF8EC;border-radius:10px;margin-top:1rem;border:1px solid rgba(201,160,48,0.25)">&#10022; {_q} &#10022;</div>', unsafe_allow_html=True)

                # selected item crops
                rec_ids   = set(rec.get("recommended_ids",[]))
                rec_items = [i for i in rec.get("all_items",[])
                             if i.get("item_id") in rec_ids and i.get("crop_b64")]
                if rec_items:
                    eyebrow("Selected pieces from your wardrobe")
                    rc2 = st.columns(min(len(rec_items),5), gap="small")
                    for col, it in zip(rc2, rec_items):
                        with col:
                            st.image(b64_to_pil(it["crop_b64"]), use_container_width=True)
                            md(f'<div style="font-family:Montserrat,sans-serif;font-size:0.68rem;'
                               f'color:#444;text-align:center;margin-top:0.2rem;'
                               f'text-transform:capitalize">{it.get("class_name","")}<br>'
                               f'<span style="color:#2e2e2e">{it.get("color_name","")}</span></div>')

                # not-selected items
                other = [i for i in rec.get("all_items",[])
                         if i.get("item_id") not in rec_ids and i.get("crop_b64")]
                if other:
                    with st.expander(f"Other wardrobe items considered ({len(other)} not selected)", expanded=False):
                        oc = st.columns(min(len(other),8), gap="small")
                        for col, it in zip(oc, other[:8]):
                            with col:
                                st.image(b64_to_pil(it["crop_b64"]), use_container_width=True)
                                st.caption(it.get("class_name","").replace("_"," ").title())

                hr()
                st.download_button(
                    label="⬇  Save recommendation as JSON",
                    data=json.dumps({
                        "outfit":       rec.get("outfit"),
                        "reasoning":    rec.get("reasoning"),
                        "styling_tips": rec.get("styling_tips"),
                        "weather_note": rec.get("weather_note"),
                        "context": {
                            "event":  ctx.get("event"),
                            "city":   w.get("city"),
                            "temp_c": w.get("temp_c"),
                            "date":   t.get("date"),
                        },
                    }, indent=2),
                    file_name="my_outfit.json", mime="application/json",
                    use_container_width=True,
                )
            elif not get_btn:
                empty_state("✦", "Fill in the form and click<br><em>Get My Outfit</em>")

    md('</div>')


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ABOUT THE MODEL
# ══════════════════════════════════════════════════════════════════════════════

with tab4:
    md('<div class="content">')

    # hero
    st.markdown("""
    <div style="background:linear-gradient(145deg,#111 0%,#130f08 100%);
                border:1px solid #C9A84C22;border-radius:12px;padding:2rem 2.25rem;margin-bottom:2rem">
      <div style="font-family:Montserrat,sans-serif;font-size:0.6rem;font-weight:700;
                  letter-spacing:0.22em;text-transform:uppercase;color:#3a2e18;margin-bottom:0.4rem">
        Powering this app</div>
      <div style="font-family:'Playfair Display',serif;font-size:2rem;color:#C9A84C;
                  font-weight:700;line-height:1.1;margin-bottom:0.75rem">YOLOv26s-seg</div>
      <div style="font-family:Montserrat,sans-serif;font-size:0.87rem;color:#666;line-height:1.8">
        Fine-tuned on the <strong style="color:#aaa">Fashionpedia dataset</strong> for instance
        segmentation of clothing items. Selected after a comparison of three models.
      </div>
      <div style="margin-top:1.25rem;display:flex;gap:2rem;flex-wrap:wrap">
        <div>
          <div style="font-family:Montserrat,sans-serif;font-size:0.6rem;color:#3a2e18;
                      text-transform:uppercase;letter-spacing:0.14em">Task</div>
          <div style="font-family:Montserrat,sans-serif;font-size:0.82rem;color:#aaa;margin-top:2px">
            Instance segmentation</div></div>
        <div>
          <div style="font-family:Montserrat,sans-serif;font-size:0.6rem;color:#3a2e18;
                      text-transform:uppercase;letter-spacing:0.14em">Dataset</div>
          <div style="font-family:Montserrat,sans-serif;font-size:0.82rem;color:#aaa;margin-top:2px">
            Fashionpedia (cleaned subset — 22 classes)</div></div>
        <div>
          <div style="font-family:Montserrat,sans-serif;font-size:0.6rem;color:#3a2e18;
                      text-transform:uppercase;letter-spacing:0.14em">University</div>
          <div style="font-family:Montserrat,sans-serif;font-size:0.82rem;color:#aaa;margin-top:2px">
            Lebanese University · Department of Data Science</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


    hr()


    # full pipeline
    lc, rc2 = st.columns([1, 1], gap="large")

    with lc:
        st.markdown("""
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;color:#ddd;
                    font-weight:600;margin:0 0 0.35rem">The full <em>pipeline</em></div>
        <p style="font-family:Montserrat,sans-serif;font-size:0.82rem;color:#484848;
                   line-height:1.7;margin:0 0 1rem">
          Every component was trained or configured specifically for fashion understanding.
        </p>
        """, unsafe_allow_html=True)

        for num, title, desc, bg, bdr in [
            ("1","Image upload",        "User submits a wardrobe photo",
             "#161616","#222"),
            ("2","Segmentability gate", "Confidence + area check — rejects occluded images",
             "#181408","#C9A84C33"),
            ("3","YOLOv26s inference",  "Detects and segments every clothing item (your model)",
             "#130f08","#C9A84C77"),
            ("4","Crop extraction",     "Each item cropped with 5% padding",
             "#161616","#222"),
            ("5","Dominant colour",     "K-Means on mask-filtered pixels per crop",
             "#161616","#222"),
            ("6","EfficientNet-B0",     "Your trained attribute classifier: textile pattern, length, neckline…",
             "#0d1208","#2a4a2255"),
            ("7","CLIP ViT-B/32",       "512-dim embedding stored in ChromaDB for retrieval",
             "#161616","#222"),
            ("8","Context + retrieval", "Weather API + CLIP text => category-balanced top-K items",
             "#161616","#222"),
            ("9","Groq Llama 3.3 70B",  "Reasons across items + context => structured recommendation",
             "#0d1a12","#1f5c3555"),
        ]:
            st.markdown(
                f'<div class="pipe-step" style="background:{bg};border:1px solid {bdr}">'
                f'<div class="pipe-num">{num}</div>'
                f'<div><div class="pipe-title">{title}</div>'
                f'<div class="pipe-desc">{desc}</div></div></div>',
                unsafe_allow_html=True,
            )

    with rc2:
        st.markdown("""
        <div style="font-family:'Playfair Display',serif;font-size:1.35rem;color:#ddd;
                    font-weight:600;margin:0 0 0.35rem">Fashionpedia <em>classes</em></div>
        <p style="font-family:Montserrat,sans-serif;font-size:0.82rem;color:#484848;
                   line-height:1.7;margin:0 0 0.75rem">
          22 clothing categories from the cleaned Fashionpedia ontology.
        </p>
        """, unsafe_allow_html=True)

        class_list = sorted(id_to_name.values()) if id_to_name else [
            "shirt, blouse","top, t-shirt, sweatshirt","sweater","cardigan","vest",
            "jacket","coat","pants","shorts","skirt","tights, stockings",
            "dress","jumpsuit","shoe","glasses","hat",
            "headband, head covering, hair accessory","tie","glove","belt","scarf","bag, wallet",
        ]
        tags = "".join(
            f'<span style="display:inline-block;padding:3px 10px;margin:3px 2px;border-radius:12px;'
            f'font-family:Montserrat,sans-serif;font-size:0.72rem;font-weight:500;'
            f'background:#141414;border:1px solid #1e1e1e;color:#7a6840;'
            f'text-transform:capitalize">{c.replace("_"," ")}</span>'
            for c in class_list
        )
        st.markdown(
            f'<div style="background:#0e0e0e;border:1px solid #161616;border-radius:8px;'
            f'padding:1rem 1.1rem;line-height:2.2;margin-bottom:1.25rem">{tags}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("""
        <div style="font-family:'Playfair Display',serif;font-size:1.1rem;color:#ddd;
                    font-weight:600;margin:0 0 0.5rem">Attribute <em>classifier</em>
          <span style="font-family:Montserrat,sans-serif;font-size:0.68rem;
                       color:#3a3020;font-weight:400;font-style:normal;
                       margin-left:0.5rem">EfficientNet-B0 · trained on Fashionpedia</span>
        </div>
        <p style="font-family:Montserrat,sans-serif;font-size:0.8rem;color:#484848;
                   line-height:1.7;margin:0 0 0.75rem">
          A fine-tuned multi-label classifier predicts the best attribute per group for each crop.
        </p>
        """, unsafe_allow_html=True)

        for attr, vals in [
            ("Textile pattern", "plain, floral, abstract, camouflage, stripe…"),
            ("Length",          "mini, midi, maxi, above-knee, full-length…"),
            ("Neckline type",   "v-neck, crew, collarless, off-shoulder…"),
            ("Silhouette",      "flare, peplum, circle, straight, bodycon…"),
            ("Opening type",    "zip-up, single breasted, pull-over…"),
            ("Waistline",       "high waist, low waist, natural waist…"),
        ]:
            st.markdown(
                f'<div style="display:flex;gap:0.75rem;padding:0.4rem 0;border-bottom:1px solid #141414">'
                f'<div style="font-family:Montserrat,sans-serif;font-size:0.73rem;font-weight:600;'
                f'color:#C9A84C;min-width:120px">{attr}</div>'
                f'<div style="font-family:Montserrat,sans-serif;font-size:0.71rem;color:#3e3e3e">'
                f'{vals}</div></div>',
                unsafe_allow_html=True,
            )

    hr()

    # project info
    st.markdown("""
    <div style="font-family:'Playfair Display',serif;font-size:1.35rem;color:#ddd;
                font-weight:600;margin:0 0 1rem">About this <em>project</em></div>
    """, unsafe_allow_html=True)

    ab1, ab2 = st.columns([2,1], gap="large")
    with ab1:
        st.markdown("""
        <div style="font-family:Montserrat,sans-serif;font-size:0.87rem;color:#555;line-height:1.9">
          <strong style="color:#aaa">Madame de la Grande Bouche</strong> is a Final Year Project
          at the Lebanese University, Department of Data Science.<br><br>
          The project builds an end-to-end AI pipeline that segments clothing items from wardrobe
          photos, extracts style attributes, and recommends context-aware outfits based on
          real-time weather and daily agenda — inspired by the animated wardrobe character from Beauty and the Beast.<br><br>
          Three segmentation models were trained and evaluated on a cleaned subset of Fashionpedia.
          The best-performing model (YOLOv26s) powers this app alongside a trained EfficientNet-B0
          attribute classifier, CLIP embeddings in ChromaDB, and Llama 3.3 70B for the final
          Retrieval-Augmented Generation recommendation.
        </div>
        """, unsafe_allow_html=True)
    with ab2:
        st.markdown('<div style="background:#0e0e0e;border:1px solid #161616;border-radius:8px;padding:1.25rem">',
                    unsafe_allow_html=True)
        st.markdown('<div style="font-family:Montserrat,sans-serif;font-size:0.6rem;color:#3a2e18;'
                    'text-transform:uppercase;letter-spacing:0.18em;margin-bottom:0.75rem">Project info</div>',
                    unsafe_allow_html=True)
        for lbl, val in [
            ("Institution","Lebanese University"),
            ("Department", "Data Science"),
            ("Year",       "2025 – 2026"),
            ("Supervisors","Romy Bou Abdo · Ismail Khodr Kattar"),
            ("Students",   "Julie El Hajj · Lucas Joumaa"),
            ("Dataset",    "Fashionpedia (22 classes)"),
            ("Trained",    "Mask R-CNN, YOLOv8s, YOLOv26s"),
            ("Chosen",     "YOLOv26s-seg"),
            ("Attributes", "EfficientNet-B0 (fine-tuned)"),
            ("Embeddings", "CLIP ViT-B/32"),
            ("Vector DB",  "ChromaDB cosine similarity"),
            ("LLM",        "Llama 3.3 70B via Groq"),
        ]:
            st.markdown(
                f'<div style="display:flex;gap:0.5rem;padding:0.28rem 0;border-bottom:1px solid #121212">'
                f'<div style="font-family:Montserrat,sans-serif;font-size:0.67rem;color:#242424;'
                f'min-width:90px;flex-shrink:0">{lbl}</div>'
                f'<div style="font-family:Montserrat,sans-serif;font-size:0.7rem;color:#4a4a4a">'
                f'{val}</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    md('</div>')


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────

md("""
<div class="footer">
  <div class="footer-brand">Madame de la Grande Bouche</div>
  <div class="footer-uni">Lebanese University · FYP · Department of Data Science</div>
</div>
""")
