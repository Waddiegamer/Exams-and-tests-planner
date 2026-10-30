from __future__ import annotations

import datetime as dt
import html
import hmac
import json
import os
import sqlite3
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from planner_logic import (
    APP_TIMEZONE, PRIORITIES, build_slots, create_balanced_study_plan,
    events_overlap, make_event, make_ics, reschedule_overdue_tasks,
)

# ---------------------------------------------------------------------
# Page setup and application constants
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="StudySpace | School Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Optional shared-password gate for a private Streamlit deployment.
def require_optional_password() -> None:
    try:
        configured_password = st.secrets.get("app", {}).get("password", "")
    except Exception:
        configured_password = ""
    if not configured_password or st.session_state.get("authenticated", False):
        return
    st.title("📚 StudySpace")
    st.write("Deze planner is beveiligd met een toegangscode.")
    with st.form("access_form"):
        entered_password = st.text_input("Toegangscode", type="password")
        submitted = st.form_submit_button("Inloggen", type="primary")
    if submitted:
        if hmac.compare_digest(entered_password, str(configured_password)):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("De toegangscode is niet juist.")
    st.stop()


require_optional_password()

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "planner.db"
DEFAULT_START = dt.time(16, 0)
DEFAULT_END = dt.time(22, 0)

SUBJECTS = [
    "Bedrijfseconomie",
    "Duitse taal en literatuur",
    "Engelse taal en literatuur",
    "Godsdienst",
    "Nat leven techniek",
    "Natuurkunde",
    "Nederlandse taal en literatuur",
    "Scheikunde",
    "Wiskunde B",
]

SUBJECT_COLORS = {
    "Bedrijfseconomie": "#9B87F5",
    "Duitse taal en literatuur": "#C18B5B",
    "Engelse taal en literatuur": "#36B37E",
    "Godsdienst": "#22A6B3",
    "Nat leven techniek": "#D99A35",
    "Natuurkunde": "#6485E8",
    "Nederlandse taal en literatuur": "#E36B75",
    "Scheikunde": "#D66AB1",
    "Wiskunde B": "#4C9BE8",
}

# ---------------------------------------------------------------------
# Optional Supabase backend. Local SQLite is the development fallback.
# Configure [supabase] url/key in Streamlit secrets to enable cloud storage.
# ---------------------------------------------------------------------
def get_supabase_credentials() -> tuple[str | None, str | None]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    try:
        supabase_secrets = st.secrets.get("supabase", {})
        url = url or supabase_secrets.get("url")
        key = key or supabase_secrets.get("key")
    except Exception:
        # Streamlit secrets are optional for local development.
        pass
    return url, key


@st.cache_resource(show_spinner=False)
def get_supabase_client(url: str, key: str):
    from supabase import create_client
    return create_client(url, key)


def get_backend():
    url, key = get_supabase_credentials()
    if url and key:
        try:
            return "supabase", get_supabase_client(url, key)
        except Exception as exc:
            st.error(
                "Supabase-instellingen zijn gevonden, maar de verbinding kon niet worden gestart. "
                f"Controleer je secrets en package-installatie. Details: {exc}"
            )
    return "sqlite", None


BACKEND, SUPABASE = get_backend()

# ---------------------------------------------------------------------
# Database layer
# ---------------------------------------------------------------------
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=25)
    conn.row_factory = sqlite3.Row
    return conn


def init_sqlite() -> None:
    with db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                topic TEXT NOT NULL DEFAULT '',
                date TEXT NOT NULL,
                start_hour INTEGER NOT NULL DEFAULT 16,
                start_time TEXT NOT NULL,
                duration REAL NOT NULL DEFAULT 0.5,
                location TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                priority TEXT NOT NULL DEFAULT 'Normaal',
                created_at TEXT NOT NULL DEFAULT ''
            )
            """
        )
        # Migrate databases created by the original version in place.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(events)").fetchall()}
        if "priority" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN priority TEXT NOT NULL DEFAULT 'Normaal'")
        if "created_at" not in columns:
            conn.execute("ALTER TABLE events ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date_time ON events(date, start_time)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)")


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    event = dict(raw)
    raw_date = event.get("date")
    if isinstance(raw_date, dt.datetime):
        event["date"] = raw_date.date()
    elif isinstance(raw_date, str):
        event["date"] = dt.date.fromisoformat(raw_date[:10])
    elif not isinstance(raw_date, dt.date):
        raise ValueError(f"Ongeldige datum in afspraak: {raw_date!r}")
    event["id"] = str(event.get("id") or uuid.uuid4())
    event["type"] = event.get("type") or "study"
    event["title"] = str(event.get("title") or "Onbekend vak")
    event["topic"] = str(event.get("topic") or "")
    event["start_time"] = str(event.get("start_time") or "16:00")[:5]
    event["start_hour"] = int(event.get("start_hour", int(event["start_time"][:2])))
    event["duration"] = float(event.get("duration") or 0.5)
    event["location"] = str(event.get("location") or "")
    event["completed"] = bool(event.get("completed", False))
    event["priority"] = event.get("priority") if event.get("priority") in PRIORITIES else "Normaal"
    event["created_at"] = event.get("created_at") or dt.datetime.now(APP_TIMEZONE).isoformat(timespec="seconds")
    return event


def serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    e = normalize_event(event)
    result = dict(e)
    result["date"] = e["date"].isoformat()
    result["completed"] = bool(e["completed"])
    return result


def fetch_events() -> list[dict[str, Any]]:
    if BACKEND == "supabase":
        response = SUPABASE.table("events").select("*").order("date").order("start_time").execute()
        return [normalize_event(row) for row in (response.data or [])]
    with db_connect() as conn:
        rows = conn.execute("SELECT * FROM events ORDER BY date, start_time, title").fetchall()
    return [normalize_event(dict(row)) for row in rows]


def insert_events(events: list[dict[str, Any]]) -> None:
    if not events:
        return
    rows = [serialize_event(e) for e in events]
    if BACKEND == "supabase":
        SUPABASE.table("events").upsert(rows).execute()
        return
    with db_connect() as conn:
        conn.executemany(
            """INSERT INTO events
            (id, type, title, topic, date, start_hour, start_time, duration,
             location, completed, priority, created_at)
            VALUES (:id, :type, :title, :topic, :date, :start_hour, :start_time,
                    :duration, :location, :completed, :priority, :created_at)""",
            [dict(row, completed=int(row["completed"])) for row in rows],
        )


def update_event(event_id: str, changes: dict[str, Any]) -> None:
    payload = dict(changes)
    if "date" in payload and isinstance(payload["date"], dt.date):
        payload["date"] = payload["date"].isoformat()
    if "completed" in payload:
        payload["completed"] = bool(payload["completed"])
    if BACKEND == "supabase":
        SUPABASE.table("events").update(payload).eq("id", event_id).execute()
        return
    allowed = {"date", "start_time", "start_hour", "duration", "location", "completed", "priority", "topic", "title"}
    payload = {k: v for k, v in payload.items() if k in allowed}
    if not payload:
        return
    assignments = ", ".join(f"{key} = ?" for key in payload)
    values = [int(v) if k == "completed" else v for k, v in payload.items()]
    with db_connect() as conn:
        conn.execute(f"UPDATE events SET {assignments} WHERE id = ?", (*values, event_id))


def update_events_batch(events: list[dict[str, Any]]) -> None:
    if not events:
        return
    if BACKEND == "supabase":
        for event in events:
            update_event(event["id"], {
                "date": event["date"],
                "start_time": event["start_time"],
                "start_hour": event["start_hour"],
            })
        return
    with db_connect() as conn:
        conn.executemany(
            "UPDATE events SET date = ?, start_time = ?, start_hour = ? WHERE id = ?",
            [(e["date"].isoformat(), e["start_time"], e["start_hour"], e["id"]) for e in events],
        )


def remove_event(event_id: str) -> None:
    if BACKEND == "supabase":
        SUPABASE.table("events").delete().eq("id", event_id).execute()
    else:
        with db_connect() as conn:
            conn.execute("DELETE FROM events WHERE id = ?", (event_id,))


def upsert_imported_events(events: list[dict[str, Any]]) -> None:
    if not events:
        return
    if BACKEND == "supabase":
        SUPABASE.table("events").upsert([serialize_event(e) for e in events]).execute()
    else:
        with db_connect() as conn:
            conn.executemany(
                """INSERT INTO events
                (id, type, title, topic, date, start_hour, start_time, duration,
                 location, completed, priority, created_at)
                VALUES (:id, :type, :title, :topic, :date, :start_hour, :start_time,
                        :duration, :location, :completed, :priority, :created_at)
                ON CONFLICT(id) DO UPDATE SET
                    type=excluded.type, title=excluded.title, topic=excluded.topic,
                    date=excluded.date, start_hour=excluded.start_hour,
                    start_time=excluded.start_time, duration=excluded.duration,
                    location=excluded.location, completed=excluded.completed,
                    priority=excluded.priority""",
                [dict(serialize_event(e), completed=int(bool(e.get("completed", False)))) for e in events],
            )


init_sqlite() if BACKEND == "sqlite" else None

# ---------------------------------------------------------------------
# Scheduling and calendar utilities
# ---------------------------------------------------------------------
def make_backup_json(events: list[dict[str, Any]]) -> bytes:
    payload = {
        "format": "studyspace-events-v1",
        "exported_at": dt.datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
        "events": [serialize_event(e) for e in events],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------
def apply_theme(theme: str) -> None:
    if theme == "Licht":
        bg, panel, text, muted, border = "#F5F7FB", "#FFFFFF", "#1F2937", "#667085", "#E4E7EC"
        card_bg = "#F8FAFC"
    else:
        bg, panel, text, muted, border = "#0D111B", "#151C2B", "#F3F5FA", "#A6B0C3", "#293247"
        card_bg = "#1B2435"
    st.markdown(f"""
    <style>
      .stApp {{ background: {bg}; color: {text}; }}
      [data-testid="stSidebar"] {{ background: {panel}; border-right: 1px solid {border}; }}
      [data-testid="stMetric"] {{ background: {panel}; border: 1px solid {border}; padding: 14px 16px; border-radius: 14px; }}
      [data-testid="stMetricLabel"] p {{ color: {muted}; }}
      [data-testid="stExpander"] {{ border: 1px solid {border}; border-radius: 12px; }}
      .ss-eyebrow {{ color: {muted}; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; }}
      .ss-event {{ background: {card_bg}; border: 1px solid {border}; border-left: 4px solid var(--subject-color, #8292B8); border-radius: 10px; padding: 10px 11px; margin: 7px 0; }}
      .ss-event-title {{ font-weight: 700; font-size: .93rem; color: {text}; }}
      .ss-event-meta {{ color: {muted}; font-size: .78rem; margin-top: 3px; }}
      .ss-pill {{ display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: .70rem; font-weight: 700; background: {panel}; border: 1px solid {border}; color: {muted}; }}
      .ss-hero {{ padding: 18px 20px; border: 1px solid {border}; border-radius: 16px; background: {panel}; margin-bottom: 10px; }}
      .ss-hero h2 {{ margin: 0 0 4px 0; }}
      div.stButton > button {{ border-radius: 9px; }}
      div[data-testid="stForm"] {{ border: 1px solid {border}; border-radius: 14px; padding: 18px; }}
    </style>
    """, unsafe_allow_html=True)


def safe(value: Any) -> str:
    return html.escape(str(value or ""))


def format_dutch_date(day: dt.date) -> str:
    weekdays_nl = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
    months_nl = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
    return f"{weekdays_nl[day.weekday()]} {day.day} {months_nl[day.month - 1]} {day.year}"


def event_card(event: dict[str, Any]) -> None:
    color = SUBJECT_COLORS.get(event["title"], "#8391A8")
    kind = "Toets" if event["type"] == "exam" else "Studieblok"
    done = " · Afgerond" if event["completed"] else ""
    st.markdown(
        f"""<div class="ss-event" style="--subject-color:{color}">
        <div class="ss-event-meta">{safe(kind)} · {safe(event['start_time'])} · {event['duration']:g} uur</div>
        <div class="ss-event-title">{safe(event['title'])}{' ✓' if event['completed'] else ''}</div>
        <div>{safe(event['topic'])}</div>
        <div class="ss-event-meta">{safe(event['location']) or 'Geen locatie'} · Prioriteit: {safe(event['priority'])}{safe(done)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def filter_events(events: list[dict[str, Any]], subjects: list[str]) -> list[dict[str, Any]]:
    if not subjects:
        return events
    return [event for event in events if event["title"] in subjects]

# ---------------------------------------------------------------------
# Sidebar and global app state
# ---------------------------------------------------------------------
all_events: list[dict[str, Any]] = []
load_error = None
try:
    all_events = fetch_events()
except Exception as exc:
    load_error = str(exc)

with st.sidebar:
    st.markdown("# 📚 StudySpace")
    st.caption("Je schoolwerk, overzichtelijk gepland.")
    page = st.radio(
        "Navigatie",
        ["Dashboard", "Weekplanner", "Planning maken", "Taken", "Statistieken", "Instellingen"],
        label_visibility="collapsed",
    )
    st.divider()
    chosen_theme = st.selectbox("Thema", ["Donker", "Licht"], index=0)
    all_subject_names = sorted(set(e["title"] for e in all_events))
    subject_filter = st.multiselect("Filter op vak", all_subject_names, placeholder="Alle vakken")
    st.divider()
    if BACKEND == "supabase":
        st.markdown("<span class='ss-pill'>Cloud database · Supabase</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='ss-pill'>Lokale database · SQLite</span>", unsafe_allow_html=True)
    st.caption("Tip: koppel Supabase voor opslag die bij Streamlit Cloud blijft bestaan.")

apply_theme(chosen_theme)
if load_error:
    st.error(f"De afspraken konden niet worden geladen: {load_error}")
    st.stop()

visible_events = filter_events(all_events, subject_filter)
today = dt.datetime.now(APP_TIMEZONE).date()
study_events = [e for e in visible_events if e["type"] == "study"]
exam_events = [e for e in visible_events if e["type"] == "exam"]
open_study = [e for e in study_events if not e["completed"]]
completed_study = [e for e in study_events if e["completed"]]

# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------
if page == "Dashboard":
    st.markdown("<div class='ss-eyebrow'>Jouw persoonlijke studieplanner</div>", unsafe_allow_html=True)
    st.title("Dashboard")
    st.caption(format_dutch_date(today))

    upcoming_exams = sorted(
        [e for e in exam_events if e["date"] >= today],
        key=lambda e: (e["date"], e["start_time"]),
    )
    next_exam = upcoming_exams[0] if upcoming_exams else None
    total_hours = sum(e["duration"] for e in study_events)
    completed_hours = sum(e["duration"] for e in completed_study)
    completion_pct = round(100 * len(completed_study) / len(study_events)) if study_events else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Open studietaken", len(open_study))
    m2.metric("Afgerond", f"{completion_pct}%", f"{len(completed_study)} van {len(study_events)}")
    m3.metric("Geplande studietijd", f"{total_hours:g} uur", f"{completed_hours:g} uur afgerond")
    m4.metric("Komende toetsen", len(upcoming_exams))

    if next_exam:
        days_left = (next_exam["date"] - today).days
        st.markdown(
            f"""<div class="ss-hero">
            <div class="ss-eyebrow">Eerstvolgende toets</div>
            <h2>{safe(next_exam['title'])}</h2>
            <div>{safe(format_dutch_date(next_exam['date']))} om {safe(next_exam['start_time'])} · {safe(next_exam['location'])}</div>
            <div style="font-size:1.25rem;font-weight:750;margin-top:8px">Nog {days_left} dagen</div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.info("Er staan geen toekomstige toetsen gepland.")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Eerstvolgende studietaken")
        upcoming_tasks = sorted(
            [e for e in open_study if (e["date"], e["start_time"]) >= (today, dt.datetime.now(APP_TIMEZONE).strftime("%H:%M"))],
            key=lambda e: (e["date"], e["start_time"]),
        )[:5]
        if upcoming_tasks:
            for event in upcoming_tasks:
                with st.container():
                    st.caption(event["date"].strftime("%a %d-%m") + " · " + event["start_time"])
                    event_card(event)
        else:
            st.success("Geen openstaande studietaken meer voor de komende momenten.")
    with right:
        st.subheader("Voortgang per vak")
        subject_rows = []
        for subject in sorted(set(e["title"] for e in study_events)):
            rows = [e for e in study_events if e["title"] == subject]
            subject_rows.append({"Vak": subject, "Afgerond": sum(e["completed"] for e in rows), "Open": sum(not e["completed"] for e in rows)})
        if subject_rows:
            chart_df = pd.DataFrame(subject_rows).set_index("Vak")
            st.bar_chart(chart_df, height=270)
        else:
            st.caption("Voeg een planning toe om je voortgang te zien.")

# ---------------------------------------------------------------------
# Weekly calendar
# ---------------------------------------------------------------------
elif page == "Weekplanner":
    st.title("Weekplanner")
    col_date, col_export = st.columns([2, 1])
    with col_date:
        selected_day = st.date_input("Kies een datum in de week", today - dt.timedelta(days=today.weekday()))
    with col_export:
        st.write("")
        if visible_events:
            st.download_button(
                "📅 Exporteer kalender (.ics)",
                data=make_ics(visible_events),
                file_name="studyspace-kalender.ics",
                mime="text/calendar",
                use_container_width=True,
            )
    monday = selected_day - dt.timedelta(days=selected_day.weekday())
    week_cols = st.columns(7, gap="small")
    day_labels = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
    for index, column in enumerate(week_cols):
        day = monday + dt.timedelta(days=index)
        day_items = sorted(
            [e for e in visible_events if e["date"] == day],
            key=lambda e: e["start_time"],
        )
        with column:
            st.markdown(f"**{day_labels[index]} {day.strftime('%d-%m')}**")
            if day == today:
                st.caption("Vandaag")
            if not day_items:
                st.caption("—")
            for event in day_items:
                event_card(event)

    st.divider()
    st.subheader("Agenda van deze week")
    week_events = sorted(
        [e for e in visible_events if monday <= e["date"] < monday + dt.timedelta(days=7)],
        key=lambda e: (e["date"], e["start_time"]),
    )
    if week_events:
        agenda_data = [{
            "Datum": e["date"].strftime("%d-%m-%Y"),
            "Tijd": e["start_time"],
            "Type": "Toets" if e["type"] == "exam" else "Studeren",
            "Vak": e["title"],
            "Onderwerp": e["topic"],
            "Duur (uur)": e["duration"],
            "Prioriteit": e["priority"],
            "Afgerond": "Ja" if e["completed"] else "Nee",
        } for e in week_events]
        st.dataframe(pd.DataFrame(agenda_data), use_container_width=True, hide_index=True)
    else:
        st.info("Geen afspraken in deze week.")

# ---------------------------------------------------------------------
# Create a study plan and exam
# ---------------------------------------------------------------------
elif page == "Planning maken":
    st.title("Nieuwe toetsplanning")
    st.write("Plan een toets en laat twee studieblokken per onderwerp automatisch spreiden over je beschikbare dagen.")
    with st.form("new_exam_plan", clear_on_submit=False):
        st.subheader("Toetsgegevens")
        c1, c2 = st.columns(2)
        with c1:
            subject = st.selectbox("Vak", SUBJECTS)
            exam_date = st.date_input("Toetsdatum", today + dt.timedelta(days=7), min_value=today + dt.timedelta(days=1))
            exam_time = st.time_input("Begintijd", dt.time(9, 0), step=dt.timedelta(minutes=15))
        with c2:
            location = st.text_input("Lokaal", placeholder="Bijvoorbeeld F103")
            exam_duration = st.number_input("Duur toets (uren)", min_value=0.5, max_value=8.0, value=1.0, step=0.5)
            priority = st.select_slider("Prioriteit", options=PRIORITIES, value="Normaal")

        st.subheader("Onderwerpen")
        topics_text = st.text_area(
            "Onderwerpen (scheid met komma's of zet elk onderwerp op een nieuwe regel)",
            placeholder="Hoofdstuk 1, Hoofdstuk 2, Paragraaf 3.1",
            height=100,
        )
        st.subheader("Studieperiode")
        c3, c4, c5 = st.columns(3)
        with c3:
            start_date = st.date_input("Start met leren", today, min_value=today)
        with c4:
            study_start = st.time_input("Beschikbaar vanaf", DEFAULT_START, step=dt.timedelta(minutes=30))
        with c5:
            study_end = st.time_input("Beschikbaar tot", DEFAULT_END, step=dt.timedelta(minutes=30))
        st.write("Op welke dagen kun je studeren?")
        weekday_options = [("Maandag", 0), ("Dinsdag", 1), ("Woensdag", 2), ("Donderdag", 3), ("Vrijdag", 4), ("Zaterdag", 5), ("Zondag", 6)]
        weekday_cols = st.columns(7)
        chosen_weekdays = set()
        default_days = {0, 1, 2, 3, 4}
        for col, (label, value) in zip(weekday_cols, weekday_options):
            with col:
                if st.checkbox(label[:2], value=value in default_days, key=f"plan_day_{value}"):
                    chosen_weekdays.add(value)
        submitted = st.form_submit_button("Maak en bewaar planning", type="primary", use_container_width=True)

    if submitted:
        topics = list(dict.fromkeys(
            topic.strip() for topic in topics_text.replace("\n", ",").split(",") if topic.strip()
        ))
        if not topics:
            st.error("Vul minimaal één onderwerp in.")
        elif not chosen_weekdays:
            st.error("Selecteer ten minste één studiedag.")
        elif study_end <= study_start:
            st.error("De eindtijd moet na de starttijd liggen.")
        elif study_start.minute not in (0, 30) or study_end.minute not in (0, 30):
            st.error("Kies voor de studieperiode hele of halve uren.")
        else:
            exam_event = make_event("exam", subject, "PTA / toets", exam_date, exam_time, exam_duration, location.strip(), priority)
            exam_conflicts = [e for e in all_events if events_overlap(exam_event, e)]
            if exam_conflicts:
                st.error("De toets overlapt met een bestaande afspraak: " + ", ".join(f"{e['title']} ({e['date']} {e['start_time']})" for e in exam_conflicts[:3]))
            elif any(e["type"] == "exam" and e["title"] == subject and e["date"] == exam_date and e["start_time"] == exam_time.strftime("%H:%M") for e in all_events):
                st.error("Er bestaat al een toets voor dit vak op deze datum en tijd.")
            elif start_date >= exam_date:
                st.error("De startdatum moet vóór de toetsdatum liggen.")
            else:
                planned, required, capacity = create_balanced_study_plan(
                    subject, topics, start_date, exam_date, chosen_weekdays,
                    study_start, study_end, priority, all_events, exam_event,
                )
                if len(planned) != required:
                    st.error(
                        f"Niet genoeg vrije studietijd: {required} blokken nodig, "
                        f"{capacity} vrije blokken beschikbaar. Start eerder, voeg dagen/tijd toe of verminder onderwerpen."
                    )
                else:
                    try:
                        insert_events(planned + [exam_event])
                        st.success(f"Opgeslagen: {len(planned)} studieblokken en 1 toets. Bestaande afspraken zijn behouden.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Opslaan is niet gelukt: {exc}")

# ---------------------------------------------------------------------
# Task manager, priorities, individual actions and automatic rescheduling
# ---------------------------------------------------------------------
elif page == "Taken":
    st.title("Taken beheren")
    if not visible_events:
        st.info("Geen afspraken gevonden met het huidige vakfilter.")
    else:
        status_filter = st.radio(
            "Weergeven", ["Alles", "Open", "Afgerond", "Toetsen"],
            index=0, horizontal=True,
        )
        shown = visible_events
        if status_filter == "Open":
            shown = [e for e in shown if e["type"] == "study" and not e["completed"]]
        elif status_filter == "Afgerond":
            shown = [e for e in shown if e["type"] == "study" and e["completed"]]
        elif status_filter == "Toetsen":
            shown = [e for e in shown if e["type"] == "exam"]
        shown.sort(key=lambda e: (e["date"], e["start_time"]))
        for event in shown:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([4, 1.3, 1.5, 1])
                with c1:
                    st.markdown(f"**{event['title']}** · {event['topic']}")
                    st.caption(f"{event['date'].strftime('%d-%m-%Y')} · {event['start_time']} · {event['duration']:g} uur · {event['location'] or 'Geen locatie'}")
                with c2:
                    new_priority = st.selectbox(
                        "Prioriteit", PRIORITIES, index=PRIORITIES.index(event["priority"]),
                        key=f"priority_{event['id']}", label_visibility="collapsed",
                    )
                    if new_priority != event["priority"]:
                        update_event(event["id"], {"priority": new_priority})
                        st.rerun()
                with c3:
                    if event["type"] == "study":
                        new_done = st.checkbox("Afgerond", value=event["completed"], key=f"done_{event['id']}")
                        if new_done != event["completed"]:
                            update_event(event["id"], {"completed": new_done})
                            st.rerun()
                    else:
                        st.caption("📝 Toets")
                with c4:
                    if st.button("Verwijder", key=f"delete_{event['id']}"):
                        remove_event(event["id"])
                        st.rerun()

    with st.expander("Automatisch achterstallige taken herplannen"):
        st.write("Verplaats open studietaken waarvan de datum of starttijd voorbij is naar het eerstvolgende vrije studieblok.")
        reschedule_days = st.multiselect(
            "Beschikbare dagen", ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"],
            default=["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag"], key="reschedule_days",
        )
        day_number = {"Maandag": 0, "Dinsdag": 1, "Woensdag": 2, "Donderdag": 3, "Vrijdag": 4, "Zaterdag": 5, "Zondag": 6}
        horizon = st.slider("Zoek vooruit (dagen)", min_value=7, max_value=90, value=30, step=7)
        overdue_count = sum(
            1 for e in all_events if e["type"] == "study" and not e["completed"]
            and (e["date"] < today or (e["date"] == today and e["start_time"] < dt.datetime.now(APP_TIMEZONE).strftime("%H:%M")))
        )
        st.caption(f"{overdue_count} openstaande taak/taken zijn achterstallig.")
        if st.button("Herplan achterstallige taken", type="primary", disabled=overdue_count == 0 or not reschedule_days):
            moved, total_overdue, _ = reschedule_overdue_tasks(
                all_events, {day_number[d] for d in reschedule_days}, horizon
            )
            if moved:
                update_events_batch(moved)
                st.success(f"{len(moved)} van {total_overdue} achterstallige taken opnieuw ingepland.")
                if len(moved) < total_overdue:
                    st.warning("Niet alle taken pasten in de gekozen periode. Verleng de zoekperiode of voeg studiedagen toe.")
                st.rerun()
            else:
                st.warning("Er zijn geen vrije studieblokken gevonden in de gekozen periode.")

# ---------------------------------------------------------------------
# Study statistics
# ---------------------------------------------------------------------
elif page == "Statistieken":
    st.title("Studie-inzicht")
    filtered_studies = [e for e in visible_events if e["type"] == "study"]
    if not filtered_studies:
        st.info("Er zijn nog geen studieblokken om te analyseren.")
    else:
        total_hours = sum(e["duration"] for e in filtered_studies)
        done_hours = sum(e["duration"] for e in filtered_studies if e["completed"])
        s1, s2, s3 = st.columns(3)
        s1.metric("Totaal gepland", f"{total_hours:g} uur")
        s2.metric("Tijd afgerond", f"{done_hours:g} uur")
        s3.metric("Taken afgerond", f"{sum(e['completed'] for e in filtered_studies)} / {len(filtered_studies)}")

        by_subject = []
        for subject in sorted(set(e["title"] for e in filtered_studies)):
            subset = [e for e in filtered_studies if e["title"] == subject]
            by_subject.append({
                "Vak": subject,
                "Gepland (uur)": sum(e["duration"] for e in subset),
                "Afgerond (uur)": sum(e["duration"] for e in subset if e["completed"]),
            })
        st.subheader("Studietijd per vak")
        st.bar_chart(pd.DataFrame(by_subject).set_index("Vak"), height=320)

        daily = defaultdict(lambda: {"Gepland": 0.0, "Afgerond": 0.0})
        for event in filtered_studies:
            key = event["date"].isoformat()
            daily[key]["Gepland"] += event["duration"]
            if event["completed"]:
                daily[key]["Afgerond"] += event["duration"]
        daily_rows = [{"Datum": day, **values} for day, values in sorted(daily.items())]
        st.subheader("Geplande en afgeronde uren per dag")
        st.line_chart(pd.DataFrame(daily_rows).set_index("Datum"), height=280)

        st.subheader("Voortgang per vak")
        progress_rows = []
        for row in by_subject:
            subject_rows = [e for e in filtered_studies if e["title"] == row["Vak"]]
            total = len(subject_rows)
            done = sum(e["completed"] for e in subject_rows)
            progress_rows.append({"Vak": row["Vak"], "Afgerond": f"{done}/{total}", "Voortgang": f"{round(done / total * 100)}%"})
        st.dataframe(pd.DataFrame(progress_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------
# Settings, export/import and database status
# ---------------------------------------------------------------------
elif page == "Instellingen":
    st.title("Instellingen en gegevens")
    st.subheader("Kalender exporteren")
    if all_events:
        st.download_button(
            "Download alle afspraken als .ics",
            data=make_ics(all_events),
            file_name="studyspace-kalender.ics",
            mime="text/calendar",
        )
        st.download_button(
            "Download gegevens-back-up (.json)",
            data=make_backup_json(all_events),
            file_name="studyspace-backup.json",
            mime="application/json",
        )
    else:
        st.caption("Er zijn nog geen afspraken om te exporteren.")

    st.divider()
    st.subheader("Back-up terugzetten")
    uploaded_backup = st.file_uploader("Kies een StudySpace JSON-back-up", type=["json"])
    if uploaded_backup is not None:
        if st.button("Importeer back-up", type="primary"):
            try:
                imported = json.loads(uploaded_backup.getvalue().decode("utf-8"))
                if imported.get("format") != "studyspace-events-v1" or not isinstance(imported.get("events"), list):
                    raise ValueError("Dit bestand is geen geldige StudySpace-back-up.")
                normalized = [normalize_event(row) for row in imported["events"]]
                upsert_imported_events(normalized)
                st.success(f"{len(normalized)} afspraken geïmporteerd of bijgewerkt.")
                st.rerun()
            except Exception as exc:
                st.error(f"Importeren is niet gelukt: {exc}")

    st.divider()
    st.subheader("Opslag")
    if BACKEND == "supabase":
        st.success("Supabase is actief. Afspraken worden in je cloud-database opgeslagen.")
    else:
        st.warning("SQLite is actief. Dit bestand staat lokaal naast app.py en is op Streamlit Cloud niet gegarandeerd blijvend.")
        st.markdown("Volg `SUPABASE_SETUP.md` in de projectmap om persistente opslag te activeren.")
    st.caption("Thema, vakfilters en navigatie-instellingen veranderen de opgeslagen afspraken niet.")

st.divider()
st.caption("StudySpace · School Planner · Exporteer regelmatig een back-up van je gegevens.")
