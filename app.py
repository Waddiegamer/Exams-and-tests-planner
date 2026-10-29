import streamlit as st
import datetime
import math
import sqlite3

# --- PAGINA CONFIGURATIE ---
st.set_page_config(
    page_title="Somtoday Rooster & PTA Planner",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DATABASE INITIALISATIE ---
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
    "Engelse taal en literatuur": "#2e7d32",
    "Duitse taal en literatuur": "#4e342e",
    "Nederlands": "#c62828",
    "Nederlandse taal en literatuur": "#c62828",
    "Godsdienst": "#00838f",
    "Natuurkunde": "#4527a0",
    "Scheikunde": "#ad1457",
    "Nat leven techniek": "#ff8f00"
}

def get_color(subject):
    return SUBJECT_COLORS.get(subject, "#58a6ff")

# --- STYLING (STRIKTE BREEDTE- EN HOOGTEBEVEILIGING) ---
st.markdown("""
    <style>
    .grid-container {
        display: grid;
        grid-template-columns: 65px repeat(5, 1fr);
        background-color: #12151a;
        border: 1px solid #232a35;
        border-radius: 6px;
        overflow: hidden;
    }
    .day-header {
        background-color: #1a1e26;
        color: #ffffff;
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
        color: #a0aec0;
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
        max-height: 65px;
        border-bottom: 1px solid #1e242d;
        border-right: 1px solid #30363d;
        padding: 2px;
        position: relative;
        background-color: #12151a;
        overflow: hidden;
        box-sizing: border-box;
    }
    .agenda-card {
        background-color: #263242;
        border-radius: 4px;
        padding: 2px 4px;
        color: #ffffff;
        font-size: 0.70rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.4);
        position: absolute;
        left: 2px;
        right: 2px;
        box-sizing: border-box;
        z-index: 2;
        height: 28px;
        max-height: 28px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .exam-card {
        background-color: #263242;
        border-radius: 4px;
        padding: 3px 6px;
        color: #ffffff;
        font-size: 0.74rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
        position: relative;
        z-index: 2;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        overflow: hidden;
    }
    .time-badge {
        float: right;
        background-color: rgba(0,0,0,0.35);
        color: #ffffff;
        padding: 0px 3px;
        border-radius: 4px;
        font-size: 0.55rem;
        font-weight: bold;
    }
    .exam-badge {
        float: right;
        background-color: #d97706;
        color: #ffffff;
        padding: 1px 5px;
        border-radius: 8px;
        font-size: 0.65rem;
        font-weight: bold;
    }
    div.stButton > button {
        background-color: #238636 !important;
        color: #ffffff !important;
        border-radius: 6px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.6rem 1.5rem !important;
    }
    div.stButton > button:hover {
        background-color: #2ea043 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATIE ---
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
# PAGINA 1: ROOSTER
# ==========================================
if st.session_state['current_page'] == "Rooster":
    col_h1, col_h2, col_h3 = st.columns([2, 1, 1])
    with col_h1:
        st.title("📅 Somtoday Rooster & Voortgang")
    with col_h2:
        if st.button("➕ Afspraak inplannen", key="top_inplannen"):
            go_to_page("Inplannen")
            st.rerun()
    with col_h3:
        if st.button("🗑️ Wis alle taken", key="clear_db_btn"):
            conn = sqlite3.connect('planner.db')
            c = conn.cursor()
            c.execute('DELETE FROM events')
            conn.commit()
            conn.close()
            st.success("Alle taken gewist!")
            st.rerun()

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
    hours = list(range(8, 23))

    grid_html = '<div class="grid-container">'
    grid_html += '<div class="time-col-header"></div>'
    for i, day_name in enumerate(days_nl):
        cur_d = start_week + datetime.timedelta(days=i)
        grid_html += f'<div class="day-header">{day_name} {cur_d.day}</div>'
    
    for hour in hours:
        grid_html += f'<div class="time-label">{hour:02d}:00</div>'
        for i in range(5):
            cur_d = start_week + datetime.timedelta(days=i)
            cell_items = [e for e in events if e['date'] == cur_d and e['start_hour'] == hour]
            
            grid_html += '<div class="grid-cell">'
            for item in cell_items:
                subject_color = get_color(item['title'])
                try:
                    time_parts = item['start_time'].split(':')
                    minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
                except:
                    minutes = 0
                
                if minutes >= 30:
                    margin_top_px = 32
                else:
                    margin_top_px = 2
                
                if item['type'] == 'exam':
                    grid_html += f"""
                    <div class="exam-card" style="border-left: 4px solid {subject_color};">
                        <span class="exam-badge">Toets {item['start_time']}</span>
                        <b style="color:#ffffff;">🔴 {item['title']}</b><br>
                        <small style="color:#f0f0f0;">📍 {item.get('location', 'N.v.t.')}</small>
                    </div>
                    """
                else:
                    opacity = "0.45" if item['completed'] else "1.0"
                    grid_html += f"""
                    <div class="agenda-card" style="opacity: {opacity}; border-left: 4px solid {subject_color}; top: {margin_top_px}px;">
                        <span class="time-badge">{item['start_time']}</span>
                        <b style="color:#ffffff;">{item['title']}</b>: <span style="color:#f0f0f0;">{item['topic']}</span>
                    </div>
                    """
            grid_html += '</div>'
            
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    st.markdown("### 📋 Studietaken Afvinken per Vak")
    if study_events:
        subjects_in_db = sorted(list(set([e['title'] for e in study_events])))
        for subj in subjects_in_db:
            subj_tasks = [e for e in study_events if e['title'] == subj]
            done_count = sum(1 for e in subj_tasks if e['completed'])
            total_count = len(subj_tasks)
            
            with st.expander(f"📚 **{subj}** — ({done_count}/{total_count} afgevinkt)", expanded=False):
                for item in sorted(subj_tasks, key=lambda x: (x['date'], x['start_hour'], x['start_time'])):
                    is_comp = st.checkbox(
                        f"**{item['topic']}** — {item['date'].strftime('%d-%m-%Y')} om {item['start_time']} (30 min)", 
                        value=item['completed'], 
                        key=f"cb_{item['id']}"
                    )
                    if is_comp != item['completed']:
                        update_task_completion(item['id'], is_comp)
                        st.rerun()
    else:
        st.info("Er zijn op dit moment geen studietaken ingepland.")

# ==========================================
# PAGINA 2: INPLANNEN FORMULIER
# ==========================================
elif st.session_state['current_page'] == "Inplannen":
    st.title("➕ Nieuwe PTA Toets of Studeersessie Inplannen")
    st.write("Elk onderwerp wordt gegarandeerd **minimaal 2 keer** evenredig verspreid over de beschikbare studiedagen (in halve blokken van 30 min tussen 16:00 en 22:00).")

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

        st.header("2. Stof & Hoofdstukken")
        default_text = "Hoofdstuk 1, Hoofdstuk 2, Paragraaf 3.1, Paragraaf 3.2, Oefentoets maken"
        raw_topics = st.text_area("Onderwerpen/Hoofdstukken (gescheiden door komma):", default_text)

        st.header("3. Planningsperiode & Studiedagen")
        start_date = st.date_input("Startdatum met leren (vandaag of later):", datetime.date.today())

        st.write("Op welke dagen wil je studeren (tussen 16:00 en 22:00)?")
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: m = st.checkbox("Maandag", value=True)
        with c2: di = st.checkbox("Dinsdag", value=True)
        with c3: wo = st.checkbox("Woensdag", value=True)
        with c4: do = st.checkbox("Donderdag", value=True)
        with c5: vr = st.checkbox("Vrijdag", value=True)
        with c6: za = st.checkbox("Zaterdag", value=False)
        with c7: zo = st.checkbox("Zondag", value=False)

        submit_button = st.form_submit_button(label="🚀 Alles Wissen, Perfect Spreiden & Opslaan")

    if submit_button:
        topics_list = [t.strip() for t in raw_topics.split(",") if t.strip()]
        
        if not topics_list:
            st.error("Voer ten minste één onderwerp of hoofdstuk in!")
        elif start_date >= exam_date:
            st.error("De toetsdatum moet ná de startdatum liggen.")
        else:
            conn = sqlite3.connect('planner.db')
            c = conn.cursor()
            c.execute('DELETE FROM events')
            conn.commit()
            conn.close()

            study_days = {
                "Maandag": m, "Dinsdag": di, "Woensdag": wo, "Donderdag": do,
                "Vrijdag": vr, "Zaterdag": za, "Zondag": zo
            }
            
            today = datetime.date.today()
            effective_start = max(start_date, today)
            
            cur_d = effective_start
            valid_dates = []
            days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
            
            while cur_d < exam_date:
                day_name = days_nl[cur_d.weekday()]
                if study_days.get(day_name, False):
                    valid_dates.append(cur_d)
                cur_d += datetime.timedelta(days=1)

            if not valid_dates:
                st.warning("Geen geldige studiedagen geselecteerd in de periode voor de toets!")
            else:
                allowed_study_slots = []
                for h in range(16, 22):
                    allowed_study_slots.append((h, 0))
                    allowed_study_slots.append((h, 30))

                busy_slots = set()

                tasks_to_schedule = []
                for topic in topics_list:
                    tasks_to_schedule.append(f"{topic} (Deel 1)")
                    tasks_to_schedule.append(f"{topic} (Deel 2 - Herhaling)")

                num_days = len(valid_dates)
                total_tasks = len(tasks_to_schedule)

                for idx, task_title in enumerate(tasks_to_schedule):
                    ideal_day_index = int((idx / total_tasks) * num_days)
                    scheduled = False
                    
                    for offset in range(num_days):
                        for direction in [1, -1]:
                            day_idx = (ideal_day_index + (offset * direction)) % num_days
                            target_date = valid_dates[day_idx]
                            
                            for (h, m_val) in allowed_study_slots:
                                if (target_date, h, m_val) not in busy_slots:
                                    task_id = f"{exam_title}_{target_date}_{h}_{m_val}_{task_title}_{idx}".replace(" ", "_").replace("(", "").replace(")", "")
                                    start_time_str = f"{h:02d}:{m_val:02d}"
                                    
                                    new_task = {
                                        "id": task_id,
                                        "type": "study",
                                        "title": exam_title,
                                        "topic": task_title,
                                        "date": target_date,
                                        "start_hour": h,
                                        "start_time": start_time_str,
                                        "duration": 0.5,
                                        "location": "Thuis",
                                        "completed": 0
                                    }
                                    save_event_to_db(new_task)
                                    busy_slots.add((target_date, h, m_val))
                                    scheduled = True
                                    break
                            if scheduled:
                                break
                        if scheduled:
                            break

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

                st.success("🎉 Perfect gespreid! Alle onderwerpen zijn minimaal 2 keer evenredig over de dagen verdeeld.")
                go_to_page("Rooster")
                st.rerun()
