import streamlit as st
import datetime
import math
from PIL import Image

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Rooster & Studieplanner",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- NAVIGATIE STATE INITIALISATIE ---
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Rooster"
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = {}
if 'exams' not in st.session_state:
    st.session_state['exams'] = []

# Navigatie helper functie
def go_to_page(page_name):
    st.session_state['current_page'] = page_name

# --- STYLING (DARK THEME ZOALS MAGISTER/SOMTODAY) ---
st.markdown("""
    <style>
    /* Dark Theme achtergrond */
    .stApp {
        background-color: #181b20;
        color: #e1e3e6;
    }
    
    /* Top navigatiebalk stijl */
    .top-nav {
        background-color: #20242b;
        padding: 10px 20px;
        border-bottom: 1px solid #2d323b;
        margin-bottom: 20px;
        border-radius: 8px;
    }
    
    /* Rooster Blokken Stijl */
    .agenda-card {
        background-color: #2b384e;
        border-left: 4px solid #4f80ff;
        border-radius: 6px;
        padding: 8px 10px;
        margin-bottom: 10px;
        color: #ffffff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .exam-card {
        background-color: #3b2d4a;
        border-left: 4px solid #b359ff;
        border-radius: 6px;
        padding: 8px 10px;
        margin-bottom: 10px;
        color: #ffffff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }

    .time-badge {
        float: right;
        background-color: #4a5873;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    
    .exam-badge {
        float: right;
        background-color: #7b42a6;
        color: #ffffff;
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: bold;
    }

    /* Knoppen styling */
    div.stButton > button {
        background-color: #34aa44;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
    }
    div.stButton > button:hover {
        background-color: #2e963b;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- BOVENBALK (HEADER & NAVIGATIE) ---
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
c_nav1, c_nav2, c_nav3, c_nav4 = st.columns([1, 1, 1, 3])

with c_nav1:
    if st.button("📅 Rooster", key="btn_nav_rooster"):
        go_to_page("Rooster")
        st.rerun()
with c_nav2:
    if st.button("➕ Afspraak / Toets inplannen", key="btn_nav_create"):
        go_to_page("Inplannen")
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGINA 1: STARTPAGINA (ROOSTER)
# ==========================================
if st.session_state['current_page'] == "Rooster":
    
    # Header acties
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title("📅 Rooster")
    with col_h2:
        if st.button("➕ Afspraak inplannen", key="btn_top_create"):
            go_to_page("Inplannen")
            st.rerun()

    st.markdown("---")
    
    # Datum kiezers
    col_d1, col_d2 = st.columns([1, 3])
    with col_d1:
        start_week = st.date_input("Week van:", datetime.date.today())
    
    # Toon weekdagen (Maandag t/m Vrijdag)
    days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    
    # Maken van 5 kolommen voor de werkweek
    cols = st
