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

# Gefilterde vakkenlijst op basis van jouw screenshot
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
    "Bedrijfseconomie": "#2c3b53",
    "Wiskunde B": "#243b55",
    "Engels": "#1e3d2f",
    "Duitse taal en literatuur": "#3d2c29",
    "Nederlands": "#4a2828",
    "Godsdienst": "#1c3d42",
    "Natuurkunde": "#312247",
    "Scheikunde": "#421c38",
    "Nat leven techniek": "#42381c"
}

def get_color(subject):
    return SUBJECT_COLORS.get(subject, "#2b3440")

# --- SOMTODAY STYLING ---
st.markdown("""
    <style>
    .stApp {
        background-color: #161922;
        color: #e1e4e8;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Somtoday Navigatiebalk */
    .somtoday-nav {
        background-color: #1e222d;
        padding: 8px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #2a2f3d;
        margin-bottom: 15px;
        border-radius: 4px;
    }
    
    .nav-tabs {
        display: flex;
        gap: 20px;
        font-size: 0.95rem;
        font-weight: 500;
        color: #8b949e;
    }
    
    .nav-tab-active {
        color: #ffffff;
        border-bottom: 2px solid #58a6ff;
        padding-bottom: 4px;
    }

    /* Rooster Grid Naadloos Aansluitend */
    .grid-container {
        display: grid;
        grid-template-columns: 60px repeat(5, 1fr);
        background-color: #161922;
        border-top: 1px solid #2a2f3d;
    }
    
    .day-header {
        background-color: #1e222d;
        color: #c9d1d9;
        text-align: center;
        padding: 10px 4px;
        font-weight: 600;
        border-right: 1px solid #2a2f3d;
        border-bottom: 1px solid #2a2f3d;
        font-size: 0.9rem;
    }
    
    .time-col-header {
        background-color: #1e222d;
        border-right: 1px solid #2a2f3d;
        border-bottom: 1px solid #2a2f3d;
    }

    .time-label {
        color: #8b949e;
        font-size: 0.75rem;
        text-align: right;
        padding-right: 8px;
        height: 60px;
        line-height: 60px;
        border-bottom: 1px solid #21262d;
        border-right: 1px solid #2a2f3d;
        background-color: #161922;
        font-weight: 500;
    }
    
    .grid-cell {
        height: 60px;
        border-bottom: 1px solid #21262d;
        border-right: 1px solid #2a2f3d;
        padding: 2px;
        position: relative;
        background-color: #161922;
    }

    /* Les & Toets Kaarten in Somtoday stijl */
    .agenda-card {
        border-radius: 4px;
        padding: 5px 8px;
        color: #ffffff;
        font-size: 0.78rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 2px;
        position: relative;
    }
    
    .time-badge {
        float: right;
        background-color: rgba(0, 0, 0, 0.35);
        color: #ffffff;
        padding: 1px 5px;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 600;
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

# --- SOMTODAY BOVENBALK ---
st.markdown("""
    <div class="somtoday-nav">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="background: #30363d; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #fff;">👤</div>
            <div class="nav-tabs">
                <span class="nav-tab-active">📅 Rooster</span>
                <span>📚 Studiewijzer</span>
                <span>📊 Cijfers</span>
                <span>💬 Berichten</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Navigatie knoppen binnen Streamlit
c_btn1, c_btn2, _ = st.columns([1, 1.5, 4])
with c_btn1:
    if st.button("📅 Naar Rooster", key="nav_r"):
        go_to_page("Rooster")
        st.rerun()
with c_btn2:
    if st.button("➕ Afspraak / Inplannen", key="nav_i"):
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
        st.title("📅 Rooster & Voortgang")
        st.caption("Jouw complete school- en oefenrooster in Somtoday-stijl (tot 22:00 uur).")
    with col_h2:
        if st.button("➕ Afspraak inplannen", key="top_inplannen"):
            go_to_page("Inplannen")
            st.rerun()

    st.markdown("---")

    # Voortgangsbalken
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

    days_nl = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag"]
    hours = list(range(6, 23)) # Van 06:00 tot 22:00 uur

    # HTML Grid opbouw voor naadloos aansluitende dagen
    grid_html = '<div class="grid-container">'
    
    # Header rij
    grid_html += '<div class="time-col-header"></div>'
    for i, day_name in enumerate(days_nl):
        cur_d = start_week + datetime.timedelta(days=i)
        grid_html += f'<div class="day-header">{day_name}<br><span style="font-size:0.75rem; color:#8b949e;">{cur_d.day}/{cur_d.month}</span></div>'
    
    # Uur rijen
    for hour in hours:
        grid_html += f'<div class="time-label">{hour:02d}:00</div>'
        for i in range(5):
            cur_d = start_week + datetime.timedelta(days=i)
            cell_items = [e for e in events if e['date'] == cur_d and e['start_hour'] == hour]
            
            grid_html += '<div class="grid-cell">'
            for item in cell_items:
                bg_col = get_color(item['title'])
                if item['type'] == 'exam':
                    grid_html += f"""
                    <div class="agenda-card" style="background-color: {bg_col}; border-left: 4px solid #f1e05a;">
                        <span class="time-badge">Toets {item['start_time']}</span>
                        <b>🔴 {item['title']}</b><br>
                        <small>📍 {item.get('location', 'N.v.t.')}</small>
                    </div>
                    """
                else:
                    opacity = "0.4" if item['completed'] else "1.0"
                    grid_html += f"""
                    <div class="agenda-card" style="background-color: {bg_col}; opacity: {opacity}; border-left: 4px solid #58a6ff;">
                        <span class="time-badge">{item['start_time']}</span>
                        <b>📖 {item['title']}</b><br>
                        <small>{item['topic']}</small>
                    </div>
                    """
            grid_html += '</div>'
            
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)

    # Interaktieve checkboxes voor studietaken onder het rooster
    st.markdown("### 📋 Studietaken Afvinken")
    if study_events:
        for item in study_events:
            is_comp = st.checkbox(f"Gereed: {item['title']} — *{item['topic']}* op {item['date'].strftime('%d-%m')} om {item['start_time']}", value=item['completed'], key=f"cb_{item['id']}")
            if is_comp != item['completed']:
                update_task_completion(item['id'], is_comp)
                st.rerun()
    else:
        st.info("Geen studietaken ingepland in deze week.")

# ==========================================
# PAGINA 2: INPLANNEN FORMULIER
# ==========================================
elif st.session_state['current_page'] == "Inplannen":
    st.title("➕ Nieuwe PTA Toets of Studeersessie Inplannen")
    st.caption("Oefentaken worden automatisch slim ingepland tussen 16:00 en 22:00 uur zonder overlappingen.")

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
                # Studeren uren uitsluitend tussen 16:00 (4 PM) en 21:00 (laatste blok 21:00 tot 22:00)
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

                st.success(f"🎉 Succesvol ingepland! Alle oefentaken zijn slim verdeeld tussen 16:00 en 22:00 uur.")
                go_to_page("Rooster")
                st.rerun()
