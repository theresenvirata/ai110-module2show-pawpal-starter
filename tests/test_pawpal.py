from datetime import date, time

from pawpal_system import Pet, Priority, Task, TaskCategory


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
