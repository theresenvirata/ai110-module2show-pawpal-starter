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
