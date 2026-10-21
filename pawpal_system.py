"""PawPal+ core classes, based on diagrams/uml.mmd."""

from dataclasses import dataclass, field
from datetime import date, time


@dataclass
class Pet:
    name: str
    age: int
    breed: str


@dataclass
class Task:
    title: str
    priority: int
    pet: Pet
    time_availability: str

    def set_priority(self, priority: int) -> None:
        """Change how important this task is."""
        pass

    def set_time_availability(self, time_availability: str) -> None:
        """Change when this task can be done."""
        pass


@dataclass
class Scheduler:
    tasks: list[Task] = field(default_factory=list)
    date: date = field(default_factory=date.today)
    timetable: dict[time, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add a task to the schedule."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a task from the schedule."""
        pass


@dataclass
class Owner:
    name: str
    pets: list[Pet] = field(default_factory=list)
    planner: Scheduler = field(default_factory=Scheduler)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        pass
