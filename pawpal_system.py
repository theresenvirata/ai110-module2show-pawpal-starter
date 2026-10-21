"""PawPal+ core classes, based on diagrams/uml.mmd."""

from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from enum import Enum
from itertools import combinations

SLOT_STEP_MINUTES = 5  # granularity used when searching for a free start time


def to_minutes(t: time) -> int:
    """Convert a time of day to minutes since midnight."""
    return t.hour * 60 + t.minute


def to_time(minutes: int) -> time:
    """Convert minutes since midnight to a time of day."""
    return time(minutes // 60, minutes % 60)


def overlaps(start_a: time, task_a: "Task", start_b: time, task_b: "Task") -> bool:
    """Return True if the two tasks, at these start times, share any minute.

    Back-to-back tasks (one ends at 8:00, the next starts at 8:00) don't overlap.
    """
    a = to_minutes(start_a)
    b = to_minutes(start_b)
    return a < b + task_b.duration_minutes and b < a + task_a.duration_minutes


def _span(task: "Task") -> str:
    """'HH:MM-HH:MM' for a scheduled task."""
    start = to_minutes(task.scheduled_at)
    return f"{task.scheduled_at:%H:%M}-{to_time(start + task.duration_minutes):%H:%M}"


class Priority(Enum):
    """Higher value = more important."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class TaskCategory(Enum):
    WALK = "walk"
    FEEDING = "feeding"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"
    OTHER = "other"


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"


# eq=False: two tasks with identical details are still different tasks.
@dataclass(eq=False)
class Task:
    description: str
    category: TaskCategory
    priority: Priority
    duration_minutes: int
    available_from: time
    available_until: time
    frequency: Frequency = Frequency.DAILY
    weekday: int | None = None  # 0 = Monday; only used for weekly tasks
    due_date: date | None = None  # not due before this date; None = due from the start
    completed: bool = False
    completed_on: date | None = None
    scheduled_at: time | None = None  # set by Scheduler.generate_plan()
    # Set by Pet.add_task(). Hidden from repr so Pet -> Task -> Pet doesn't loop.
    pet: "Pet | None" = field(default=None, repr=False)
    # The occurrence created when this one was completed (see mark_complete).
    next_task: "Task | None" = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Reject invalid durations, time windows, and weekly tasks without a weekday."""
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        if self.available_from >= self.available_until:
            raise ValueError("available_from must be before available_until")
        if self.frequency is Frequency.WEEKLY and self.weekday is None:
            raise ValueError("weekly tasks need a weekday (0 = Monday)")

    def set_priority(self, priority: Priority) -> None:
        """Change how important this task is."""
        self.priority = priority

    def set_duration(self, duration_minutes: int) -> None:
        """Change how long this task takes."""
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        self.duration_minutes = duration_minutes

    def set_time_availability(self, available_from: time, available_until: time) -> None:
        """Change the window of the day this task can be done in."""
        if available_from >= available_until:
            raise ValueError("available_from must be before available_until")
        self.available_from = available_from
        self.available_until = available_until

    def mark_complete(self, on: date | None = None) -> "Task | None":
        """Mark this task done for the given date (default today).

        Also creates the next occurrence (tomorrow for daily tasks, the next
        matching weekday for weekly ones) and gives it to the same pet.
        Returns the new task, or None if this one was already completed.
        """
        if self.completed:
            return None
        on = on or date.today()
        self.completed = True
        self.completed_on = on
        self.next_task = self.next_occurrence(on)
        if self.pet is not None:
            self.pet.add_task(self.next_task)
        return self.next_task

    def mark_incomplete(self) -> None:
        """Undo a completion, removing the next occurrence it created.

        If that occurrence was completed too, its own next occurrence is
        removed as well, and so on down the chain.
        """
        self.completed = False
        self.completed_on = None
        if self.next_task is not None:
            self.next_task.mark_incomplete()
            if self.next_task.pet is not None:
                self.next_task.pet.remove_task(self.next_task)
            self.next_task = None

    def next_occurrence(self, after: date) -> "Task":
        """A fresh copy of this task, due on its first repeat after the given date."""
        if self.frequency is Frequency.WEEKLY:
            days = (self.weekday - after.weekday() - 1) % 7 + 1  # 1..7
        else:
            days = 1
        return replace(self, due_date=after + timedelta(days=days), completed=False,
                       completed_on=None, scheduled_at=None, pet=None, next_task=None)

    def is_due(self, on: date) -> bool:
        """Return True if this task still needs doing on the given date.

        A completed task is never due again; its next occurrence takes over.
        Nothing is due before its due_date. After that, daily tasks are due
        every day and weekly tasks only on their weekday.
        """
        if self.completed:
            return False
        if self.due_date is not None and on < self.due_date:
            return False
        if self.frequency is Frequency.WEEKLY:
            return on.weekday() == self.weekday
        return True

    def label(self) -> str:
        pet_name = self.pet.name if self.pet else "unassigned pet"
        return f"{self.description} for {pet_name}"


@dataclass
class Pet:
    name: str
    age: int
    breed: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Give this pet a task."""
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove one of this pet's tasks."""
        self.tasks.remove(task)
        task.pet = None


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    # Preferred start time for each kind of task, e.g. walks at 7:00.
    preferences: dict[TaskCategory, time] = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet; its tasks go with it."""
        self.pets.remove(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name."""
        return next((p for p in self.pets if p.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every pet's tasks together in one list."""
        return [task for pet in self.pets for task in pet.tasks]

    def set_preference(self, category: TaskCategory, preferred_time: time) -> None:
        """Prefer to do this kind of task around the given time."""
        self.preferences[category] = preferred_time

    def remove_preference(self, category: TaskCategory) -> None:
        """Stop preferring a time for this kind of task."""
        self.preferences.pop(category, None)


@dataclass
class Scheduler:
    owner: Owner
    plan_date: date = field(default_factory=date.today)
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    # Built only by generate_plan(); never edited directly.
    timetable: dict[time, Task] = field(default_factory=dict)
    unscheduled: list[Task] = field(default_factory=list)
    reasons: dict[Task, str] = field(default_factory=dict)

    def get_due_tasks(self) -> list[Task]:
        """Tasks across all of the owner's pets that still need doing on plan_date."""
        return [t for t in self.owner.get_all_tasks() if t.is_due(self.plan_date)]

    def filter_tasks(self, pet_name: str | None = None,
                     completed: bool | None = None) -> list[Task]:
        """Owner's tasks, optionally narrowed to one pet and/or completion status."""
        tasks = self.owner.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet and t.pet.name == pet_name]
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Highest priority first; ties go to the task with the tighter window."""
        return sorted(tasks, key=lambda t: (
            -t.priority.value,
            to_minutes(t.available_until) - to_minutes(t.available_from),
        ))

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Earliest first, by scheduled time (or available_from if not yet scheduled).

        Zero-padded "HH:MM" strings sort the same as the times they name,
        so "07:30" < "12:00" < "17:05".
        """
        return sorted(tasks, key=lambda t: (t.scheduled_at or t.available_from).strftime("%H:%M"))

    def mark_task_complete(self, task: Task) -> Task | None:
        """Mark a task done for plan_date; returns its next occurrence."""
        return task.mark_complete(self.plan_date)

    def has_conflict(self, start: time, task: Task) -> bool:
        """Return True if task, starting at start, would overlap the timetable."""
        return any(overlaps(start, task, placed_start, placed)
                   for placed_start, placed in self.timetable.items())

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return a warning for every pair of tasks whose scheduled times overlap.

        Checks the given tasks (default: all of the owner's tasks) that have a
        scheduled_at, whether they belong to the same pet or different pets.
        Tasks without a time are skipped. This never raises: an empty list
        means no conflicts.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        timed = self.sort_by_time([t for t in tasks if t.scheduled_at is not None])
        warnings = []
        for a, b in combinations(timed, 2):
            if overlaps(a.scheduled_at, a, b.scheduled_at, b):
                same_pet = "same pet" if a.pet is not None and a.pet is b.pet else "different pets"
                warnings.append(
                    f"Warning: {a.label()} ({_span(a)}) overlaps "
                    f"{b.label()} ({_span(b)}) [{same_pet}]"
                )
        return warnings

    def _candidate_starts(self, task: Task) -> list[int]:
        """Possible start times (in minutes) for task, best first."""
        earliest = max(to_minutes(task.available_from), to_minutes(self.day_start))
        latest = min(to_minutes(task.available_until), to_minutes(self.day_end)) - task.duration_minutes
        starts = list(range(earliest, latest + 1, SLOT_STEP_MINUTES))
        preferred = self.owner.preferences.get(task.category)
        if preferred is not None:
            target = to_minutes(preferred)
            starts.sort(key=lambda m: (abs(m - target), m))
        return starts

    def generate_plan(self) -> dict[time, Task]:
        """Rebuild the timetable from the tasks due on plan_date.

        Tasks are placed highest priority first, between day_start and
        day_end, inside their own availability window, without conflicts.
        A task whose category has a preferred time is placed as close to
        that time as possible. Tasks that don't fit go into unscheduled.
        """
        self.timetable = {}
        self.unscheduled = []
        self.reasons = {}
        for task in self.owner.get_all_tasks():
            task.scheduled_at = None

        for task in self.sort_by_priority(self.get_due_tasks()):
            start = next((m for m in self._candidate_starts(task)
                          if not self.has_conflict(to_time(m), task)), None)
            if start is None:
                self.unscheduled.append(task)
                self.reasons[task] = (
                    f"no free {task.duration_minutes}-min slot between "
                    f"{task.available_from:%H:%M} and {task.available_until:%H:%M}"
                )
                continue
            task.scheduled_at = to_time(start)
            self.timetable[task.scheduled_at] = task
            preferred = self.owner.preferences.get(task.category)
            if preferred is None:
                self.reasons[task] = "earliest free slot in its window"
            elif task.scheduled_at == preferred:
                self.reasons[task] = "at your preferred time"
            else:
                self.reasons[task] = f"closest free slot to your preferred {preferred:%H:%M}"

        self.timetable = dict(sorted(self.timetable.items()))
        return self.timetable

    def explain_plan(self) -> str:
        """Describe why each task was scheduled where it was, or left out."""
        lines = [f"Plan for {self.owner.name} on {self.plan_date:%A %d %B %Y}:"]
        if not self.timetable:
            lines.append("  Nothing scheduled.")
        for start, task in self.timetable.items():
            end = to_time(to_minutes(start) + task.duration_minutes)
            lines.append(
                f"  {start:%H:%M}-{end:%H:%M}  {task.label()} "
                f"[{task.priority.name}] - {self.reasons[task]}"
            )
        if self.unscheduled:
            lines.append("Could not fit:")
            for task in self.unscheduled:
                lines.append(f"  {task.label()} [{task.priority.name}] - {self.reasons[task]}")
        return "\n".join(lines)
