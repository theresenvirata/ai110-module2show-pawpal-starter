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

    biscuit.add_task(Task("Morning walk", TaskCategory.WALK, Priority.HIGH,
                          30, time(7, 0), time(9, 0)))
    biscuit.add_task(Task("Breakfast", TaskCategory.FEEDING, Priority.HIGH,
                          10, time(8, 0), time(8, 30)))
    mochi.add_task(Task("Thyroid meds", TaskCategory.MEDS, Priority.HIGH,
                        5, time(12, 0), time(12, 30)))
    mochi.add_task(Task("Laser pointer play", TaskCategory.ENRICHMENT, Priority.MEDIUM,
                        20, time(17, 0), time(19, 0)))
    biscuit.add_task(Task("Brushing", TaskCategory.GROOMING, Priority.LOW,
                          15, time(18, 0), time(20, 0), Frequency.WEEKLY, weekday=6))

    scheduler = Scheduler(owner, day_start=time(7, 0))
    scheduler.generate_plan()

    print("=" * 60)
    print("Today's Schedule")
    print("=" * 60)
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
