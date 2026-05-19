import sys
import asyncio

# Fix NotImplementedError in Windows when using Playwright + Streamlit
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
import plotly.graph_objects as go
from scraper import get_pln_tariffs, get_bbm_price
from agent import EnergyTransitAgent

# --- Compatibility Helpers for older Streamlit versions ---
def safe_cache_data(*args, **kwargs):
    if hasattr(st, "cache_data"):
        return st.cache_data(*args, **kwargs)
    return st.experimental_memo(*args, **kwargs)

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# --- Setup API Key ---
import os
DEFAULT_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

# ─── Konfigurasi halaman ──────────────────────────────────────────────
from PIL import Image
from pathlib import Path

try:
    logo_path = Path(__file__).parent / "asset" / "LogoGreenSwitch-1.png"
    favicon = Image.open(logo_path) if logo_path.exists() else "⚡"
except Exception:
    favicon = "⚡"

st.set_page_config(
    page_title="GreenSwitch — AI Agent Transisi Energi",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="collapsed", # Sembunyikan sidebar secara default
)


# Force parent window (main Streamlit frame) to light mode to bypass Chrome's Auto Dark Mode
import streamlit.components.v1 as components
components.html(
    """
    <script>
        const parentDoc = window.parent.document;
        // Inject meta tag
        if (!parentDoc.querySelector('meta[name="color-scheme"]')) {
            const meta = parentDoc.createElement('meta');
            meta.name = "color-scheme";
            meta.content = "only light";
            parentDoc.head.appendChild(meta);
        }
        // Inject style tag to force light color-scheme
        if (!parentDoc.querySelector('#force-light-style')) {
            const style = parentDoc.createElement('style');
            style.id = 'force-light-style';
            style.innerHTML = ':root { color-scheme: only light !important; }';
            parentDoc.head.appendChild(style);
        }
    </script>
    """,
    height=0,
    width=0,
)

# ─── CSS KUSTOM (Meniru Tailwind dari React) ──────────────────────────
st.markdown("""
<style>
    /* Sembunyikan tombol expand sidebar bawaan Streamlit agar terasa seperti web app murni */
    [data-testid="collapsedControl"] { display: none; }
    
    /* Global Background & Fonts */
    .stApp { 
        background: radial-gradient(ellipse at top right, #ecfdf5 0%, #f0fdf4 50%, #f0f9ff 100%); 
        color: #1f2937; 
    }
    
    /* ─── TWEAK NATIVE STREAMLIT COMPONENT MENGGUNAKAN GAYA TAILWIND ─── */
    
    /* Sembunyikan Header/Footer bawaan & Kurangi jarak atas */
    header[data-testid="stHeader"] { background: transparent !important; height: 0px !important; }
    footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
    
    /* Form Inputs (Selectbox & NumberInput) -> bergaya bg-gray-50 rounded-2xl */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div {
        background-color: #f9fafb !important;
        border-radius: 1rem !important;
        border: 1px solid #e5e7eb !important;
        font-weight: 600 !important;
        color: #1f2937 !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    
    /* Hanya berikan padding kustom pada input (number/text), bukan selectbox agar teks tidak terpotong */
    div[data-baseweb="input"] > div {
        padding: 0.3rem 0.5rem !important;
    }
    
    /* Focus State Input -> ring-emerald-500 */
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="input"] > div:focus-within {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15) !important;
    }

    /* Labels Input */
    .stSelectbox label, .stNumberInput label, .stSlider label, .stTextInput label {
        font-weight: 800 !important;
        color: #374151 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Buttons -> bergaya gradient emerald rounded-xl shadow-lg */
    .stButton, .stFormSubmitButton, div[data-testid="stButton"], div[data-testid="stFormSubmitButton"] {
        width: 100% !important;
    }
    .stButton button, .stFormSubmitButton button {
        background: linear-gradient(to right, #059669, #047857) !important;
        color: white !important;
        border-radius: 1rem !important;
        font-weight: 800 !important;
        padding: 0.6rem 2rem !important;
        border: none !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.3) !important;
        color: white !important;
        border: none !important;
    }
    .stButton button:active, .stFormSubmitButton button:active {
        transform: translateY(0) !important;
    }

    /* Slider -> Emerald */
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: #10b981 !important;
        border: 2px solid white !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
    }
    
    /* ────────────────────────────────────────────────────────────────── */
    
    /* Navbar Styling */
    .modern-navbar { 
        background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(10px); 
        border: 1px solid rgba(255, 255, 255, 0.4); padding: 1rem 2rem; 
        border-radius: 24px; display: flex; justify-content: space-between; 
        align-items: center; margin-bottom: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        max-width: 100%; margin-left: auto; margin-right: auto;
    }
    :root { color-scheme: only light !important; }
    .navbar-brand { font-size: 1.8rem !important; font-weight: 900 !important; color: #064e3b !important; margin: 0 !important; }
    .navbar-badge { background: linear-gradient(to right, #d1fae5, #a7f3d0) !important; color: #065f46 !important; padding: 0.5rem 1rem !important; border-radius: 999px !important; font-size: 0.75rem !important; font-weight: 800 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; border: 1px solid rgba(16, 185, 129, 0.2) !important; }

    /* Centered Container for Forms and Results */
    .center-container {
        max-width: 1000px;
        margin: 0 auto;
    }

    /* Hero Card Style (Streamlit Native Columns via CSS hack) */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(.step0-active) {
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 2.5rem !important;
        border: 1px solid white !important;
        padding: 1.5rem 5rem 3.5rem 5rem !important;
        box-shadow: 0 25px 50px -12px rgba(6, 78, 59, 0.05) !important;
        margin-top: 0 !important;
        margin-bottom: 2rem !important;
        min-height: 440px !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .glow-circle {
        position: absolute !important;
        top: -120px !important;
        right: -120px !important;
        width: 380px !important;
        height: 380px !important;
        background: rgba(52, 211, 153, 0.15) !important;
        border-radius: 50% !important;
        filter: blur(80px) !important;
        pointer-events: none !important;
        z-index: 1 !important;
    }
    
    .hero-left-col {
        max-width: 520px !important;
        position: relative !important;
        z-index: 2 !important;
    }
    
    .hero-right-col {
        position: relative !important;
        z-index: 2 !important;
    }

    .ai-badge {
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 6px 16px !important;
        background: #e8fbf2 !important;
        color: #047857 !important;
        border-radius: 99px !important;
        font-size: 0.75rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.1em !important;
        margin-bottom: 0.8rem !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        width: fit-content !important;
    }

    .hero-title-react {
        font-size: 2.8rem !important;
        font-weight: 950 !important;
        color: #111827 !important;
        line-height: 1.15 !important;
        margin-bottom: 0.6rem !important;
        margin-top: 0 !important;
        letter-spacing: -0.02em !important;
    }

    .gradient-text {
        background: linear-gradient(to right, #10b981, #069669) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    .hero-desc-react {
        color: #6b7280 !important;
        font-size: 1.125rem !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
        margin-bottom: 1.6rem !important;
        margin-top: 0 !important;
    }

    /* Native Button Styling inside Step 0 */
    div[data-testid="stVerticalBlock"]:has(.step0-active) .stButton button {
        background: linear-gradient(to right, #10b981, #059669) !important;
        color: white !important;
        border: none !important;
        padding: 1.1rem 2.8rem !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        border-radius: 1.25rem !important;
        box-shadow: 0 10px 25px -5px rgba(5, 150, 105, 0.4) !important;
        transition: all 0.3s ease !important;
        width: auto !important;
        display: inline-block !important;
        margin-top: 0.5rem !important;
    }
    div[data-testid="stVerticalBlock"]:has(.step0-active) .stButton button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 15px 30px -5px rgba(5, 150, 105, 0.5) !important;
    }

    @media (max-width: 768px) {
        div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(.step0-active) {
            padding: 2.5rem 2rem !important;
            min-height: auto !important;
        }
        .hero-title-react {
            font-size: 2.2rem !important;
        }
    }

    /* Hero Circle Graphic & Badges */
    .hero-circle {
        width: 320px;
        height: 320px;
        background: linear-gradient(135deg, #f0fdf4 0%, #d1fae5 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        border: 10px solid white;
        box-shadow: 0 20px 40px rgba(16, 185, 129, 0.12);
        margin: 0 auto;
    }
    .floating-badge {
        position: absolute;
        background: white;
        padding: 12px;
        border-radius: 1rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        font-size: 1.5rem;
        animation: bounce 3s infinite;
        border: 1px solid rgba(229, 231, 235, 0.5);
    }
    .badge-top {
        top: 30px;
        right: 15px;
        animation-delay: 0.5s;
    }
    .badge-bottom {
        bottom: 50px;
        left: 15px;
    }
    @keyframes bounce {
        0%, 100% {
            transform: translateY(0);
        }
        50% {
            transform: translateY(-8px);
        }
    }

    /* Form Card */
    .form-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 2.5rem;
        border: 1px solid white;
        padding: 3rem;
        box-shadow: 0 25px 50px -12px rgba(5, 150, 105, 0.05);
        margin-bottom: 2rem;
    }

    /* CSS hack to style Step 1 container as a beautiful glassmorphism card */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]:has(.step1-active) {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border-radius: 2.5rem !important;
        border: 1px solid white !important;
        padding: 2.2rem 3.5rem 3.5rem 3.5rem !important;
        box-shadow: 0 25px 50px -12px rgba(5, 150, 105, 0.05) !important;
        margin-bottom: 2rem !important;
    }



    /* Core Metrics Cards */
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
    .modern-metric { background: #ffffff; padding: 1.5rem; border-radius: 24px; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); transition: transform 0.2s, box-shadow 0.2s; }
    .modern-metric:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
    .modern-metric-dark { background: #111827; color: white; border: 1px solid #1f2937; }
    .metric-label { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; margin-bottom: 0.25rem; }
    .metric-val { font-size: 1.75rem; font-weight: 900; margin: 0; }
    
    /* Narrative Box (AI Verdict) */
    .narrative-box { padding: 2.5rem; border-radius: 2rem; margin-bottom: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); position: relative; overflow: hidden; }
    .narrative-switch { background: linear-gradient(to bottom right, #f0fdf4, #ecfdf5); border: 1px solid #d1fae5; }
    .narrative-switch .verdict-label { color: #059669; }
    .narrative-switch h3 { color: #022c22; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.5rem; }
    .narrative-switch p { color: #065f46; font-size: 1.1rem; line-height: 1.6; font-weight: 500; margin: 0; }
    
    .narrative-wait { background: linear-gradient(to bottom right, #fffbeb, #fefce8); border: 1px solid #fef3c7; }
    .narrative-wait .verdict-label { color: #d97706; }
    .narrative-wait h3 { color: #451a03; font-size: 1.8rem; font-weight: 900; margin-bottom: 0.5rem; }
    .narrative-wait p { color: #92400e; font-size: 1.1rem; line-height: 1.6; font-weight: 500; margin: 0; }

    /* Component Boxes */
    .content-box { background: white; padding: 1.8rem; border-radius: 2rem; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); height: 100%; }
    .box-title { font-size: 1.25rem; font-weight: 800; color: #111827; margin-bottom: 1.2rem; display: flex; align-items: center; gap: 0.5rem; }
    
    /* Tips List */
    .tip-item { display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 1rem; }
    .tip-number { background: #fffbeb; color: #d97706; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.85rem; flex-shrink: 0; border: 1px solid #fef3c7; }
    .tip-text { font-size: 0.95rem; color: #374151; font-weight: 500; line-height: 1.5; margin: 0; }
    .tip-highlight { font-weight: 800; color: #b45309; margin-right: 0.3rem; }

    /* EV Card */
    .ev-card { padding: 1.2rem; border-radius: 1.5rem; border: 1px solid #f1f5f9; margin-bottom: 1rem; transition: background 0.2s; background: #ffffff; }
    .ev-card:hover { background: #ecfdf5; border-color: #d1fae5; }
    .ev-price { background: #ecfdf5; padding: 0.3rem 0.8rem; border-radius: 0.8rem; border: 1px solid #d1fae5; font-weight: 900; color: #065f46; font-size: 0.9rem;}

    /* Subsidy Box */
    .subsidy-box { background: linear-gradient(to bottom right, #111827, #1f2937); padding: 1.8rem; border-radius: 2rem; color: white; position: relative; overflow: hidden; margin-bottom: 1.5rem; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); }
    .subsidy-title { font-size: 0.85rem; font-weight: 800; letter-spacing: 0.1em; color: #34d399; text-transform: uppercase; margin-bottom: 1rem; }
    .subsidy-item { font-size: 0.9rem; color: #d1d5db; margin-bottom: 0.8rem; font-weight: 500; display: flex; gap: 0.5rem;}
    
    /* Chat Box Modern */
    .chat-user-msg { background: #111827; color: white; padding: 1rem 1.2rem; border-radius: 1.2rem 1.2rem 0.2rem 1.2rem; max-width: 85%; margin-left: auto; margin-bottom: 1rem; font-weight: 500; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .chat-agent-msg { background: white; border: 1px solid #e5e7eb; color: #1f2937; padding: 1rem 1.2rem; border-radius: 1.2rem 1.2rem 1.2rem 0.2rem; max-width: 85%; margin-right: auto; margin-bottom: 1rem; font-weight: 500; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.05); line-height: 1.6;}

    /* ─── CHAT UI INTEGRATION ─── */
    .chat-container { background: white; padding: 1.8rem; border-radius: 2rem 2rem 0 0; border: 1px solid #f1f5f9; border-bottom: none; }
    
    /* Mengunci Form Streamlit ke Kotak Chat History di Atasnya */
    [data-testid="stForm"] { 
        background: white; 
        border-radius: 0 0 2rem 2rem; 
        border: 1px solid #f1f5f9; 
        border-top: 1px dashed #e2e8f0; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        padding: 1.5rem 1.8rem; 
        margin-top: -1.3rem; 
        z-index: 10;
        position: relative;
    }
    
    /* Sejajarkan input chat dan tombol Kirim secara vertikal di bagian bawah */
    [data-testid="stForm"] [data-testid="stHorizontalBlock"] {
        align-items: flex-end !important;
    }

            
    /* ─── ANIMASI GEMINI THINKING (LOADING PILL) ─── */
    @keyframes spin-slow { 100% { transform: rotate(360deg); } }
    @keyframes shine { to { background-position: 200% center; } }
    
    .gemini-pill {
        display: inline-flex; align-items: center; gap: 12px; 
        padding: 12px 24px; background: #ffffff; 
        border-radius: 999px; border: 1px solid #d1fae5; 
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.15); 
        margin-bottom: 2rem; margin-left: auto; margin-right: auto;
    }
    .gemini-icon {
        font-size: 1.4rem; 
        animation: spin-slow 3s linear infinite; 
        display: inline-block;
    }
    .gemini-text {
        font-size: 1.05rem; font-weight: 800; 
        background: linear-gradient(90deg, #059669, #34d399, #059669);
        background-size: 200% auto; color: transparent;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shine 2s linear infinite;
        white-space: nowrap;
    }
    
    /* Vector Icons inside Metric Cards */
    .icon-wrapper {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 0.8rem;
    }
    .icon-bbm { background: #f1f5f9; color: #475569; }
    .icon-ev { background: #e8fbf2; color: #10b981; }
    .icon-save { background: #fffbeb; color: #d97706; }
    .icon-save-negative { background: #fef2f2; color: #dc2626; }
    .icon-co2 { background: #1f2937; color: #10b981; }
    
    /* Narrative Box Header Layout */
    .narrative-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .narrative-icon-wrapper {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .narrative-switch .narrative-icon-wrapper {
        background: #e8fbf2;
        color: #10b981;
    }
    .narrative-wait .narrative-icon-wrapper {
        background: #fffbeb;
        color: #d97706;
    }
    .narrative-box h3 {
        margin: 0 !important;
        line-height: 1.2 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar untuk API Key ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 Konfigurasi API Key")
    user_api_key = st.text_input(
        "Gemini API Key",
        value=DEFAULT_API_KEY,
        type="password",
        help="Dapatkan API key gratis dari Google AI Studio."
    )
    st.markdown("[Dapatkan API Key Gemini](https://aistudio.google.com/)")

GEMINI_API_KEY = user_api_key if user_api_key else ""

# ─── Init State & Agent ───────────────────────────────────────────────
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'agent' not in st.session_state or st.session_state.get('last_api_key') != GEMINI_API_KEY:
    st.session_state.agent = EnergyTransitAgent(api_key=GEMINI_API_KEY)
    st.session_state.last_api_key = GEMINI_API_KEY
if "conversation" not in st.session_state: 
    st.session_state.conversation = []
if "parsed_result" not in st.session_state: 
    st.session_state.parsed_result = None


# Data Referensi
KENDARAAN = [
    {"label": "Motor Matic (Beat, Scoopy, dll)", "jenis": "motor", "konsumsi": 45},
    {"label": "Mobil City Car (Brio, Agya, dll)", "jenis": "mobil_kecil", "konsumsi": 14},
    {"label": "Mobil MPV/SUV (Avanza, HR-V, dll)", "jenis": "mobil_besar", "konsumsi": 10},
]
PLN_TARIFFS = get_pln_tariffs()

# ─── NAVBAR ──────────────────────────────────────────────────────────
import base64
from pathlib import Path
from PIL import Image
import io

@safe_cache_data
def get_logo_html():
    logo_path = Path(__file__).parent / "asset" / "LogoGreenSwitch-1.png"
    if logo_path.exists():
        img = Image.open(logo_path)
        img.thumbnail((200, 200))
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        encoded_string = base64.b64encode(buffered.getvalue()).decode()
        return f'<img src="data:image/png;base64,{encoded_string}" style="height: 48px; margin-right: 4px; vertical-align: middle;">'
    return "⚡"

logo_html = get_logo_html()

st.markdown(f"""
<div class="modern-navbar">
    <h1 class="navbar-brand" style="display: flex; align-items: center;">{logo_html} GreenSwitch</h1>
    <div class="navbar-badge">Tim RDR · TechnoFest 2026</div>
</div>
""", unsafe_allow_html=True)

# Container Utama
st.markdown('<div class="center-container">', unsafe_allow_html=True)

# ─── STEP 0: HERO SECTION ─────────────────────────────────────────────
if st.session_state.step == 0:
    with st.container():
        st.markdown('<div class="step0-active"></div>', unsafe_allow_html=True)
        st.markdown('<div class="glow-circle"></div>', unsafe_allow_html=True)
        
        col_left, col_right = st.columns([1.2, 0.8], gap="large")
        with col_left:
            st.markdown(
                '<div class="hero-left-col">'
                '<div class="ai-badge">✨ AI AGENT REASONING</div>'
                '<h1 class="hero-title-react">Transisi ke EV dengan <span class="gradient-text">Data & Fakta.</span></h1>'
                '<p class="hero-desc-react">GreenSwitch menganalisis profil harian Anda untuk memberikan rekomendasi beralasan. Apakah beralih ke kendaraan listrik benar-benar menguntungkan Anda saat ini?</p>'
                '</div>',
                unsafe_allow_html=True
            )
            
            if st.button("Mulai Analisis ➔", key="start_btn"):
                st.session_state.step = 1
                safe_rerun()
                
        with col_right:
            st.markdown(
                '<div class="hero-right-col">'
                '<div style="display: flex; justify-content: center; align-items: center; height: 100%;">'
                '  <div class="hero-circle">'
                '    <svg width="120" height="120" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
                '      <rect width="16" height="10" x="2" y="7" rx="2" ry="2" />'
                '      <line x1="22" x2="22" y1="11" y2="13" />'
                '      <path d="m11 7-3 5h4l-3 5" />'
                '    </svg>'
                '    <div class="floating-badge badge-top">🌱</div>'
                '    <div class="floating-badge badge-bottom">📈</div>'
                '  </div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True
            )

# ─── STEP 1: FORM INPUT TERPUSAT ──────────────────────────────────────
elif st.session_state.step == 1:
    
    # Wrap inputs inside a card visually
    with st.container():
        st.markdown('<div class="step1-active"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="margin-bottom: 2.5rem;">
            <h2 style="font-size: 2.2rem; font-weight: 900; color: #111827; margin-bottom: 0.5rem; margin-top: 0;">Profil Pengguna</h2>
            <p style="color: #6b7280; font-weight: 500; font-size: 1.1rem; margin: 0;">Data ini diproses oleh AI untuk menjamin akurasi rekomendasi finansial Anda.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="large")
        with col1:
            kendaraan_idx = st.selectbox("Kendaraan BBM Saat Ini", range(len(KENDARAAN)), format_func=lambda i: KENDARAAN[i]["label"])
            jenis_bbm = st.selectbox("BBM yang Digunakan", ["Pertalite", "Pertamax", "Pertamax Turbo"])
            kategori_ev = st.selectbox("Kategori EV yang Diinginkan", ["Motor", "Mobil City Car", "Mobil Sedan/MPV", "SUV"], index=1)
            jarak = st.slider("Jarak Tempuh Harian (km)", 10, 150, 60, step=5)
            
        with col2:
            pln_idx = st.selectbox("Daya Listrik Rumah (PLN)", range(len(PLN_TARIFFS)), format_func=lambda i: f"{PLN_TARIFFS[i]['label']} (Rp {PLN_TARIFFS[i]['tarif']}/kWh)")
            anggaran = st.number_input("Budget Beli EV (Juta Rp)", min_value=10, max_value=2000, value=300, step=10)
            trade_in_juta = st.number_input("Nilai Jual Kendaraan Lama (Juta Rp)", min_value=0, max_value=1000, value=15, step=1)
            
            st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Kalkulasi Live Preview di dalam form
        konsumsi_km_per_liter = KENDARAAN[kendaraan_idx]["konsumsi"]
        
        with st.spinner("⛽ Sedang mengecek harga BBM terbaru (Live dari MyPertamina)..."):
            harga_bbm = get_bbm_price(jenis_bbm)
            
        estimasi_bbm_bulan = int(((jarak * 30) / konsumsi_km_per_liter) * harga_bbm)
        
        col_preview = st.columns(1)
        with col_preview[0]:
            st.markdown(f"""
            <div style="background: linear-gradient(to right, #eff6ff, #e0e7ff); border: 1px solid #bfdbfe; border-radius: 1rem; padding: 1.5rem; margin-top: 1rem; margin-bottom: 2rem;">
                <p style="color: #1e3a8a; font-size: 1.05rem; font-weight: 500; margin: 0; line-height: 1.5;">
                    ℹ️ Berdasarkan mobilitas Anda, estimasi biaya BBM saat ini mencapai <strong style="color: #1d4ed8; font-size: 1.15rem;">Rp {estimasi_bbm_bulan:,}/bulan</strong>. Mari kita lihat seberapa besar yang bisa Anda hemat.
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        col_back, col_submit = st.columns([1, 2])
        with col_back:
            if st.button("Kembali"):
                st.session_state.step = 0
                safe_rerun()
        with col_submit:
            analyze_btn = st.button("✨ Analisis dengan Agent")
        
    if analyze_btn:
        st.session_state.user_data = {
            "kendaraan_jenis": KENDARAAN[kendaraan_idx]["jenis"],
            "konsumsi_km_per_liter": KENDARAAN[kendaraan_idx]["konsumsi"],
            "jenis_bbm": jenis_bbm,
            "jarak_km": jarak,
            "pln_label": PLN_TARIFFS[pln_idx]["label"],
            "pln_tarif": PLN_TARIFFS[pln_idx]["tarif"],
            "anggaran_juta": float(anggaran),
            "kategori_ev_diinginkan": kategori_ev,
            "trade_in_juta": float(trade_in_juta)
        }
        
        st.session_state.conversation = []
        st.session_state.has_scrolled_top = False
        
        # Animasi Loading Gemini
        think_placeholder = st.empty()
        think_placeholder.markdown(f"""
        <div style="display: flex; justify-content: center; width: 100%; margin-top: -1.5rem;">
            <div class="gemini-pill">
                <span class="gemini-icon">✨</span>
                <span class="gemini-text">Agent Sedang Menganalisis Data Transisi...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Scroll ke bawah untuk menunjukkan loading
        scroll_placeholder = st.empty()
        with scroll_placeholder:
            components.html(
                """
                <script>
                    setTimeout(() => {
                        const mainSection = window.parent.document.querySelector('section.main');
                        if (mainSection) {
                            mainSection.scrollTo({ top: mainSection.scrollHeight, behavior: 'smooth' });
                        }
                        window.parent.scrollTo({ top: window.parent.document.body.scrollHeight, behavior: 'smooth' });
                    }, 100);
                </script>
                """,
                height=0,
                width=0,
            )

        try:
            # Panggil Agent
            result = st.session_state.agent.analyze(st.session_state.user_data)
            think_placeholder.empty() 
            scroll_placeholder.empty()
            
            st.session_state.parsed_result = result
            st.session_state.step = 2
            safe_rerun()
        except Exception as e:
            st.error(f"❌ Terjadi Kesalahan Eksekusi: {str(e)}")


# ─── STEP 2: RESULT DASHBOARD UTAMA ───────────────────────────────────
elif st.session_state.step == 2:
    res = st.session_state.parsed_result
    
    # Scroll ke atas hanya sekali saat pertama kali masuk ke step 2 (Laporan Hasil)
    if not st.session_state.get('has_scrolled_top', False):
        components.html(
            """
            <script>
                setTimeout(() => {
                    const mainSection = window.parent.document.querySelector('section.main');
                    if (mainSection) {
                        mainSection.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                    window.parent.scrollTo({ top: 0, behavior: 'smooth' });
                }, 100);
            </script>
            """,
            height=0,
            width=0,
        )
        st.session_state.has_scrolled_top = True
        
    metrics = res.get("metrics", {})
    ev_matches = res.get("evMatches", [])
    
    biaya_bbm = metrics.get("biaya_bbm_bulanan", 0)
    biaya_ev = metrics.get("biaya_listrik_bulanan", 0)
    selisih = metrics.get("selisih_bulanan", 0)
    co2_kg = metrics.get("emisi_co2_bulan", 0) * 12 # Disetahunkan
    
    u_budget = st.session_state.user_data.get('anggaran_juta', 300)
    u_trade = st.session_state.user_data.get('trade_in_juta', 15)
    investasi_awal_juta = max(0, u_budget - u_trade)
    verdict_class = "narrative-switch" if res.get("verdict", "").lower() == "switch" else "narrative-wait"
    
    # Format angka dengan format ribuan titik (.)
    bbm_formatted = f"{int(biaya_bbm):,}".replace(",", ".")
    ev_formatted = f"{int(biaya_ev):,}".replace(",", ".")
    selisih_formatted = f"{'+' if selisih >= 0 else '-'}Rp {int(abs(selisih)):,}".replace(",", ".")
    co2_formatted = f"{co2_kg:,.1f}".replace(",", ".")

    # SVGs
    icon_chat_svg = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
    icon_car_svg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9C2 11.1 2 11.3 2 11.5V16c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/></svg>'
    icon_zap_svg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
    icon_save_svg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v12"/><path d="M15 9.5H11.5a2.5 2.5 0 0 0 0 5H13a2.5 2.5 0 0 1 0 5H9"/></svg>'
    icon_co2_svg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>'

    # Header Results
    col_title, col_btn = st.columns([3, 1])
    with col_title:
        st.markdown('<div style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 12px; background: #d1fae5; color: #065f46; border-radius: 99px; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; margin-bottom: 0.5rem; border: 1px solid #a7f3d0;">✨ INSIGHTS</div>', unsafe_allow_html=True)
        st.markdown('<h2 style="font-size: 2.2rem; font-weight: 900; color: #111827; margin-bottom: 1.5rem; margin-top: 0;">Laporan Transisi EV Anda</h2>', unsafe_allow_html=True)
    with col_btn:
        if st.button("⚙️ Sesuaikan Parameter"):
            st.session_state.step = 1
            safe_rerun()

    # NARRATIVE BOX AI
    st.markdown(f"""
    <div class="narrative-box {verdict_class}">
        <div class="narrative-header">
            <div class="narrative-icon-wrapper">
                {icon_chat_svg}
            </div>
            <div>
                <div class="verdict-label" style="text-transform: uppercase; font-size: 0.75rem; font-weight: 800; letter-spacing: 0.1em; margin-bottom: 0.25rem;">Keputusan Agent</div>
                <h3 style="margin: 0; font-size: 1.8rem; font-weight: 900;">{res.get('title', 'Analisis Selesai')}</h3>
            </div>
        </div>
        <p style="margin-top: 1rem; margin-bottom: 0;">{res.get('narasi', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # 4 KOTAK METRIK UTAMA
    st.markdown(f"""
    <div class="metric-grid">
        <div class="modern-metric">
            <div class="icon-wrapper icon-bbm">
                {icon_car_svg}
            </div>
            <div class="metric-label">BBM / Bulan</div>
            <div class="metric-val" style="color: #111827;">Rp {bbm_formatted}</div>
        </div>
        <div class="modern-metric">
            <div class="icon-wrapper icon-ev">
                {icon_zap_svg}
            </div>
            <div class="metric-label">Listrik EV / Bulan</div>
            <div class="metric-val" style="color: #059669;">Rp {ev_formatted}</div>
        </div>
        <div class="modern-metric" style="background: {'#f0fdf4' if selisih > 0 else '#fef2f2'}; border-color: {'#d1fae5' if selisih > 0 else '#fee2e2'};">
            <div class="icon-wrapper {'icon-save' if selisih > 0 else 'icon-save-negative'}">
                {icon_save_svg}
            </div>
            <div class="metric-label" style="color: {'#065f46' if selisih > 0 else '#991b1b'}">Penghematan</div>
            <div class="metric-val" style="color: {'#059669' if selisih > 0 else '#dc2626'};">{selisih_formatted}</div>
        </div>
        <div class="modern-metric modern-metric-dark">
            <div class="icon-wrapper icon-co2">
                {icon_co2_svg}
            </div>
            <div class="metric-label" style="color: #9ca3af;">Reduksi CO2 / Tahun</div>
            <div class="metric-val">{co2_formatted} <span style="font-size: 1rem; color: #6b7280;">Kg</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # PEMBAGIAN KOLOM KIRI & KANAN
    col_left, col_right = st.columns([1.5, 1], gap="medium")
    
    with col_left:
        # KOTAK GRAFIK
        st.markdown("""
        <div style="background: #ffffff; padding: 1.8rem 1.8rem 0 1.8rem; border-radius: 2rem 2rem 0 0; border: 1px solid #f1f5f9; border-bottom: none; box-shadow: 0 -2px 5px rgba(0,0,0,0.02);">
            <div style="font-size: 1.25rem; font-weight: 800; color: #111827; margin-bottom: 0.2rem;">Proyeksi Pengeluaran Kumulatif</div>
            <div style="font-size: 0.9rem; color: #6b7280; font-weight: 500;">Perbandingan biaya operasional selama 5 tahun ke depan.</div>
        </div>
        """, unsafe_allow_html=True)
        
        bulan = list(range(0, 61))
        kum_bbm = [(m * biaya_bbm) / 1_000_000 for m in bulan]
        kum_ev  = [((m * biaya_ev) / 1_000_000) for m in bulan]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bulan, y=kum_bbm, fill='tozeroy', name="Kendaraan BBM", line=dict(color="#ef4444", width=3), fillcolor="rgba(239, 68, 68, 0.05)"))
        fig.add_trace(go.Scatter(x=bulan, y=kum_ev, fill='tozeroy', name="Kendaraan Listrik", line=dict(color="#10b981", width=3), fillcolor="rgba(16, 185, 129, 0.05)"))
        
        fig.update_layout(
            margin=dict(l=40, r=20, t=15, b=10), height=280,
            paper_bgcolor='rgba(255,255,255,1)', plot_bgcolor='rgba(255,255,255,1)',
            showlegend=False,
            xaxis=dict(
                showgrid=False,
                tickvals=[12, 24, 36, 48, 60],
                ticktext=["Tahun 1", "Tahun 2", "Tahun 3", "Tahun 4", "Tahun 5"],
                tickfont=dict(color="#9ca3af", size=11),
                zeroline=False
            ), 
            yaxis=dict(
                showgrid=True,
                gridcolor="#f1f5f9",
                ticksuffix=" Jt",
                tickfont=dict(color="#9ca3af", size=11),
                zeroline=False
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # HTML Legend & Card Bottom
        st.markdown("""
        <div style="background: #ffffff; padding: 0 1.8rem 1.8rem 1.8rem; border-radius: 0 0 2rem 2rem; border: 1px solid #f1f5f9; border-top: none; margin-top: -1.2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem; display: flex; justify-content: center; gap: 1.5rem; font-size: 0.9rem; font-weight: 700;">
            <div style="display: flex; align-items: center; gap: 0.5rem; color: #4b5563;">
                <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #ef4444;"></span>
                Kendaraan BBM
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem; color: #4b5563;">
                <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #10b981;"></span>
                Kendaraan Listrik
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # KOTAK TIPS KHUSUS
        if res and "tips" in res:
            tips_html = '<div class="content-box"><div class="box-title">💡 Tips Khusus untuk Anda</div>'
            for i, tip in enumerate(res["tips"]):
                highlight = tip.get("highlight", "")
                text = tip.get("text", "")
                tips_html += f'<div class="tip-item"><div class="tip-number">{i+1}</div><p class="tip-text"><span class="tip-highlight">{highlight}:</span> {text}</p></div>'
            tips_html += '</div>'
            st.markdown(tips_html, unsafe_allow_html=True)


    with col_right:
        # KOTAK INSENTIF
        st.markdown("""
        <div class="subsidy-box" style="margin-bottom: 1.5rem;">
            <div class="subsidy-title">🏛️ Insentif Pemerintah</div>
            <div class="subsidy-item"><span>✓</span> Potongan PPN dari 11% menjadi 1%</div>
            <div class="subsidy-item"><span>✓</span> Bebas Ganjil-Genap di DKI Jakarta</div>
            <div class="subsidy-item"><span>✓</span> Subsidi Insentif Langsung s.d Rp 7 Juta</div>
        </div>
        """, unsafe_allow_html=True)
        
        # KOTAK KENDARAAN TERDEKAT DARI DATABASE
        if ev_matches:
            ev_html = '<div class="content-box"><div class="box-title">🚗 Opsi Unit EV Terdekat</div>'
            for ev in ev_matches[:2]:  # Tampilkan top 2 saja agar rapi
                ev_html += f"""<div class="ev-card">
<div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
<div>
<h4 style="margin: 0; font-weight: 800; color: #111827; font-size: 1.05rem;">{ev['nama']}</h4>
<p style="margin: 0; font-size: 0.8rem; font-weight: bold; color: #059669; margin-top: 4px;">Jangkauan {ev['jangkauan']} km</p>
</div>
<div class="ev-price">Rp {ev['harga']} Jt</div>
</div>
<p style="margin: 0; font-size: 0.82rem; color: #64748b; font-weight: 500; line-height: 1.4;">Charging: {ev['charging']} | {ev['catatan']}</p>
</div>"""
            ev_html += '</div>'
            st.markdown(ev_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="content-box">
                <div class="box-title">🚗 Opsi Unit EV Terdekat</div>
                <div class="ev-card" style="text-align:center;">
                    <p style="margin:0; color:#64748b;">Belum ada opsi EV yang pas dengan anggaran Anda saat ini.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # KOTAK ANALISIS MENDALAM
    # KOTAK ANALISIS MENDALAM
    if res and "analisis_mendalam" in res:
        import markdown
        html_content = markdown.markdown(res["analisis_mendalam"])
        
        html_string = f"""<style>
.analisis-content h3 {{ color: #111827; font-size: 1.3rem; font-weight: 700; margin-top: 2rem; margin-bottom: 0.75rem; }}
.analisis-content p {{ margin-bottom: 1rem; }}
.analisis-content ul {{ margin-bottom: 1rem; padding-left: 1.5rem; }}
.analisis-content li {{ margin-bottom: 0.5rem; }}
</style>
<div style="background: white; padding: 2.5rem 3rem; border-radius: 2rem; border: 1px solid #f1f5f9; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.05); margin-top: 1.5rem; margin-bottom: 2rem; border-top: 4px solid #10b981;">
    <h3 style="margin-top: 0; margin-bottom: 1.5rem; color: #111827; font-size: 1.6rem; font-weight: 800; border-bottom: 2px solid #f1f5f9; padding-bottom: 1rem;">
        🔍 Analisis Mendalam
    </h3>
    <div class="analisis-content" style="color: #374151; line-height: 1.7; font-size: 1rem;">
        {html_content}
    </div>
</div>"""
        st.markdown(html_string, unsafe_allow_html=True)

    # KOTAK CHAT LANJUTAN
    chat_html = '<div style="margin-top: 2rem;" class="chat-container"><div class="box-title">💬 Diskusi Lanjut dengan Agent</div>'
    for msg in st.session_state.conversation:
        if msg["role"] == "user":
            chat_html += f'<div class="chat-user-msg">{msg["content"]}</div>'
        elif msg["role"] == "assistant":
            chat_html += f'<div class="chat-agent-msg">{msg["content"]}</div>'
    chat_html += '</div>'
    
    st.markdown(chat_html, unsafe_allow_html=True)
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # FORM INPUT CHAT BARU
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_btn = st.columns([5, 1])
        with col_input: 
            user_input = st.text_input(" ", placeholder="Ketik pertanyaan lanjutan untuk AI (Misal: Apakah bengkel resminya banyak di Jakarta?).")
        with col_btn: 
            submitted = st.form_submit_button("Kirim")

    # EKSEKUSI CHAT DENGAN ANIMASI GEMINI
    if submitted and user_input:
        st.session_state.conversation.append({"role": "user", "content": user_input})
        
        chat_think_placeholder = st.empty()
        chat_think_placeholder.markdown(f"""
        <div style="display: flex; justify-content: center; width: 100%;">
            <div class="gemini-pill">
                <span class="gemini-icon">✨</span>
                <span class="gemini-text">Agent sedang mengetik balasan...</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Gunakan fungsi chat dari instance agent yang aktif
            reply = st.session_state.agent.chat(user_input)
            st.session_state.conversation.append({"role": "assistant", "content": reply})
            
            chat_think_placeholder.empty()
            safe_rerun()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Tutup Container Utama
st.markdown('</div>', unsafe_allow_html=True)
