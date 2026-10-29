import streamlit as st
import datetime
import math
import sqlite3

# --- PAGINA CONFIGURATIE (PC GEOPTIMALISEERD) ---
st.set_page_config(
    page_title="Somtoday Rooster",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DATABASE INITIALISATIE (SQLITE) ---
def init_db():
    conn = sqlite3.connect('planner.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            type TEXT,
            title TEXT,
            topic TEXT,
            date TEXT,
            start_hour INTEGER,
            start_time TEXT,
            duration REAL,
            location TEXT,
            completed INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_all_events():
    conn = sqlite3.connect('planner.db')
    c = conn.cursor()
    c.execute('SELECT id, type, title, topic, date, start_hour, start_time, duration, location, completed FROM events')
    rows = c.fetchall()
    conn.close()
    
    events = []
    for r in rows:
        events.append({
            "id": r[0],
            "type": r[1],
            "title": r[2],
            "topic": r[3],
            "date": datetime.datetime.strptime(r[4], "%Y-%m-%d").date(),
            "start_hour": r[5],
            "start_time": r[6],
            "duration": r[7],
            "location": r[8],
            "completed": bool(r[9])
        })
    return events

def save_event_to_db(ev):
    conn = sqlite3.connect('planner.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO events (id, type, title, topic, date, start_hour, start_time, duration, location, completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (ev['id'], ev['type'], ev['title'], ev['topic'], str(ev['date']), ev['start_hour'], ev['start_time'], ev['duration'], ev.get('location', 'N.v.t.'), int(ev.get('completed', 0))))
    conn.commit()
    conn.close()

def update_task_completion(task_id, completed):
    conn = sqlite3.connect('planner.db')
    c = conn.cursor()
    c.execute('UPDATE events SET completed = ? WHERE id = ?', (int(completed), task_id))
    conn.commit()
    conn.close()

# --- NAVIGATIE STATE ---
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Rooster"

def go_to_page(page_name):
    st.session_state['current_page'] = page_name

# Gefilterde vakkenlijst
ALLOWED_SUBJECTS = [
    "Bedrijfseconomie",
    "Duitse taal en literatuur",
    "Engelse taal en literatuur",
    "Godsdienst",
    "Nat leven techniek",
    "Natuurkunde",
    "Nederlandse taal en literatuur",
    "Scheikunde",
    "Wiskunde B"
]

# Exacte Somtoday Donkerblauwe Kleuren per Vak
SUBJECT_COLORS = {
    "Bedrijfseconomie": "#263242",
    "Wiskunde B": "#263242",
    "Engels": "#263242",
    "Duitse taal en literatuur": "#263242",
    "Nederlands": "#263242",
    "Godsdienst": "#263242",
    "Natuurkunde": "#263242",
    "Scheikunde": "#263242",
    "Nat leven techniek": "#263242"
}

def get_color(subject):
    return SUBJECT_COLORS.get(subject, "#263242")

# --- SOMTODAY EXACTE STYLING & HOOG CONTRAST ---
st.markdown("""
    <style>
    /* Hoofdachtergrond van Somtoday */
    .stApp {
        background-color: #12151a;
        color: #ffffff;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Hoge contrasten voor alle invoervelden, labels en helpteksten */
    label, .stMarkdown, p, span, div {
        color: #ffffff !important;
        font-weight: 500;
    }

    .stCaption, small {
        color: #f0f0f0 !important;
        font-weight: 600;
    }

    /* Invoervelden achtergrond en tekst */
    input, textarea, select, div[data-baseweb="select"] {
        background-color: #1e242d !important;
        color: #ffffff !important;
        border: 1px solid #4a5568 !important;
        font-weight: bold !important;
    }
    
    /* Rooster Grid Naadloos Aansluitend */
    .grid-container {
        display: grid;
        grid-template-columns: 65px repeat(5, 1fr);
        background-color: #12151a;
        border: 1px solid #232a35;
        border-radius: 4px;
        overflow: hidden;
    }
    
    .day-header {
        background-color: #1a1e26;
        color: #ffffff !important;
        text-align: center;
        padding: 12px 4px;
        font-weight: bold;
        border-right: 1px solid #232a35;
        border-bottom: 1px solid #232a35;
        font-size: 0.95rem;
    }
    
    .time-col-header {
        background-color: #1a1e26;
        border-right: 1px solid #232a35;
        border-bottom: 1px solid #232a35;
    }

    .time-label {
        color: #a0aec0 !important;
        font-size: 0.78rem;
        text-align: right;
        padding-right: 8px;
        height: 65px;
        line-height: 65px;
        border-bottom: 1px solid #1e242d;
        border-right: 1px solid #232a35;
        background-color: #12151a;
        font-weight: 600;
    }
    
    .grid-cell {
        height: 65px;
        border-bottom: 1px solid #1e242d;
        border-right: 1px solid #232a35;
        padding: 2px;
        position: relative;
        background-color: #12151a;
    }

    /* Les & Toets Kaarten in Somtoday stijl */
    .agenda-card {
        background-color: #263242;
        border-radius: 6px;
        padding: 6px 8px;
        color: #ffffff !important;
        font-size: 0.82rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        margin-bottom: 2px;
        position: relative;
        border-left: 3px solid #58a6ff;
    }

    .exam-card {
        background-color: #263242;
        border-radius: 6px;
        padding: 6px 8px;
        color: #ffffff !important;
        font-size: 0.82rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        margin-bottom: 2px;
        position: relative;
        border-left: 3px solid #e3b341;
    }
    
    .time-badge {
        float: right;
        background-color: #3b82f6;
        color: #ffffff !important;
        padding: 1px 7px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
    }

    .exam-badge {
        float: right;
        background-color: #d97706;
        color: #ffffff !important;
        padding: 1px 7px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: bold;
    }

    /* Actieknoppen */
    div.stButton > button {
        background-color: #238636;
        color: #ffffff !important;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        padding: 0.5rem 1.2rem;
    }
    div.stButton > button:hover {
        background-color: #2ea043;
    }
    </style>
""", unsafe_allow_html=True)

# --- DIRECTE FUNCTIONELE NAVIGATIEKNOPPEN ---
c_btn1, c_btn2, _ = st.columns([1.2, 1.8, 4])
with c_btn1:
    if st.button("📅 Naar Rooster", key="nav_r"):
        go_to_page("Rooster")
        st.rerun()
with c_btn2:
    if st.button("➕ Afspraak / PTA Inplannen", key="nav_i"):
        go_to_page("Inplannen")
        st.rerun()

st.markdown("---")
events = get_all_events()

# ==========================================
# PAGINA 1: ROOSTER (SOMTODAY GRID)
# ==========================================
if st.session_state['current_page'] == "Rooster":
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title("📅 Somtoday Rooster & Voortgang")
    with col_h2:
        if st.button("➕ Afspraak inplannen", key="top_inplannen"):
            go_to_page("Inplannen")
            st.rerun()

    # Voortgangsbalken per vak
    study_events = [e for e in events if e['type'] == 'study']
    if study_events:
        st.subheader("📊 Voortgang per Vak (% Geleerd)")
        all_subjects = list(set([e['title'] for e in study_events]))
        prog_cols = st.columns(min(len(all_subjects), 3))
        for idx, subj in enumerate(all_subjects):
            with prog_cols[idx % 3]:
                subj_tasks = [t for t in study_events if t['title'] == subj]
                total_t = len(subj_tasks)
                done_t = sum(1 for t in subj_tasks if t['completed'])
                percent = int((done_t / total_t) * 100) if total_t > 0 else 0
                st.markdown(f"**{subj}** ({done_t}/{total_t} taken)")
                st.progress(percent / 100)
        st.markdown("---")

    col_d1, _ = st.columns([1.5, 3])
    with col_d1:
        start_week = st.date_input("Selecteer week (Maandag):", datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday()))

    days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag"]
    hours = list(range(6, 23)) # Uren van 06:00 tot 22:00

    # HTML Grid opbouw
    grid_html = '<div class="grid-container">'
    
    # Header
    grid_html += '<div class="time-col-header"></div>'
    for i, day_name in enumerate(days_nl):
        cur_d = start_week + datetime.timedelta(days=i)
        grid_html += f'<div class="day-header">{day_name} {cur_d.day}</div>'
    
    # Uur-rijen
    for hour in hours:
        grid_html += f'<div class="time-label">{hour:02d}:00</div>'
        for i in range(5):
            cur_d = start_week + datetime.timedelta(days=i)
            cell_items = [e for e in events if e['date'] == cur_d and e['start_hour'] == hour]
            
            grid_html += '<div class="grid-cell">'
            for item in cell_items:
                if item['type'] == 'exam':
                    grid_html += f"""
                    <div class="exam-card">
                        <span class="exam-badge">Toets {item['start_time']}</span>
                        <b style="color:#ffffff;">{item['title']}</b><br>
                        <small style="color:#f0f0f0;">📍 {item.get('location', 'N.v.t.')}</small>
                    </div>
                    """
                else:
                    opacity = "0.45" if item['completed'] else "1.0"
                    grid_html += f"""
                    <div class="agenda-card" style="opacity: {opacity};">
                        <span class="time-badge">{item['start_time']}</span>
                        <b style="color:#ffffff;">{item['title']}</b><br>
                        <small style="color:#f0f0f0;">{item['topic']}</small>
                    </div>
                    """
            grid_html += '</div>'
            
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # Interactieve checkboxes
    st.markdown("### 📋 Studietaken Afvinken")
    if study_events:
        for item in study_events:
            is_comp = st.checkbox(f"Gereed: {item['title']} — {item['topic']} op {item['date'].strftime('%d-%m')} om {item['start_time']}", value=item['completed'], key=f"cb_{item['id']}")
            if is_comp != item['completed']:
                update_task_completion(item['id'], is_comp)
                st.rerun()
    else:
        st.info("Geen studietaken ingepland in deze periode.")

# ==========================================
# PAGINA 2: INPLANNEN FORMULIER
# ==========================================
elif st.session_state['current_page'] == "Inplannen":
    st.title("➕ Nieuwe PTA Toets of Studeersessie Inplannen")
    st.write("Oefentaken worden automatisch tussen **16:00 en 22:00 uur** ingepland zonder overlappingen.")

    st.markdown("---")

    with st.form("exam_input_form"):
        st.header("1. Toets Gegevens")
        
        col1, col2 = st.columns(2)
        with col1:
            exam_title = st.selectbox("Selecteer Vak / PTA:", ALLOWED_SUBJECTS)
            exam_date = st.date_input("Datum van de PTA/Toets:", datetime.date.today() + datetime.timedelta(days=7))
            exam_time = st.time_input("Begintijd van de toets:", datetime.time(9, 0))

        with col2:
            location = st.text_input("Lokaal / Ruimte:", "f103")
            exam_duration = st.number_input("Tijdsduur van de toets (in uren):", min_value=0.5, max_value=8.0, value=1.0, step=0.5)

        st.header("2. Stof & Screenshot")
        uploaded_file = st.file_uploader("Upload eventueel een screenshot van je PTA:", type=["png", "jpg", "jpeg"])
        
        default_text = "Hoofdstuk 1, Hoofdstuk 2, Paragraaf 3.1, Paragraaf 3.2, Oefentoets maken"
        raw_topics = st.text_area("Onderwerpen/Hoofdstukken (gescheiden door komma):", default_text)

        st.header("3. Planningsperiode & Studiedagen")
        start_date = st.date_input("Startdatum met leren:", datetime.date.today())

        st.write("Op welke dagen wil je studeren (tussen 16:00 en 22:00)?")
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: m = st.checkbox("Maandag", value=True)
        with c2: di = st.checkbox("Dinsdag", value=True)
        with c3: wo = st.checkbox("Woensdag", value=True)
        with c4: do = st.checkbox("Donderdag", value=True)
        with c5: vr = st.checkbox("Vrijdag", value=True)
        with c6: za = st.checkbox("Zaterdag", value=False)
        with c7: zo = st.checkbox("Zondag", value=False)

        submit_button = st.form_submit_button(label="🚀 Genereer & Opslaan in Database")

    if submit_button:
        topics_list = [t.strip() for t in raw_topics.split(",") if t.strip()]
        
        if not topics_list:
            st.error("Voer ten minste één onderwerp of hoofdstuk in!")
        elif start_date >= exam_date:
            st.error("De toetsdatum moet ná de startdatum liggen.")
        else:
            study_days = {
                "Maandag": m, "Dinsdag": di, "Woensdag": wo, "Donderdag": do,
                "Vrijdag": vr, "Zaterdag": za, "Zondag": zo
            }
            
            cur_d = start_date
            valid_dates = []
            days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
            
            while cur_d < exam_date:
                day_name = days_nl[cur_d.weekday()]
                if study_days.get(day_name, False):
                    valid_dates.append(cur_d)
                cur_d += datetime.timedelta(days=1)

            if not valid_dates:
                st.warning("Geen geldige studiedagen geselecteerd binnen deze periode!")
            else:
                allowed_study_hours = [16, 17, 18, 19, 20, 21]
                existing_events = get_all_events()
                busy_slots = set()
                for ev in existing_events:
                    busy_slots.add((ev['date'], ev['start_hour']))

                for topic in topics_list:
                    scheduled = False
                    for date in valid_dates:
                        if scheduled:
                            break
                        for h in allowed_study_hours:
                            if (date, h) not in busy_slots:
                                task_id = f"{exam_title}_{date}_{h}_{topic}".replace(" ", "_")
                                start_time_str = f"{h:02d}:00"
                                
                                new_task = {
                                    "id": task_id,
                                    "type": "study",
                                    "title": exam_title,
                                    "topic": topic,
                                    "date": date,
                                    "start_hour": h,
                                    "start_time": start_time_str,
                                    "duration": 1.0,
                                    "location": "Thuis",
                                    "completed": 0
                                }
                                save_event_to_db(new_task)
                                busy_slots.add((date, h))
                                scheduled = True
                                break

                # Toets opslaan
                exam_task_id = f"exam_{exam_title}_{exam_date}".replace(" ", "_")
                exam_event = {
                    "id": exam_task_id,
                    "type": "exam",
                    "title": exam_title,
                    "topic": "PTA Toets",
                    "date": exam_date,
                    "start_hour": exam_time.hour,
                    "start_time": exam_time.strftime("%H:%M"),
                    "duration": exam_duration,
                    "location": location if location else "N.v.t.",
                    "completed": 0
                }
                save_event_to_db(exam_event)

                st.success("🎉 Succesvol ingepland! Alle oefentaken zijn slim verdeeld tussen 16:00 en 22:00 uur.")
                go_to_page("Rooster")
                st.rerun()
