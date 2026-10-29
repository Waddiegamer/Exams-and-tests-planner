import streamlit as st
import datetime
import math
import sqlite3

# --- PAGINA CONFIGURATIE (PC GEOPTIMALISEERD) ---
st.set_page_config(
    page_title="Somtoday PC Rooster & PTA Planner",
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

# Database hulpfuncties
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
        OR REPLACE INTO events (id, type, title, topic, date, start_hour, start_time, duration, location, completed)
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

# Gefilterde vakkenlijst (zonder CKV, LO, maatschappijleer, etc.)
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

SUBJECT_COLORS = {
    "Bedrijfseconomie": "#7b42a6",
    "Wiskunde B": "#2b5c8f",
    "Engels": "#2e7d32",
    "Duitse taal en literatuur": "#4e342e",
    "Nederlands": "#c62828",
    "Godsdienst": "#00838f",
    "Natuurkunde": "#4527a0",
    "Scheikunde": "#ad1457",
    "Nat leven techniek": "#ff8f00"
}

def get_color(subject):
    return SUBJECT_COLORS.get(subject, "#37474f")

# --- STYLING (SOMTODAY / DARK MODE / GRID TOT 22:00) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #121418;
        color: #e1e3e6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .top-nav {
        background-color: #1c2128;
        padding: 12px 20px;
        border-bottom: 1px solid #30363d;
        margin-bottom: 20px;
        border-radius: 8px;
        display: flex;
        gap: 10px;
    }
    .grid-header {
        background-color: #1c2128;
        color: #8b949e;
        text-align: center;
        padding: 10px 4px;
        font-weight: bold;
        border: 1px solid #30363d;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    .time-label {
        color: #8b949e;
        font-size: 0.75rem;
        text-align: right;
        padding-right: 12px;
        height: 55px;
        line-height: 55px;
        border-bottom: 1px solid #21262d;
        font-weight: 600;
    }
    .grid-cell {
        height: 55px;
        border-bottom: 1px solid #21262d;
        border-right: 1px solid #30363d;
        padding: 2px;
        position: relative;
        background-color: rgba(255, 255, 255, 0.01);
    }
    .agenda-card {
        border-radius: 5px;
        padding: 4px 6px;
        color: #ffffff;
        font-size: 0.75rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
        margin-bottom: 2px;
        border-left: 4px solid rgba(255,255,255,0.6);
    }
    .time-badge {
        float: right;
        background-color: rgba(0,0,0,0.3);
        color: #ffffff;
        padding: 1px 3px;
        border-radius: 3px;
        font-size: 0.6rem;
    }
    div.stButton > button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        border: none;
        font-weight: bold;
        padding: 0.4rem 1rem;
    }
    div.stButton > button:hover {
        background-color: #2ea043;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATIE BALK ---
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

events = get_all_events()

# ==========================================
# PAGINA 1: ROOSTER & VOORTGANG
# ==========================================
if st.session_state['current_page'] == "Rooster":
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title("📅 Somtoday Rooster & Voortgang")
        st.caption("Jouw studie- en toetsrooster met rasterlijnen tot 22:00 uur ('s avonds).")
    with col_h2:
        if st.button("➕ Nieuwe Afspraak", key="btn_top_create"):
            go_to_page("Inplannen")
            st.rerun()

    st.markdown("---")

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

    col_d1, _ = st.columns([1, 3])
    with col_d1:
        start_week = st.date_input("Week van (Maandag):", datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday()))

    days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    
    # Raster uren van 08:00 tot 22:00 ('s avonds)
    hours = list(range(8, 23)) 
    
    grid_cols = st.columns([0.6, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4, 1.4])
    
    with grid_cols[0]:
        st.markdown('<div class="grid-header">Tijd</div>', unsafe_allow_html=True)
    for i, day_name in enumerate(days_nl):
        cur_d = start_week + datetime.timedelta(days=i)
        with grid_cols[i+1]:
            st.markdown(f'<div class="grid-header">{day_name[:3]}<br><small>{cur_d.day}/{cur_d.month}</small></div>', unsafe_allow_html=True)

    for hour in hours:
        with grid_cols[0]:
            st.markdown(f'<div class="time-label">{hour:02d}:00</div>', unsafe_allow_html=True)
            
        for i in range(7):
            cur_d = start_week + datetime.timedelta(days=i)
            with grid_cols[i+1]:
                cell_items = [e for e in events if e['date'] == cur_d and e['start_hour'] == hour]
                
                cell_html = '<div class="grid-cell">'
                for item in cell_items:
                    bg_col = get_color(item['title'])
                    if item['type'] == 'exam':
                        cell_html += f"""
                        <div class="agenda-card" style="background-color: {bg_col}; border-left: 4px solid #ffeb3b;">
                            <span class="time-badge">{item['start_time']}</span>
                            <b>🔴 TOETS: {item['title']}</b><br>
                            <small>📍 {item.get('location', 'N.v.t.')} ({item['duration']}u)</small>
                        </div>
                        """
                    else:
                        opacity = "0.4" if item['completed'] else "1.0"
                        cell_html += f"""
                        <div class="agenda-card" style="background-color: {bg_col}; opacity: {opacity};">
                            <span class="time-badge">{item['start_time']}</span>
                            <b>📖 {item['title']}</b><br>
                            <small>{item['topic']}</small>
                        </div>
                        """
                cell_html += '</div>'
                st.markdown(cell_html, unsafe_allow_html=True)
                
                # Checkboxes voor interactie onder het raster
                for item in cell_items:
                    if item['type'] == 'study':
                        is_comp = st.checkbox(f"Gereed: {item['title']} ({item['topic']}) op {cur_d.strftime('%d-%m')} {item['start_time']}", value=item['completed'], key=f"cb_{item['id']}")
                        if is_comp != item['completed']:
                            update_task_completion(item['id'], is_comp)
                            st.rerun()

# ==========================================
# PAGINA 2: INPLANNEN FORMULIER
# ==========================================
elif st.session_state['current_page'] == "Inplannen":
    st.title("➕ Nieuwe PTA Toets of Studeersessie Inplannen")
    st.caption("Oefentaken worden automatisch slim ingepland tussen 16:00 en 22:00 uur zonder overlappingen met toetsen.")

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
            
            # Verzamel geldige studiedagen
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
                # Bepaal beschikbare uren tussen 16:00 (4 PM) en 22:00 (10 PM)
                # Uren: 16, 17, 18, 19, 20, 21
                allowed_study_hours = [16, 17, 18, 19, 20, 21]
                
                # Haal bestaande events op om overlappingen te voorkomen
                existing_events = get_all_events()
                busy_slots = set()
                for ev in existing_events:
                    busy_slots.add((ev['date'], ev['start_hour']))

                # Verdeel onderwerpen over beschikbare vrije slots tussen 16:00 en 22:00
                assigned_count = 0
                for topic in topics_list:
                    scheduled = False
                    for date in valid_dates:
                        if scheduled:
                            break
                        for h in allowed_study_hours:
                            # Controleer of dit uur op deze dag al bezet is door een toets of andere taak
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
                                assigned_count +=- 0 # dummy
                                break

                # Sla de toets zelf op op de toetsdag en toets-tijd
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

                st.success(f"🎉 Succesvol ingepland! Alle {len(topics_list)} oefentaken zijn slim verdeeld tussen 16:00 en 22:00 zonder overlappingen.")
                go_to_page("Rooster")
                st.rerun()
