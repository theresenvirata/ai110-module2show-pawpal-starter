# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
============================================================
Today's Schedule
============================================================
Plan for Jordan on Tuesday 20 October 2026:
  07:30-08:00  Morning walk for Biscuit [HIGH] - at your preferred time
  08:00-08:10  Breakfast for Biscuit [HIGH] - earliest free slot in its window
  12:00-12:05  Thyroid meds for Mochi [HIGH] - earliest free slot in its window
  17:00-17:20  Laser pointer play for Mochi [MEDIUM] - earliest free slot in its window
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
==================================================== test session starts =====================================================
platform win32 -- Python 3.14.8, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\there\OneDrive\Documents\Visual Studio Code\ai110-module2show-pawpal-starter
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 2 items                                                                                                             

tests\test_pawpal.py ..                                                                                                 [100%]

===================================================== 2 passed in 0.02s ======================================================
```

## Short Implementation Summary

PawPal+ keeps track of care tasks for all of an owner's pets and builds a daily plan around priorities, time windows, and the owner's preferred times. The logic lives in `pawpal_system.py`; `main.py` runs a demo from the terminal.

**Classes**

- **`Task`**: one care activity. Stores a description, category (walk, feeding, meds, …), priority, duration, the time window it can happen in, how often it repeats (daily or weekly), and whether it's done. `is_due(date)` says whether it needs doing on a given day.
- **`Pet`**: a pet's details plus its own list of tasks. `add_task()` also links the task back to the pet.
- **`Owner`**: holds the pets and the owner's preferred times for each kind of task, such as walks at 7:30. `get_all_tasks()` returns every pet's tasks in one list.
- **`Scheduler`**: the planner. It is given an `Owner` and reads tasks only through `owner.get_all_tasks()`, so it plans across all pets at once.

**How a plan is made** (`Scheduler.generate_plan()`)

1. Collect every task due on the plan date. Completed tasks, tasks whose next occurrence isn't due yet, and weekly tasks on other days are left out.
2. Sort by priority, highest first. If two tasks tie, the one with the shorter time window goes first.
3. Give each task the earliest start time inside its window that doesn't overlap a task already placed. If the owner has a preferred time for that category, try the times closest to it first.
4. Put any task that can't fit into `unscheduled`.

`explain_plan()` prints the timetable along with the reason for each placement and each skipped task.


## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sort by priority | `Scheduler.sort_by_priority()` | Highest priority first; ties go to the task with the shorter time window. Used by `generate_plan()`. |
| Sort by time | `Scheduler.sort_by_time()` | Earliest first, by scheduled time, or by window start if not scheduled yet. |
| Filtering | `Scheduler.filter_tasks()`, `Scheduler.get_due_tasks()` | Filter by pet name, completion status, or both; due tasks only. |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()`, `Task.is_due()` | Completing a task creates the next occurrence. |
| Conflict detection | `Scheduler.detect_conflicts()`, `Scheduler.has_conflict()`, `overlaps()` | Warns about overlapping tasks instead of crashing. |

**Sorting.** `sort_by_priority()` decides the order in which `generate_plan()` places tasks. `sort_by_time()` is for showing tasks in time order. Its `sorted()` key is a lambda that turns each task's time into an `"HH:MM"` string. Zero-padded strings sort the same way as the times they stand for (`"07:30" < "12:00"`).

**Filtering.** `filter_tasks(pet_name=None, completed=None)` narrows the owner's tasks to one pet, to done or not-done tasks, or both. A filter left as `None` is skipped. `get_due_tasks()` keeps only the tasks due on the plan date, and those are the only tasks the scheduler plans.

**Recurring tasks.** When a daily or weekly task is marked complete (`Task.mark_complete()` or `Scheduler.mark_task_complete()`), `next_occurrence()` makes a fresh copy. The copy's `due_date` is the next day for daily tasks, or the same weekday next week for weekly ones, and it is added to the same pet. `is_due()` treats a completed task as finished for good and doesn't let the new copy show up before its `due_date`, so a day never gets two copies of the same task. Completing a task twice does nothing the second time. `mark_incomplete()` removes the copy that was created.

**Conflict detection.** `generate_plan()` uses `has_conflict()` so it never schedules two overlapping tasks. A time can still be set by hand, though, so `detect_conflicts()` checks every pair of timed tasks, for the same pet or different pets. It returns a list of warnings such as `Warning: Morning walk for Biscuit (07:30-08:00) overlaps Thyroid meds for Mochi (07:30-07:35) [different pets]`. An empty list means no conflicts, and it never raises an error. Both methods use the same `overlaps()` check: tasks that share at least one minute conflict, and back-to-back tasks (one ends at 8:00, the next starts at 8:00) don't.
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
