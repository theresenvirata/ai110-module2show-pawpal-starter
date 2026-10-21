# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- "Owner" class that can told pets and a planner.
- Have a "Pet" class that allows you to add a pet with attriutes like their name, age, and breed.
- Have a "Task" class with attributes of a title, priority, pet, and time availability. These tasks can be created, priority and time availability can be changed at any time of the day.
- Have another class called "Scheduler" which takes an array of "Task"s, a set date, and a timetable of tasks to do at specific times of the day such as grooming, walking, feeding, etc. Tasks can be removed and added at any time for the "Scheduler" class.

**b. Design changes**

- Yes my design did change. There is now a new Priority enum so that a higher value means the a greater priority and will be shown first when tasks are listed.
- Added owner preferences on whether the owner prefers to walk, feed, enich, groom, or give meds to their pets. This will keep the tasks organized between owners and prevents bugs.
- Categories for generic tasks like walking, feeding, and meds since there are different ways to walk a pet, feed them, and give them meals. For example, feed lunch compared to feeding dinner.
- Added Frequency enum for reoccuring tasks
- has_conflict() method for Scheduler to ensure no overlapping.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- My scheduler considers five constraints:
  - **Time available in the day:** tasks only go between the Scheduler's `day_start` and `day_end`.
  - **Each task's time window:** a task must start and finish between its `available_from` and `available_until`. For example, meds can only be given between 12:00 and 12:30.
  - **Priority:** HIGH tasks are placed before MEDIUM, and MEDIUM before LOW.
  - **No overlaps:** `has_conflict()` stops two tasks from being scheduled at the same time, even when they belong to different pets.
  - **Owner preferences:** if the owner prefers a time for a kind of task, like walks at 7:30, the scheduler tries times as close to that as possible.
- The scheduler also only plans tasks that are due that day. Weekly tasks only show up on their weekday, and tasks already marked complete for the day are skipped.
- I decided time windows and priority matter most because they are about the pet's health and needs: meds or feeding at the wrong time can actually hurt a pet. Preferences matter least because they are about the owner's convenience, so the scheduler treats them as "as close as possible" and not a hard rule.

**b. Tradeoffs**

- My scheduler puts fitting every important task in ahead of hitting the owner's exact preferred time. When two tasks have the same priority, the one with the shorter time window gets placed first because it has fewer places it can go. In my test, Biscuit's walk had a preferred time of 8:30, but Mochi's meds had the same priority and only a 15-minute window, so the meds took 8:30 and the walk moved to 8:35.
- This is reasonable for pet care because a walk 5 minutes late doesn't matter, but missing a medication window could. The scheduler also places tasks one at a time and never goes back to rearrange them. That means it might not find the absolute best plan, but it is simple, fast, and easy to explain to the owner, which matters more for a daily pet care app.
- My conflict detection (`detect_conflicts()`) checks whether task durations overlap, not just whether two tasks start at the same time. A walk from 7:30 to 8:00 and meds at 7:45 get flagged even though their start times are different. To do this it compares every pair of tasks, so the work grows with the square of the number of tasks. A faster version could sort the tasks and only compare neighbors, but one owner's pets only have a handful of tasks a day, so the simpler pairwise check is fast enough and easier to trust. It also only warns and never moves anything, because if the owner set a time by hand they should decide which task to change.
- When I asked the AI to simplify `has_conflict()`, it suggested turning the loop into a one-line `any(...)` with all the overlap math written inline. That was more "Pythonic" but harder to read. I kept the `any(...)` but moved the math into a named helper, `overlaps()`, so the method reads like a sentence and `detect_conflicts()` can reuse the same check.

---

## 3. AI Collaboration

**a. How you used AI**

- I used Claude Code at almost every step:
  - turning my brainstormed classes into a Mermaid UML diagram
  - generating the class skeleton
  - reviewing the skeleton for missing relationships and logic problems
  - implementing the scheduling logic
  - writing `main.py`, the tests, and docstrings
- The review step was the most useful. The AI pointed out problems I hadn't noticed: my Task had no duration, there was no method to actually generate the plan, `time_availability` as a string couldn't be compared, and a field named `date` was hiding the `date` type.
- The most helpful prompts were specific and pointed at my own material, like "create the diagram based on the attributes listed under initial design" or "review the skeleton for missing relationships". Asking it to "give a summary of what changed and why" also helped, because then I could check each change myself instead of just trusting the new code.

**b. Judgment and verification**

- After the review, the AI left out owner preferences because my design didn't define any yet. I didn't accept that, because the README lists owner preferences as one of the constraints the app must consider. I told it to add them and to check the README for anything else missing. That turned up more gaps: task categories, editing a task's duration, recurring tasks, and conflict handling.
- I also changed the AI's structure to match the assignment. Its version had tasks stored in the Scheduler and the Owner holding a planner. The assignment needed each Pet to hold its own tasks and the Scheduler to read them through an Owner method (`get_all_tasks()`), so I had it restructure the classes that way.
- To verify the AI's work, I ran `main.py` and read the printed schedule to make sure the times made sense and nothing overlapped. I also ran `pytest` and checked that the tests passed, and compared the code against the README's requirements and the UML diagram to make sure they matched.

**c. AI strategy**

- **Most effective features:**
  - **Agent mode editing several files at once.** One request could update `pawpal_system.py`, the UML diagram, and the README together, so they didn't drift apart.
  - **The AI running code itself.** It ran `main.py`, `pytest`, and a headless test of the Streamlit app after making changes, so I saw real output and not just "this should work". When I asked it to add tests, it found that plain `pytest` couldn't import my code and fixed it with a `pytest.ini`.
  - **Asking for a review before writing logic.** The review of my skeleton caught a missing duration, a missing plan method, and a field name that hid a type before any of those turned into bugs.
- **A suggestion I modified to keep the design clean:** in the AI's first version, the `Owner` held a `Scheduler` as its `planner`, and the Scheduler kept its own list of tasks. That meant tasks lived in a different place than the pets they belonged to, and removing a pet could leave its tasks behind. I had it change the structure so each `Pet` holds its own tasks, the `Owner` has one method that collects them (`get_all_tasks()`), and the `Scheduler` reads only through that method. Now there is one place where tasks live, and removing a pet removes its tasks automatically.
- **Separate chat sessions for different phases:** I used one session for design, the class skeleton, and the first implementation, and a separate one for the Phase 3 algorithms (sorting, filtering, conflict detection, recurrence) and the tests. Each session only had to focus on one goal, so the AI's answers stayed on that phase instead of mixing in older ideas. Starting fresh also made me write down where the project stood (in the README, the UML, and this reflection), which made it easier to pick back up.
- **Being the "lead architect":** the AI can write a lot of working code quickly, but it makes choices I didn't ask for and fills gaps with its own guesses. My job was to know what the system needed and to check the AI's work against that. I kept the README requirements and the UML as my source of truth, asked for summaries of what changed and why, and read and ran the results myself. The AI was best at doing the work. I was responsible for deciding what the work should be and whether it was right.

---

## 4. Testing and Verification

**a. What you tested**

- `tests/test_pawpal.py` has 21 tests covering:
  - **Basics:** marking a task complete changes its status, and adding a task increases the pet's task count.
  - **Sorting:** `sort_by_time()` returns tasks in time order and uses the booked time once a task is scheduled. `sort_by_priority()` puts the highest priority first and breaks ties by the tighter time window.
  - **Recurring tasks:** completing a daily task creates a copy due tomorrow, even from Dec 31 to Jan 1. Completing a weekly task, even late, creates a copy due on its next weekday. Completing twice or undoing a completion doesn't leave extra copies.
  - **Conflict detection:** overlapping tasks and tasks with the same start time are flagged for the same pet or different pets, while back-to-back and unscheduled tasks are not.
  - **Scheduling boundaries:** a task that exactly fills its window gets scheduled, a task longer than its window ends up unscheduled, a generated plan has no conflicts, and generating twice gives the same plan.
- These tests matter because they cover the parts that are easy to get subtly wrong: off-by-one times (back-to-back tasks), dates that roll over months and years, and recurring tasks that could double up or never come back. A bug there would mean a pet missing a meal or medication.

**b. Confidence**

- I'm confident (5/5) the scheduler works for the cases it was built for. All 21 tests pass, `main.py` gives the schedule I expect, and the Streamlit app was tested by adding pets and tasks, generating a plan, and marking tasks complete and undoing them.
- Edge cases I would test next:
  - a task whose window crosses midnight (for example, 23:00 to 01:00)
  - a preferred time that falls outside a task's window
  - a day so full that a HIGH task can't fit, to check it's reported clearly
  - a weekly task created on a different weekday than the one it repeats on
  - a pet removed while its tasks are in the current plan

---

## 5. Reflection

**a. What went well**

- I'm most satisfied that the scheduler explains itself. Every task in the plan says why it was placed there ("at your preferred time", "closest free slot to your preferred 08:30"), and tasks that don't fit are listed with the reason instead of disappearing. That makes the plan easy to trust and easy to check.

**b. What you would improve**

- Save the owner, pets, and tasks to a file. Right now everything is kept in the Streamlit session, so refreshing the page loses it.
- Support tasks at a fixed time, like a vet appointment at 14:00, not just a window.
- Let the scheduler rearrange tasks it already placed when a new task can't fit, instead of placing each task once and never going back.
- Allow editing a task in the app. The backend has methods for this (`set_priority()`, `set_duration()`, `set_time_availability()`), but the UI only adds and completes tasks.

**c. Key takeaway**

- Design first, then let the AI build. Having a UML diagram and a clear list of requirements meant I could tell when the AI went in a different direction, and I could ask for specific fixes instead of starting over. The AI made the coding much faster, but the design decisions, and checking that the code matched them, were still my job.
