from datetime import date, time

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task, TaskCategory


def make_task(description: str = "Morning walk") -> Task:
    return Task(description, TaskCategory.WALK, Priority.HIGH, 30, time(7, 0), time(9, 0))


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete(date(2026, 10, 20))

    assert task.completed is True
    assert task.completed_on == date(2026, 10, 20)


def test_add_task_increases_pet_task_count():
    pet = Pet("Biscuit", 3, "Golden Retriever")
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1


def test_completing_daily_task_creates_tomorrows_task():
    pet = Pet("Biscuit", 3, "Golden Retriever")
    task = make_task()
    pet.add_task(task)

    next_task = task.mark_complete(date(2026, 10, 20))

    assert next_task in pet.tasks and next_task.pet is pet
    assert next_task.due_date == date(2026, 10, 21)
    assert next_task.completed is False
    assert not task.is_due(date(2026, 10, 21))
    assert not next_task.is_due(date(2026, 10, 20))
    assert next_task.is_due(date(2026, 10, 21))


def test_completing_weekly_task_creates_next_weeks_task():
    task = Task("Brushing", TaskCategory.GROOMING, Priority.LOW, 15,
                time(18, 0), time(20, 0), Frequency.WEEKLY, weekday=6)
    Pet("Biscuit", 3, "Golden Retriever").add_task(task)

    next_task = task.mark_complete(date(2026, 10, 25))  # a Sunday

    assert next_task.due_date == date(2026, 11, 1)
    assert not next_task.is_due(date(2026, 10, 25))
    assert next_task.is_due(date(2026, 11, 1))


def test_completing_twice_or_undoing_does_not_leave_extra_tasks():
    pet = Pet("Biscuit", 3, "Golden Retriever")
    task = make_task()
    pet.add_task(task)

    task.mark_complete(date(2026, 10, 20))
    assert task.mark_complete(date(2026, 10, 20)) is None
    assert len(pet.tasks) == 2

    task.mark_incomplete()
    assert pet.tasks == [task]


def make_scheduler() -> tuple[Scheduler, Pet, Pet]:
    owner = Owner("Jordan")
    biscuit = Pet("Biscuit", 3, "Golden Retriever")
    mochi = Pet("Mochi", 5, "Tabby Cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)
    return Scheduler(owner, plan_date=date(2026, 10, 20)), biscuit, mochi


def test_sort_by_time_orders_tasks_earliest_first():
    scheduler, biscuit, _ = make_scheduler()
    late = Task("Dinner", TaskCategory.FEEDING, Priority.HIGH, 10, time(17, 0), time(18, 0))
    early = Task("Breakfast", TaskCategory.FEEDING, Priority.HIGH, 10, time(9, 0), time(10, 0))
    biscuit.add_task(late)
    biscuit.add_task(early)

    assert scheduler.sort_by_time(biscuit.tasks) == [early, late]


def test_detect_conflicts_warns_about_overlaps_only():
    scheduler, biscuit, mochi = make_scheduler()
    walk = make_task()
    meds = Task("Meds", TaskCategory.MEDS, Priority.HIGH, 5, time(7, 0), time(9, 0))
    play = Task("Play", TaskCategory.ENRICHMENT, Priority.LOW, 10, time(7, 0), time(9, 0))
    biscuit.add_task(walk)
    mochi.add_task(meds)
    mochi.add_task(play)
    walk.scheduled_at = time(7, 0)   # 07:00-07:30
    meds.scheduled_at = time(7, 15)  # overlaps the walk
    play.scheduled_at = time(7, 30)  # starts as the walk ends: no conflict

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Morning walk for Biscuit" in warnings[0] and "Meds for Mochi" in warnings[0]
    assert "different pets" in warnings[0]


def test_generated_plan_has_no_conflicts():
    scheduler, biscuit, mochi = make_scheduler()
    biscuit.add_task(make_task())
    mochi.add_task(Task("Meds", TaskCategory.MEDS, Priority.HIGH, 5, time(7, 0), time(9, 0)))

    scheduler.generate_plan()

    assert scheduler.detect_conflicts() == []


# --- Sorting correctness ---

def test_sort_by_time_prefers_scheduled_time_over_window():
    scheduler, biscuit, _ = make_scheduler()
    walk = make_task()                 # window opens 07:00...
    walk.scheduled_at = time(8, 30)    # ...but it's booked for 08:30
    meds = Task("Meds", TaskCategory.MEDS, Priority.HIGH, 5, time(8, 0), time(9, 0))
    biscuit.add_task(walk)
    biscuit.add_task(meds)

    assert scheduler.sort_by_time(biscuit.tasks) == [meds, walk]


def test_generated_plan_is_in_chronological_order():
    scheduler, biscuit, mochi = make_scheduler()
    biscuit.add_task(Task("Dinner", TaskCategory.FEEDING, Priority.HIGH, 10, time(17, 0), time(18, 0)))
    mochi.add_task(Task("Play", TaskCategory.ENRICHMENT, Priority.LOW, 20, time(12, 0), time(13, 0)))
    biscuit.add_task(Task("Breakfast", TaskCategory.FEEDING, Priority.MEDIUM, 10, time(8, 0), time(9, 0)))

    timetable = scheduler.generate_plan()
    ordered = scheduler.sort_by_time(scheduler.owner.get_all_tasks())

    assert list(timetable) == sorted(timetable)
    assert [t.description for t in ordered] == ["Breakfast", "Play", "Dinner"]


def test_sort_by_priority_breaks_ties_by_tighter_window_then_insertion_order():
    scheduler, _, _ = make_scheduler()
    wide = Task("Wide", TaskCategory.OTHER, Priority.HIGH, 10, time(8, 0), time(12, 0))
    tight = Task("Tight", TaskCategory.OTHER, Priority.HIGH, 10, time(8, 0), time(9, 0))
    tight_twin = Task("Tight twin", TaskCategory.OTHER, Priority.HIGH, 10, time(8, 0), time(9, 0))
    low = Task("Low", TaskCategory.OTHER, Priority.LOW, 10, time(8, 0), time(8, 30))

    result = scheduler.sort_by_priority([low, wide, tight, tight_twin])

    assert result == [tight, tight_twin, wide, low]


# --- Recurrence logic ---

def test_completed_daily_task_moves_to_next_days_plan():
    scheduler, biscuit, _ = make_scheduler()          # plan_date 2026-10-20
    task = Task("Walk", TaskCategory.WALK, Priority.HIGH, 30, time(8, 0), time(10, 0))
    biscuit.add_task(task)

    next_task = scheduler.mark_task_complete(task)

    assert scheduler.get_due_tasks() == []
    tomorrow = Scheduler(scheduler.owner, plan_date=date(2026, 10, 21))
    assert tomorrow.get_due_tasks() == [next_task]


def test_daily_recurrence_rolls_over_year_end():
    task = make_task()
    Pet("Biscuit", 3, "Golden Retriever").add_task(task)

    next_task = task.mark_complete(date(2026, 12, 31))

    assert next_task.due_date == date(2027, 1, 1)


def test_weekly_task_completed_late_is_next_due_on_its_weekday():
    task = Task("Brushing", TaskCategory.GROOMING, Priority.LOW, 15,
                time(18, 0), time(20, 0), Frequency.WEEKLY, weekday=6)
    Pet("Biscuit", 3, "Golden Retriever").add_task(task)

    next_task = task.mark_complete(date(2026, 10, 28))  # a Wednesday, 3 days late

    assert next_task.due_date == date(2026, 11, 1)      # the following Sunday


def test_undoing_completion_removes_whole_chain_of_occurrences():
    pet = Pet("Biscuit", 3, "Golden Retriever")
    task = make_task()
    pet.add_task(task)

    second = task.mark_complete(date(2026, 10, 20))
    second.mark_complete(date(2026, 10, 21))
    task.mark_incomplete()

    assert pet.tasks == [task]


# --- Conflict detection ---

def test_detect_conflicts_flags_duplicate_start_times_for_same_pet():
    scheduler, biscuit, _ = make_scheduler()
    walk = make_task()
    meds = Task("Meds", TaskCategory.MEDS, Priority.HIGH, 5, time(7, 0), time(9, 0))
    biscuit.add_task(walk)
    biscuit.add_task(meds)
    walk.scheduled_at = time(7, 0)
    meds.scheduled_at = time(7, 0)

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Morning walk for Biscuit" in warnings[0] and "Meds for Biscuit" in warnings[0]
    assert "same pet" in warnings[0]


def test_detect_conflicts_reports_every_overlapping_pair():
    scheduler, biscuit, mochi = make_scheduler()
    tasks = [make_task(f"Task {i}") for i in range(3)]
    biscuit.add_task(tasks[0])
    biscuit.add_task(tasks[1])
    mochi.add_task(tasks[2])
    for t in tasks:
        t.scheduled_at = time(7, 0)

    assert len(scheduler.detect_conflicts()) == 3


def test_detect_conflicts_ignores_unscheduled_tasks():
    scheduler, biscuit, _ = make_scheduler()
    scheduled = make_task("Scheduled")
    scheduled.scheduled_at = time(7, 0)
    biscuit.add_task(scheduled)
    biscuit.add_task(make_task("Not scheduled"))

    assert scheduler.detect_conflicts() == []


# --- Scheduling boundaries ---

def test_task_that_exactly_fills_its_window_is_scheduled():
    scheduler, biscuit, _ = make_scheduler()
    task = Task("Walk", TaskCategory.WALK, Priority.HIGH, 30, time(8, 0), time(8, 30))
    biscuit.add_task(task)

    scheduler.generate_plan()

    assert task.scheduled_at == time(8, 0)


def test_task_longer_than_its_window_is_unscheduled():
    scheduler, biscuit, _ = make_scheduler()
    task = Task("Walk", TaskCategory.WALK, Priority.HIGH, 30, time(8, 0), time(8, 15))
    biscuit.add_task(task)

    assert scheduler.generate_plan() == {}
    assert scheduler.unscheduled == [task]
    assert task.scheduled_at is None


def test_generate_plan_twice_gives_same_result():
    scheduler, biscuit, mochi = make_scheduler()
    biscuit.add_task(Task("Walk", TaskCategory.WALK, Priority.HIGH, 30, time(8, 0), time(9, 0)))
    mochi.add_task(Task("Meds", TaskCategory.MEDS, Priority.HIGH, 5, time(8, 0), time(9, 0)))

    first = scheduler.generate_plan()
    second = scheduler.generate_plan()

    assert first == second
