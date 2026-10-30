import datetime as dt
import unittest

from planner_logic import (
    APP_TIMEZONE,
    build_slots,
    events_overlap,
    make_event,
    create_balanced_study_plan,
    make_ics,
    reschedule_overdue_tasks,
)


class PlannerLogicTests(unittest.TestCase):
    def test_build_slots_half_hour(self):
        slots = build_slots(dt.date(2026, 11, 2), dt.time(16, 0), dt.time(18, 0))
        self.assertEqual([t.strftime("%H:%M") for t in slots], ["16:00", "16:30", "17:00", "17:30"])

    def test_overlap_detection(self):
        day = dt.date(2026, 11, 2)
        one = make_event("study", "Wiskunde B", "H1", day, dt.time(16, 0), 1.0, "Thuis", "Normaal")
        touching = make_event("study", "Wiskunde B", "H2", day, dt.time(17, 0), 0.5, "Thuis", "Normaal")
        collision = make_event("exam", "Wiskunde B", "PTA", day, dt.time(16, 30), 1.0, "F103", "Hoog")
        self.assertFalse(events_overlap(one, touching))
        self.assertTrue(events_overlap(one, collision))

    def test_balanced_plan_creates_two_sessions_per_topic(self):
        start = dt.date(2026, 11, 2)
        exam_day = dt.date(2026, 11, 6)
        exam = make_event("exam", "Wiskunde B", "PTA", exam_day, dt.time(9, 0), 1.0, "F103", "Hoog")
        planned, needed, capacity = create_balanced_study_plan(
            "Wiskunde B", ["Hoofdstuk 1", "Hoofdstuk 2"], start, exam_day,
            {0, 1, 2, 3, 4}, dt.time(16, 0), dt.time(18, 0), "Hoog", [], exam,
        )
        self.assertEqual(needed, 4)
        self.assertEqual(len(planned), 4)
        self.assertGreaterEqual(capacity, needed)
        self.assertEqual(len({e["id"] for e in planned}), 4)


    def test_scheduler_respects_existing_time_conflicts(self):
        start = dt.date(2026, 11, 2)
        exam_day = dt.date(2026, 11, 6)
        exam = make_event("exam", "Wiskunde B", "PTA", exam_day, dt.time(9, 0), 1.0, "F103", "Hoog")
        busy = make_event("study", "Andere vak", "Bestaande taak", start, dt.time(16, 0), 1.0, "Thuis", "Normaal")
        planned, needed, capacity = create_balanced_study_plan(
            "Wiskunde B", ["Hoofdstuk 1"], start, exam_day,
            {0}, dt.time(16, 0), dt.time(17, 0), "Normaal", [busy], exam,
        )
        self.assertEqual(needed, 2)
        self.assertEqual(capacity, 0)
        self.assertEqual(planned, [])

    def test_overdue_task_rescheduler_moves_task_forward(self):
        yesterday = dt.datetime.now(APP_TIMEZONE).date() - dt.timedelta(days=1)
        overdue = make_event("study", "Scheikunde", "Hoofdstuk 3", yesterday, dt.time(16, 0), 0.5, "Thuis", "Hoog")
        moved, total, _ = reschedule_overdue_tasks([overdue], {0, 1, 2, 3, 4, 5, 6}, 14)
        self.assertEqual(total, 1)
        self.assertEqual(len(moved), 1)
        self.assertGreaterEqual(moved[0]["date"], dt.datetime.now(APP_TIMEZONE).date())
        self.assertNotEqual(moved[0]["date"], yesterday)

    def test_ics_contains_events(self):
        day = dt.date(2026, 11, 2)
        event = make_event("exam", "Scheikunde", "PTA toets", day, dt.time(9, 0), 1.5, "A101", "Hoog")
        payload = make_ics([event]).decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", payload)
        self.assertIn("SUMMARY:Scheikunde", payload)
        self.assertIn("DTSTART:20261102T090000", payload)
        self.assertIn("END:VCALENDAR", payload)


if __name__ == "__main__":
    unittest.main()
