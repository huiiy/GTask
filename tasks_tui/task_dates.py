"""Calendar-date ordering and section labels for the task view."""

from datetime import date, timedelta

from dateutil.parser import isoparse


def due_date(task):
    """Read the date as supplied, without shifting date-only deadlines by timezone."""
    value = task.get("due")
    if not value:
        return None
    try:
        return isoparse(value).date()
    except (ValueError, TypeError, OverflowError):
        return None


def sort_tasks(tasks):
    """Stable chronological order, preserving existing order within each day."""
    return sorted(tasks, key=lambda task: due_date(task) or date.max)


def date_section(task, today=None):
    today = today or date.today()
    due = due_date(task)
    if due is None:
        return "No date"
    if due < today:
        return "Overdue"
    if due == today:
        return "Today"
    if due == today + timedelta(days=1):
        return "Tomorrow"
    label = f"{due:%a, %b} {due.day}"
    return label if due.year == today.year else f"{label}, {due.year}"
