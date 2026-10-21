"""Demo: build an owner with two pets and print today's schedule."""

from datetime import time

from pawpal_system import Frequency, Owner, Pet, Priority, Scheduler, Task, TaskCategory


def main() -> None:
    owner = Owner("Jordan")
    owner.set_preference(TaskCategory.WALK, time(7, 30))

    biscuit = Pet("Biscuit", 3, "Golden Retriever")
    mochi = Pet("Mochi", 5, "Tabby Cat")
    owner.add_pet(biscuit)
    owner.add_pet(mochi)

    # Added out of time order on purpose, to exercise sort_by_time().
    mochi.add_task(Task("Laser pointer play", TaskCategory.ENRICHMENT, Priority.MEDIUM,
                        20, time(17, 0), time(19, 0)))
    biscuit.add_task(Task("Brushing", TaskCategory.GROOMING, Priority.LOW,
                          15, time(18, 0), time(20, 0), Frequency.WEEKLY, weekday=6))
    mochi.add_task(Task("Thyroid meds", TaskCategory.MEDS, Priority.HIGH,
                        5, time(12, 0), time(12, 30)))
    biscuit.add_task(Task("Breakfast", TaskCategory.FEEDING, Priority.HIGH,
                          10, time(8, 0), time(8, 30)))
    biscuit.add_task(Task("Morning walk", TaskCategory.WALK, Priority.HIGH,
                          30, time(7, 0), time(9, 0)))

    scheduler = Scheduler(owner, day_start=time(7, 0))

    print_tasks("Tasks as added", owner.get_all_tasks())
    print_tasks("Sorted by time (before scheduling)", scheduler.sort_by_time(owner.get_all_tasks()))

    scheduler.generate_plan()
    breakfast = next(t for t in biscuit.tasks if t.description == "Breakfast")
    next_breakfast = scheduler.mark_task_complete(breakfast)
    print(f"Completed {breakfast.label()}; next one is due {next_breakfast.due_date:%A %d %B}.")

    print_tasks("Sorted by time (after scheduling)", scheduler.sort_by_time(owner.get_all_tasks()))
    print_tasks("Only Mochi's tasks", scheduler.filter_tasks(pet_name="Mochi"))
    print_tasks("Completed tasks", scheduler.filter_tasks(completed=True))
    print_tasks("Biscuit's incomplete tasks, by time",
                scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Biscuit", completed=False)))

    print("=" * 60)
    print("Today's Schedule")
    print("=" * 60)
    print(scheduler.explain_plan())

    print("\n--- Conflict check on the generated plan ---")
    print_conflicts(scheduler.detect_conflicts())

    # The owner moves two of Mochi's tasks by hand onto Biscuit's walk at 07:30.
    walk = next(t for t in biscuit.tasks if t.description == "Morning walk")
    for task in mochi.tasks:
        task.scheduled_at = walk.scheduled_at
    print("\n--- Conflict check after moving Mochi's tasks to 07:30 ---")
    print_conflicts(scheduler.detect_conflicts())


def print_conflicts(warnings: list[str]) -> None:
    """Print each conflict warning, or say there are none."""
    for warning in warnings or ["No conflicts."]:
        print(f"  {warning}")


def print_tasks(title: str, tasks: list[Task]) -> None:
    """Print a titled list of tasks, one per line."""
    print(f"\n--- {title} ---")
    if not tasks:
        print("  (none)")
    for t in tasks:
        when = f"{t.scheduled_at:%H:%M}" if t.scheduled_at else f"from {t.available_from:%H:%M}"
        done = " [done]" if t.completed else ""
        print(f"  {when:>10}  {t.label()}{done}")
    print()


if __name__ == "__main__":
    main()
