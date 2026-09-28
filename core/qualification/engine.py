"""Deterministic scheduling for qualification dependency graphs."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .models import (
    QualificationGraphInputError,
    QualificationGraphResult,
    QualificationTask,
    ResourceCalendar,
    ScheduleStatus,
    TaskSchedule,
)


def build_qualification_graph(
    *,
    candidate_id: str,
    tasks: Iterable[QualificationTask],
    calendars: Iterable[ResourceCalendar],
) -> QualificationGraphResult:
    """Validate, topologically order, and schedule one candidate's tasks."""

    all_tasks = tuple(tasks)
    calendar_list = tuple(calendars)
    candidate_tasks = tuple(
        task for task in all_tasks if task.candidate_id == candidate_id
    )
    _validate_inputs(candidate_id, candidate_tasks, calendar_list)

    task_by_id = {task.task_id: task for task in candidate_tasks}
    calendar_by_id = {
        calendar.resource_id: calendar for calendar in calendar_list
    }
    order = _topological_order(candidate_tasks)
    schedules: dict[str, TaskSchedule] = {}
    driving_predecessor: dict[str, str | None] = {}

    for task_id in order:
        task = task_by_id[task_id]
        predecessor_schedules = tuple(
            schedules[predecessor_id] for predecessor_id in task.predecessor_ids
        )
        unresolved_predecessors = tuple(
            schedule.task_id
            for schedule in predecessor_schedules
            if schedule.status == ScheduleStatus.UNRESOLVED
        )
        if unresolved_predecessors:
            schedules[task_id] = _unresolved(
                task,
                "Predecessor timing is unresolved: "
                + ", ".join(unresolved_predecessors),
            )
            driving_predecessor[task_id] = None
            continue
        if task.duration_hours is None:
            schedules[task_id] = _unresolved(task, "Task duration is unknown.")
            driving_predecessor[task_id] = None
            continue

        predecessor_end_times = tuple(
            schedule.end_time
            for schedule in predecessor_schedules
            if schedule.end_time is not None
        )
        latest_predecessor_end = max(predecessor_end_times, default=None)
        start_time = _latest(task.earliest_start, latest_predecessor_end)
        if start_time is None:
            schedules[task_id] = _unresolved(
                task, "Task has no resolved predecessor end or earliest start."
            )
            driving_predecessor[task_id] = None
            continue
        if start_time.tzinfo is None or start_time.utcoffset() is None:
            raise QualificationGraphInputError(
                f"task {task.task_id} earliest_start must be timezone-aware"
            )
        dependency_ready_time = start_time

        if task.duration_hours == 0:
            end_time = start_time.astimezone(timezone.utc)
            start_time = end_time
        else:
            if task.required_resource is None:
                schedules[task_id] = _unresolved(
                    task, "Positive-duration task has no required resource."
                )
                driving_predecessor[task_id] = None
                continue
            calendar = calendar_by_id.get(task.required_resource)
            if calendar is None:
                schedules[task_id] = _unresolved(
                    task,
                    f"Resource calendar is unavailable: {task.required_resource}",
                )
                driving_predecessor[task_id] = None
                continue
            start_time, end_time = _schedule_on_calendar(
                start_time, task.duration_hours, calendar
            )

        schedules[task_id] = TaskSchedule(
            task_id=task.task_id,
            name=task.name,
            task_type=task.task_type,
            status=ScheduleStatus.SCHEDULED,
            start_time=start_time,
            end_time=end_time,
            duration_hours=task.duration_hours,
            predecessor_ids=task.predecessor_ids,
            required_resource=task.required_resource,
            requirement_id=task.requirement_id,
            reason=None,
            source_reference=task.source_reference,
        )
        driving_predecessor[task_id] = _driving_predecessor(
            task,
            schedules,
            dependency_ready_time,
        )

    schedule_tuple = tuple(schedules[task_id] for task_id in order)
    unresolved_task_ids = tuple(
        schedule.task_id
        for schedule in schedule_tuple
        if schedule.status == ScheduleStatus.UNRESOLVED
    )
    terminal_ids = _terminal_task_ids(candidate_tasks)
    terminal_schedules = tuple(schedules[task_id] for task_id in terminal_ids)
    resolved = not unresolved_task_ids and all(
        schedule.end_time is not None for schedule in terminal_schedules
    )
    if resolved:
        completion_schedule = max(
            terminal_schedules,
            key=lambda schedule: schedule.end_time,
        )
        qualification_complete = completion_schedule.end_time
        critical_path = _critical_path(
            completion_schedule.task_id, driving_predecessor
        )
    else:
        qualification_complete = None
        critical_path = ()

    return QualificationGraphResult(
        candidate_id=candidate_id,
        resolved=resolved,
        qualification_complete=qualification_complete,
        critical_path=critical_path,
        unresolved_task_ids=unresolved_task_ids,
        schedules=schedule_tuple,
    )


def _validate_inputs(
    candidate_id: str,
    tasks: tuple[QualificationTask, ...],
    calendars: tuple[ResourceCalendar, ...],
) -> None:
    if not candidate_id:
        raise QualificationGraphInputError("candidate_id is required")
    if not tasks:
        raise QualificationGraphInputError(
            f"at least one qualification task is required for {candidate_id}"
        )
    _require_unique_ids("task", (task.task_id for task in tasks))
    _require_unique_ids("resource calendar", (item.resource_id for item in calendars))

    task_ids = {task.task_id for task in tasks}
    for task in tasks:
        if task.duration_hours is not None and task.duration_hours < 0:
            raise QualificationGraphInputError(
                f"task duration cannot be negative: {task.task_id}"
            )
        missing = set(task.predecessor_ids) - task_ids
        if missing:
            raise QualificationGraphInputError(
                f"task {task.task_id} references unknown predecessor: {sorted(missing)[0]}"
            )
        if task.task_id in task.predecessor_ids:
            raise QualificationGraphInputError(
                f"task cannot depend on itself: {task.task_id}"
            )

    for calendar in calendars:
        if not calendar.working_weekdays:
            raise QualificationGraphInputError(
                f"resource calendar has no working days: {calendar.resource_id}"
            )
        if any(day < 0 or day > 6 for day in calendar.working_weekdays):
            raise QualificationGraphInputError(
                f"resource calendar has invalid weekday: {calendar.resource_id}"
            )
        if calendar.workday_start >= calendar.workday_end:
            raise QualificationGraphInputError(
                f"resource calendar workday must have positive duration: {calendar.resource_id}"
            )
        try:
            ZoneInfo(calendar.timezone)
        except ZoneInfoNotFoundError as error:
            raise QualificationGraphInputError(
                f"unknown resource timezone: {calendar.timezone}"
            ) from error


def _topological_order(tasks: tuple[QualificationTask, ...]) -> tuple[str, ...]:
    successors: dict[str, list[str]] = defaultdict(list)
    indegree = {task.task_id: len(task.predecessor_ids) for task in tasks}
    for task in tasks:
        for predecessor_id in task.predecessor_ids:
            successors[predecessor_id].append(task.task_id)

    ready = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    order: list[str] = []
    while ready:
        task_id = ready.pop(0)
        order.append(task_id)
        for successor_id in sorted(successors[task_id]):
            indegree[successor_id] -= 1
            if indegree[successor_id] == 0:
                ready.append(successor_id)
                ready.sort()

    if len(order) != len(tasks):
        raise QualificationGraphInputError("qualification dependency graph contains a cycle")
    return tuple(order)


def _schedule_on_calendar(
    earliest_start: datetime,
    duration_hours: Decimal,
    calendar: ResourceCalendar,
) -> tuple[datetime, datetime]:
    zone = ZoneInfo(calendar.timezone)
    cursor = earliest_start.astimezone(zone)
    start: datetime | None = None
    remaining_seconds = duration_hours * Decimal("3600")

    for _ in range(3660):
        local_date = cursor.date()
        if (
            local_date.weekday() not in calendar.working_weekdays
            or local_date in calendar.unavailable_dates
        ):
            cursor = datetime.combine(
                local_date + timedelta(days=1), time.min, tzinfo=zone
            )
            continue

        window_start = datetime.combine(
            local_date, calendar.workday_start, tzinfo=zone
        )
        window_end = datetime.combine(local_date, calendar.workday_end, tzinfo=zone)
        if cursor < window_start:
            cursor = window_start
        if cursor >= window_end:
            cursor = datetime.combine(
                local_date + timedelta(days=1), time.min, tzinfo=zone
            )
            continue
        if start is None:
            start = cursor

        available_seconds = Decimal(str((window_end - cursor).total_seconds()))
        if remaining_seconds <= available_seconds:
            end = cursor + timedelta(seconds=float(remaining_seconds))
            return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

        remaining_seconds -= available_seconds
        cursor = datetime.combine(
            local_date + timedelta(days=1), time.min, tzinfo=zone
        )

    raise QualificationGraphInputError(
        f"could not schedule resource within ten years: {calendar.resource_id}"
    )


def _driving_predecessor(
    task: QualificationTask,
    schedules: dict[str, TaskSchedule],
    dependency_ready_time: datetime,
) -> str | None:
    predecessor_schedules = [
        schedules[predecessor_id]
        for predecessor_id in task.predecessor_ids
        if schedules[predecessor_id].end_time is not None
    ]
    if not predecessor_schedules:
        return None
    latest = max(predecessor_schedules, key=lambda schedule: schedule.end_time)
    return latest.task_id if latest.end_time == dependency_ready_time else None


def _critical_path(
    terminal_task_id: str, driving_predecessor: dict[str, str | None]
) -> tuple[str, ...]:
    reversed_path: list[str] = []
    current: str | None = terminal_task_id
    while current is not None:
        reversed_path.append(current)
        current = driving_predecessor[current]
    return tuple(reversed(reversed_path))


def _terminal_task_ids(tasks: tuple[QualificationTask, ...]) -> tuple[str, ...]:
    predecessor_ids = {
        predecessor_id for task in tasks for predecessor_id in task.predecessor_ids
    }
    return tuple(
        sorted(task.task_id for task in tasks if task.task_id not in predecessor_ids)
    )


def _unresolved(task: QualificationTask, reason: str) -> TaskSchedule:
    return TaskSchedule(
        task_id=task.task_id,
        name=task.name,
        task_type=task.task_type,
        status=ScheduleStatus.UNRESOLVED,
        start_time=None,
        end_time=None,
        duration_hours=task.duration_hours,
        predecessor_ids=task.predecessor_ids,
        required_resource=task.required_resource,
        requirement_id=task.requirement_id,
        reason=reason,
        source_reference=task.source_reference,
    )


def _latest(first: datetime | None, second: datetime | None) -> datetime | None:
    if first is None:
        return second
    if second is None:
        return first
    return max(first, second)


def _require_unique_ids(entity: str, identifiers: Iterable[str]) -> None:
    duplicates = [
        identifier
        for identifier, count in Counter(identifiers).items()
        if count > 1
    ]
    if duplicates:
        raise QualificationGraphInputError(
            f"duplicate {entity} ID: {sorted(duplicates)[0]}"
        )
