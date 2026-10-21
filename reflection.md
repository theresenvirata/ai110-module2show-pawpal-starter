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

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
