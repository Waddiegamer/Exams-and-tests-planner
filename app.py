import streamlit as st
import datetime
import math
from PIL import Image

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Rooster & PTA Planner",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- NAVIGATIE & SESSIE OPSLAG ---
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Rooster"
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = []

def go_to_page(page_name):
    st.session_state['current_page'] = page_name

# --- STYLING (DARK THEME & TIMETABLE GRID) ---
st.markdown("""
    <style>
    /* Dark Theme basis */
    .stApp {
        background-color: #181b20;
        color: #e1e3e6;
    }
    
    /* Navigatiebalk bovenin */
    .top-nav {
        background-color: #20242b;
        padding: 10px 15px;
        border-bottom: 1px solid #2d323b;
        margin-bottom: 20px;
        border-radius: 8px;
    }
    
    /* Agenda Grid Styling */
    .time-slot-header {
        background-color: #20242b;
        color: #9aa0a6;
        text-align: center;
        padding: 8px 0;
        font-weight: bold;
        border-bottom: 2px solid #3c4043;
        font-size: 0.9rem;
    }
    
    .time-cell {
        height: 60px;
        border-bottom: 1px solid #2d323b;
        border-right: 1px solid #2d323b;
        position: relative;
        padding: 2px;
    }
    
    .time-label {
        color: #80868b;
        font-size: 0.8rem;
        text-align: right;
        padding-right: 8px;
        line-height: 60px;
        border-bottom: 1px solid #2d323b;
    }

    /* Event Kaarten in het Rooster */
    .agenda-card {
        background-color: #2b384e;
        border-left: 4px solid #4f80ff;
        border-radius: 6px;
        padding: 6px 8px;
        margin-bottom: 4px;
        color: #ffffff;
        font-size: 0.85rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    
    .exam-card {
        background-color: #3b2d4a;
        border-left: 4px solid #b359ff;
        border-radius: 6px;
        padding: 6px 8px;
        margin-bottom: 4px;
        color: #ffffff;
        font-size: 0.85rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }

    .time-badge {
        float: right;
        background-color: #4a5873;
        color: #ffffff;
        padding: 1px 5px;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    
    .exam-badge {
        float: right;
        background-color: #7b42a6;
        color: #ffffff;
        padding: 1px 5px;
        border-radius: 8px;
        font-size: 0.7rem;
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

# --- BOVENBALK NAVIGATIE ---
st.markdown('<div class="top-nav">', unsafe_allow_html=True)
c_nav1, c_nav2, _ = st.columns([1, 1.5, 4])

with c_nav1:
    if st.button("📅 Rooster", key="btn_nav_rooster"):
        go_to_page("Rooster")
        st.rerun()
with c_nav2:
    if st.button("➕ Afspraak / PTA Inplannen", key="btn_nav_create"):
        go_to_page("Inplannen")
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAGINA 1: ROOSTER (AGENDA GRID)
# ==========================================
if st.session_state['current_page'] == "Rooster":
    
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title("📅 Rooster")
    with col_h2:
        if st.button("➕ Afspraak inplannen", key="btn_top_create"):
            go_to_page("Inplannen")
            st.rerun()

    st.markdown("---")
    
    col_d1, _ = st.columns([1, 3])
