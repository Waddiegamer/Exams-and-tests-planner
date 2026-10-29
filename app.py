import streamlit as st
import datetime
import math
from PIL import Image

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="PTA & Examen Agenda",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AANGEPASTE CSS VOOR EEN MOOIER EN STRAKKER DESIGN ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #45a049;
        color: white;
    }
    .agenda-card {
        background-color: #ffffff;
        border-left: 5px solid #2196F3;
        padding: 12px;
        margin-bottom: 10px;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .exam-card {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 12px;
        margin-bottom: 10px;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSIE OPSLAG GEBRUIKEN (Slaat de planning op tijdens de sessie) ---
if 'schedule' not in st.session_state:
    st.session_state['schedule'] = {}
if 'exams' not in st.session_state:
    st.session_state['exams'] = []

# --- NAVIGATIE IN DE SIDEBAR ---
st.sidebar.title("📌 Navigatie")
page = st.sidebar.radio("Ga naar:", ["📅 Startpagina (Agenda)", "➕ Nieuwe PTA/Toets Inplannen"])

# ==========================================
# PAGINA 1: STARTPAGINA (AGENDA)
# ==========================================
if page == "📅 Startpagina (Agenda)":
    st.title("📅 Jouw Studie & Toets Agenda")
    st.caption("Bekijk hier je ingeplande leerdagen, PTA's en toetsen.")

    col_btn, _ = st.columns([1, 2])
    with col_btn:
        if st.button("➕ Nieuwe PTA of Toets Toevoegen"):
            st.session_state['goto_create'] = True
            st.rerun()

    st.markdown("---")

    # Selecteer een week/datumweergave
    selected_date = st.date_input("Bekijk agenda vanaf datum:", datetime.date.today())
    
    st.subheader("📋 Komende 7 Dagen")
    
    days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]

    # Toon 7 dagen overzicht
    for i in range(7):
        current_day = selected_date + datetime.timedelta(days=i)
        day_str = days_nl[current_day.weekday()]
        date_formatted = current_day.strftime("%d-%m-%Y")
        
        # Check of er items zijn voor deze dag
        has_tasks = current_day in st.session_state['schedule']
        has_exams = any(e['date'] == current_day for e in st.session_state['exams'])

        with st.expander(f"📆 **{day_str} {date_formatted}**" + (" 🔴 (TOETSDAG)" if has_exams else (" 🔵 (Studiedag)" if has_tasks else "")), expanded=(i < 3)):
            
            # 1. Toon eventuele toetsen op deze dag
            if has_exams:
                for exam in st.session_state['exams']:
                    if exam['date'] == current_day:
                        st.markdown(f"""
                        <div class="exam-card">
                            🎯 <b>TOETS: {exam['title']}</b><br>
                            ⏱️ <b>Tijdsduur:</b> {exam['duration']} uur<br>
                            📌 <b>Onderwerpen:</b> {exam['topics_summary']}
                        </div>
                        """, unsafe_allow_html=True)

            # 2. Toon de studietaken voor deze dag
            if has_tasks:
                tasks = st.session_state['schedule'][current_day]
                st.markdown("<b>📚 Te leren onderwerpen:</b>", unsafe_allow_html=True)
                for task in tasks:
                    st.checkbox(f"{task}", key=f"check_{current_day}_{task}")

            if not has_tasks and not has_exams:
                st.write("🟢 *Geen studietaken of toetsen gepland voor vandaag.*")

# ==========================================
# PAGINA 2: NIEUWE PTA/TOETS INPLANNEN
# ==========================================
else:
    st.title("➕ Nieuwe PTA / Toets Inplannen")
    st.write("Vul hier de details in van je toets om automatisch een leerschema te genereren.")

    st.markdown("---")

    # --- SECTIE 1: TOETS DETAILS ---
    st.header("1. Toets Details")
    
    col1, col2 = st.columns(2)
    with col1:
        exam_title = st.text_input("Naam van het vak / PTA:", "Bedrijfseconomie")
        start_date = st.date_input("Startdatum leren:", datetime.date.today())

    with col2:
        exam_duration = st.number_input("Tijdsduur van de toets (in uren):", min_value=0.5, max_value=8.0, value=1.0, step=0.5)
        exam_date = st.date_input("Datum van de PTA/Toets:", datetime.date.today() + datetime.timedelta(days=7))

    # --- SECTIE 2: INFORMATIE & ONDERWERPEN ---
    st.header("2. Stof & Screenshot")
    
    uploaded_file = st.file_uploader("Upload eventueel een screenshot van je PTA (optioneel):", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Geüploade PTA-afbeelding", use_container_width=True)

    default_text = "Hoofdstuk 1, Hoofdstuk 2, Paragraaf 3.1, Paragraaf 3.2, Samenvatting maken"
    raw_topics = st.text_area("Typ de onderwerpen/hoofdstukken (gescheiden door een komma):", default_text)
    topics_list = [t.strip() for t in raw_topics.split(",") if t.strip()]

    # --- SECTIE 3: STUDIEDAGEN KIEZEN ---
    st.header("3. Dagen-voorkeur")
    st.write("Op welke dagen wil je leren?")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        m = st.checkbox("Maandag", value=True)
        di = st.checkbox("Dinsdag", value=True)
    with c2:
        wo = st.checkbox("Woensdag", value=True)
        do = st.checkbox("Donderdag", value=True)
    with c3:
        vr = st.checkbox("Vrijdag", value=True)
        za = st.checkbox("Zaterdag", value=True)
    with c4:
        zo = st.checkbox("Zondag", value=False)

    study_days = {
        "Maandag": m, "Dinsdag": di, "Woensdag": wo, "Donderdag": do,
        "Vrijdag": vr, "Zaterdag": za, "Zondag": zo
    }

    st.markdown("---")

    # --- KNOP OM SCHEMA OP TE SLAAN ---
    if st.button("🚀 Schema Genereren & Opslaan in Agenda"):
        if not topics_list:
            st.error("Voer ten minste één onderwerp of hoofdstuk in!")
        elif start_date >= exam_date:
            st.error("De toetsdatum moet ná de startdatum liggen.")
        else:
            # Bereken beschikbare dagen
            current_date = start_date
            valid_dates = []
            days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
            
            while current_date < exam_date:
                day_name = days_nl[current_date.weekday()]
                if study_days[day_name]:
                    valid_dates.append(current_date)
                current_date += datetime.timedelta(days=1)

            if not valid_dates:
                st.warning("Geen geldige studiedagen geselecteerd binnen deze periode!")
            else:
                # Verdeel de taken
                num_days = len(valid_dates)
                num_topics = len(topics_list)
                topics_per_day = math.ceil(num_topics / num_days)

                for i, date in enumerate(valid_dates):
                    start_idx = i * topics_per_day
                    end_idx = min(start_idx + topics_per_day, num_topics)
                    assigned_topics = topics_list[start_idx:end_idx]

                    if assigned_topics:
                        if date not in st.session_state['schedule']:
                            st.session_state['schedule'][date] = []
                        for topic in assigned_topics:
                            st.session_state['schedule'][date].append(f"[{exam_title}] {topic}")

                # Voeg de toets toe aan de agenda
                st.session_state['exams'].append({
                    "title": exam_title,
                    "date": exam_date,
                    "duration": exam_duration,
                    "topics_summary": ", ".join(topics_list[:3]) + ("..." if len(topics_list) > 3 else "")
                })

                st.success("🎉 Je PTA is succesvol verwerkt en ingepland in de agenda!")
                st.info("Ga via het menu links naar **📅 Startpagina (Agenda)** om je overzicht te bekijken.")
