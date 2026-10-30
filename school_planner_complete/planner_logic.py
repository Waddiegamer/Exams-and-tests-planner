"""Pure scheduling and calendar helpers for StudySpace."""
from __future__ import annotations

import datetime as dt
import uuid
from zoneinfo import ZoneInfo
from typing import Any

SLOT_MINUTES = 30
PRIORITIES = ["Laag", "Normaal", "Hoog"]
PRIORITY_RANK = {"Hoog": 0, "Normaal": 1, "Laag": 2}
APP_TIMEZONE = ZoneInfo("Europe/Amsterdam")


def event_start_minutes(event: dict[str, Any]) -> int:
    hour, minute = map(int, event["start_time"].split(":")[:2])
    return hour * 60 + minute


def event_end_minutes(event: dict[str, Any]) -> int:
    return event_start_minutes(event) + round(float(event["duration"]) * 60)


def events_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["date"] != b["date"]:
        return False
    return event_start_minutes(a) < event_end_minutes(b) and event_start_minutes(b) < event_end_minutes(a)


def make_event(event_type: str, title: str, topic: str, day: dt.date,
               start: dt.time, duration: float, location: str, priority: str) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "title": title,
        "topic": topic,
        "date": day,
        "start_hour": start.hour,
        "start_time": start.strftime("%H:%M"),
        "duration": float(duration),
        "location": location,
        "completed": False,
        "priority": priority if priority in PRIORITIES else "Normaal",
        "created_at": dt.datetime.now(APP_TIMEZONE).isoformat(timespec="seconds"),
    }


def build_slots(day: dt.date, start: dt.time, end: dt.time) -> list[dt.time]:
    start_min = start.hour * 60 + start.minute
    end_min = end.hour * 60 + end.minute
    slots = []
    for minute in range(start_min, end_min, SLOT_MINUTES):
        if minute + SLOT_MINUTES <= end_min:
            slots.append(dt.time(minute // 60, minute % 60))
    return slots


def create_balanced_study_plan(
    subject: str,
    topics: list[str],
    start_date: dt.date,
    exam_date: dt.date,
    weekdays: set[int],
    day_start: dt.time,
    day_end: dt.time,
    priority: str,
    existing_events: list[dict[str, Any]],
    exam_event: dict[str, Any],
) -> tuple[list[dict[str, Any]], int, int]:
    valid_dates = []
    cursor = start_date
    while cursor < exam_date:
        if cursor.weekday() in weekdays:
            valid_dates.append(cursor)
        cursor += dt.timedelta(days=1)

    task_specs = []
    for topic in topics:
        task_specs.extend([(topic, "Leren"), (topic, "Herhalen")])
    required = len(task_specs)

    if not valid_dates:
        return [], required, 0

    busy_events = existing_events + [exam_event]
    slots_by_day: dict[dt.date, list[dt.time]] = {}
    capacity = 0
    for day in valid_dates:
        available = []
        for clock_time in build_slots(day, day_start, day_end):
            candidate = make_event("study", subject, "", day, clock_time, 0.5, "Thuis", priority)
            if not any(events_overlap(candidate, old) for old in busy_events):
                available.append(clock_time)
        slots_by_day[day] = available
        capacity += len(available)

    if capacity < required:
        return [], required, capacity

    planned: list[dict[str, Any]] = []
    daily_counts = {day: 0 for day in valid_dates}
    for index, (topic, session_type) in enumerate(task_specs):
        ideal_index = min(len(valid_dates) - 1, int((index + 0.5) * len(valid_dates) / max(required, 1)))
        candidate_days = sorted(
            valid_dates,
            key=lambda day: (daily_counts[day], abs(valid_dates.index(day) - ideal_index), valid_dates.index(day)),
        )
        chosen_day = next((day for day in candidate_days if slots_by_day[day]), None)
        if chosen_day is None:
            return [], required, len(planned)
        chosen_time = slots_by_day[chosen_day].pop(0)
        daily_counts[chosen_day] += 1
        planned.append(make_event(
            "study", subject, f"{topic} · {session_type}", chosen_day,
            chosen_time, 0.5, "Thuis", priority,
        ))
    return planned, required, capacity


def reschedule_overdue_tasks(events: list[dict[str, Any]], weekdays: set[int],
                             window_days: int = 30) -> tuple[list[dict[str, Any]], int, int]:
    local_now = dt.datetime.now(APP_TIMEZONE)
    today = local_now.date()
    now_string = local_now.strftime("%H:%M")
    overdue = [
        e for e in events
        if e["type"] == "study" and not e["completed"]
        and (e["date"] < today or (e["date"] == today and e["start_time"] < now_string))
    ]
    overdue.sort(key=lambda e: (PRIORITY_RANK.get(e["priority"], 1), e["date"], e["start_time"]))
    moving_ids = {e["id"] for e in overdue}
    fixed_events = [e for e in events if e["id"] not in moving_ids]

    slots = []
    for offset in range(window_days + 1):
        day = today + dt.timedelta(days=offset)
        if day.weekday() not in weekdays:
            continue
        for clock_time in build_slots(day, dt.time(16, 0), dt.time(22, 0)):
            if day == today and clock_time.strftime("%H:%M") <= now_string:
                continue
            slots.append((day, clock_time))

    moved = []
    used = []
    for task in overdue:
        candidate = None
        for day, clock_time in slots:
            proposed = dict(task, date=day, start_time=clock_time.strftime("%H:%M"), start_hour=clock_time.hour)
            if any(events_overlap(proposed, other) for other in fixed_events + used):
                continue
            candidate = proposed
            break
        if candidate is None:
            continue
        moved.append(candidate)
        used.append(candidate)
        slots = [(d, t) for d, t in slots if not (d == candidate["date"] and t == dt.time.fromisoformat(candidate["start_time"]))]
    return moved, len(overdue), window_days


def ics_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def make_ics(events: list[dict[str, Any]]) -> bytes:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//StudySpace School Planner//NL", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    for event in events:
        start_hour, start_minute = map(int, event["start_time"].split(":"))
        start = dt.datetime.combine(event["date"], dt.time(start_hour, start_minute))
        end = start + dt.timedelta(minutes=round(event["duration"] * 60))
        label = "Toets" if event["type"] == "exam" else "Studeren"
        description = f"{label}: {event['topic']}\nPrioriteit: {event['priority']}\nLocatie: {event['location']}"
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{event['id']}@studyspace-planner",
            f"DTSTAMP:{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{ics_escape(event['title'] + ' — ' + label)}",
            f"DESCRIPTION:{ics_escape(description)}",
            f"LOCATION:{ics_escape(event['location'])}",
            "END:VEVENT",
        ])
    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")
