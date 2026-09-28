from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, time, timezone
from decimal import Decimal

from core.qualification import (
    QualificationGraphInputError,
    QualificationTask,
    ResourceCalendar,
    ScheduleStatus,
    TaskType,
    build_qualification_graph,
)


START = datetime(2026, 10, 5, 8, tzinfo=timezone.utc)


class QualificationGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calendar = ResourceCalendar(
            resource_id="RESOURCE-1",
            timezone="UTC",
            working_weekdays=(0, 1, 2, 3, 4),
            workday_start=time(8),
            workday_end=time(16),
        )

    def test_schedules_sequential_tasks(self) -> None:
        first = self.task("TASK-1", Decimal("2"), earliest_start=START)
        second = self.task("TASK-2", Decimal("3"), predecessors=("TASK-1",))

        result = build_qualification_graph(
            candidate_id="CAND-A", tasks=(second, first), calendars=(self.calendar,)
        )

        self.assertTrue(result.resolved)
        self.assertEqual(
            datetime(2026, 10, 5, 13, tzinfo=timezone.utc),
            result.qualification_complete,
        )
        self.assertEqual(("TASK-1", "TASK-2"), result.critical_path)

    def test_parallel_tasks_complete_at_longest_branch(self) -> None:
        root = self.task("ROOT", Decimal("0"), earliest_start=START, resource=None)
        short = self.task("SHORT", Decimal("4"), predecessors=("ROOT",))
        long = replace(
            self.task("LONG", Decimal("6"), predecessors=("ROOT",)),
            required_resource="RESOURCE-2",
        )
        release = self.task(
            "RELEASE",
            Decimal("0"),
            predecessors=("SHORT", "LONG"),
            resource=None,
        )
        second_calendar = replace(self.calendar, resource_id="RESOURCE-2")

        result = build_qualification_graph(
            candidate_id="CAND-A",
            tasks=(root, short, long, release),
            calendars=(self.calendar, second_calendar),
        )

        self.assertEqual(
            datetime(2026, 10, 5, 14, tzinfo=timezone.utc),
            result.qualification_complete,
        )
        self.assertEqual(("ROOT", "LONG", "RELEASE"), result.critical_path)

    def test_unknown_duration_propagates_to_dependents(self) -> None:
        unknown = self.task("UNKNOWN", None, earliest_start=START)
        dependent = self.task("DEPENDENT", Decimal("1"), predecessors=("UNKNOWN",))

        result = build_qualification_graph(
            candidate_id="CAND-A",
            tasks=(unknown, dependent),
            calendars=(self.calendar,),
        )

        self.assertFalse(result.resolved)
        self.assertIsNone(result.qualification_complete)
        self.assertEqual(("UNKNOWN", "DEPENDENT"), result.unresolved_task_ids)

    def test_missing_resource_calendar_remains_unresolved(self) -> None:
        task = replace(
            self.task("TASK-1", Decimal("1"), earliest_start=START),
            required_resource="MISSING",
        )

        result = build_qualification_graph(
            candidate_id="CAND-A", tasks=(task,), calendars=(self.calendar,)
        )

        self.assertEqual(ScheduleStatus.UNRESOLVED, result.schedules[0].status)
        self.assertIn("unavailable", result.schedules[0].reason)

    def test_weekend_start_moves_to_next_workday(self) -> None:
        saturday = datetime(2026, 10, 3, 8, tzinfo=timezone.utc)
        task = self.task("TASK-1", Decimal("2"), earliest_start=saturday)

        result = build_qualification_graph(
            candidate_id="CAND-A", tasks=(task,), calendars=(self.calendar,)
        )

        self.assertEqual(
            datetime(2026, 10, 5, 8, tzinfo=timezone.utc),
            result.schedules[0].start_time,
        )
        self.assertEqual(
            datetime(2026, 10, 5, 10, tzinfo=timezone.utc),
            result.qualification_complete,
        )

    def test_calendar_wait_does_not_break_critical_dependency_path(self) -> None:
        friday_after_hours = datetime(2026, 10, 2, 17, tzinfo=timezone.utc)
        delivery = self.task(
            "DELIVERY",
            Decimal("0"),
            earliest_start=friday_after_hours,
            resource=None,
        )
        test = self.task("TEST", Decimal("2"), predecessors=("DELIVERY",))

        result = build_qualification_graph(
            candidate_id="CAND-A",
            tasks=(delivery, test),
            calendars=(self.calendar,),
        )

        self.assertEqual(("DELIVERY", "TEST"), result.critical_path)
        self.assertEqual(
            datetime(2026, 10, 5, 8, tzinfo=timezone.utc),
            result.schedules[1].start_time,
        )

    def test_cycle_fails_closed(self) -> None:
        first = self.task("TASK-1", Decimal("1"), predecessors=("TASK-2",))
        second = self.task("TASK-2", Decimal("1"), predecessors=("TASK-1",))

        with self.assertRaisesRegex(QualificationGraphInputError, "contains a cycle"):
            build_qualification_graph(
                candidate_id="CAND-A",
                tasks=(first, second),
                calendars=(self.calendar,),
            )

    @staticmethod
    def task(
        task_id: str,
        duration: Decimal | None,
        *,
        predecessors: tuple[str, ...] = (),
        earliest_start: datetime | None = None,
        resource: str | None = "RESOURCE-1",
    ) -> QualificationTask:
        return QualificationTask(
            task_id=task_id,
            candidate_id="CAND-A",
            name=task_id,
            task_type=TaskType.TEST,
            duration_hours=duration,
            predecessor_ids=predecessors,
            required_resource=resource,
            earliest_start=earliest_start,
            requirement_id=None,
            source_reference=f"fixture:{task_id}",
        )


if __name__ == "__main__":
    unittest.main()
