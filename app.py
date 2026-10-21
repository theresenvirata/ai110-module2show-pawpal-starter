from datetime import date, time

import streamlit as st
from pawpal_system import (
    Frequency, Owner, Pet, Priority, Scheduler, Task, TaskCategory, to_minutes, to_time,
)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
PRIORITY_BADGES = {Priority.HIGH: "🔴 High", Priority.MEDIUM: "🟠 Medium", Priority.LOW: "🟢 Low"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def end_time(task: Task) -> time:
    """When a scheduled task finishes."""
    return to_time(to_minutes(task.scheduled_at) + task.duration_minutes)


def repeats_text(task: Task) -> str:
    """'Daily' or 'Weekly (Sunday)'."""
    if task.frequency is Frequency.WEEKLY:
        return f"Weekly ({WEEKDAYS[task.weekday]})"
    return "Daily"


def status_text(task: Task, on: date) -> str:
    """Whether the task is done, due on the plan date, or due later."""
    if task.completed:
        return f"✅ Done {task.completed_on:%b %d}"
    if task.is_due(on):
        return "📅 Due"
    if task.due_date is not None and task.due_date > on:
        return f"⏳ From {task.due_date:%b %d}"
    return "⏳ Not today"


def flash(kind: str, message: str) -> None:
    """Show a message after the next rerun."""
    st.session_state.flash = (kind, message)


def show_flash() -> None:
    """Show and clear any message saved by flash()."""
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        getattr(st, kind)(message)


# --- Owner (kept in session_state so pets and tasks survive reruns) ---

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan")
owner: Owner = st.session_state.owner

# --- Sidebar: plan settings ---

with st.sidebar:
    st.header("Plan settings")
    owner.name = st.text_input("Owner name", value=owner.name)
    plan_date = st.date_input("Plan date", value=date.today())
    day_start = st.time_input("Day starts", value=time(7, 0), step=300)
    day_end = st.time_input("Day ends", value=time(21, 0), step=300)

    st.subheader("Preferred times")
    st.caption("Each kind of task is placed as close to its preferred time as possible.")
    with st.form("preference_form", border=False):
        pref_category = st.selectbox(
            "Task category", list(TaskCategory), format_func=lambda c: c.value.title()
        )
        pref_time = st.time_input("Preferred time", value=time(7, 30), step=300)
        if st.form_submit_button("Save preference"):
            owner.set_preference(pref_category, pref_time)

    for category, preferred in list(owner.preferences.items()):
        col1, col2 = st.columns([3, 2])
        col1.write(f"**{category.value.title()}** ~ {preferred:%H:%M}")
        if col2.button("Remove", key=f"remove_pref_{category.value}"):
            owner.remove_preference(category)
            st.rerun()

scheduler = Scheduler(owner, plan_date=plan_date, day_start=day_start, day_end=day_end)

st.title("🐾 PawPal+")
st.caption(
    f"Plan care tasks for all of {owner.name}'s pets based on priority, "
    "time windows, and preferred times."
)
show_flash()

# --- Pets ---

st.subheader("Pets")
with st.expander("Add a pet", expanded=not owner.pets):
    with st.form("pet_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_name = st.text_input("Pet name", value="Mochi")
        with col2:
            pet_age = st.number_input("Age", min_value=0, max_value=40, value=3)
        with col3:
            pet_breed = st.text_input("Breed", value="Tabby Cat")
        if st.form_submit_button("Add pet"):
            if not pet_name.strip():
                st.error("Please enter a pet name.")
            else:
                try:
                    owner.add_pet(Pet(pet_name.strip(), int(pet_age), pet_breed.strip()))
                    flash("success", f"Added {pet_name.strip()}.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

if owner.pets:
    st.dataframe(
        [
            {
                "Name": p.name,
                "Age": p.age,
                "Breed": p.breed,
                "Due on plan date": sum(t.is_due(plan_date) for t in p.tasks),
                "Done": sum(t.completed for t in p.tasks),
            }
            for p in owner.pets
        ],
        hide_index=True,
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks ---

st.subheader("Tasks")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.expander("Add a task", expanded=not owner.get_all_tasks()):
        with st.form("task_form"):
            task_pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
            col1, col2 = st.columns(2)
            with col1:
                description = st.text_input("Description", value="Morning walk")
                category = st.selectbox(
                    "Category", list(TaskCategory), format_func=lambda c: c.value.title()
                )
                priority = st.selectbox(
                    "Priority", list(Priority), index=2, format_func=PRIORITY_BADGES.get
                )
            with col2:
                duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
                available_from = st.time_input("Available from", value=time(7, 0), step=300)
                available_until = st.time_input("Available until", value=time(9, 0), step=300)
            col1, col2 = st.columns(2)
            with col1:
                frequency = st.selectbox(
                    "Repeats", list(Frequency), format_func=lambda f: f.value.title()
                )
            with col2:
                weekday = st.selectbox("Weekday (weekly tasks only)", range(7),
                                       format_func=lambda d: WEEKDAYS[d])

            if st.form_submit_button("Add task"):
                try:
                    task = Task(
                        description.strip() or "Untitled task",
                        category,
                        priority,
                        int(duration),
                        available_from,
                        available_until,
                        frequency,
                        weekday if frequency is Frequency.WEEKLY else None,
                    )
                    owner.get_pet(task_pet_name).add_task(task)
                    flash("success", f"Added {task.label()}.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

if owner.get_all_tasks():
    # Filter and sort with the Scheduler's own methods.
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_filter = st.selectbox("Show pet", ["All pets"] + [p.name for p in owner.pets])
    with col2:
        status_filter = st.selectbox("Show status", ["All", "To do", "Done"])
    with col3:
        sort_choice = st.selectbox("Sort by", ["Time", "Priority"])

    tasks = scheduler.filter_tasks(
        pet_name=None if pet_filter == "All pets" else pet_filter,
        completed={"All": None, "To do": False, "Done": True}[status_filter],
    )
    tasks = scheduler.sort_by_time(tasks) if sort_choice == "Time" else scheduler.sort_by_priority(tasks)

    if tasks:
        st.dataframe(
            [
                {
                    "Status": status_text(t, plan_date),
                    "Pet": t.pet.name if t.pet else "",
                    "Task": t.description,
                    "Category": t.category.value.title(),
                    "Priority": PRIORITY_BADGES[t.priority],
                    "Minutes": t.duration_minutes,
                    "Window": f"{t.available_from:%H:%M}-{t.available_until:%H:%M}",
                    "Repeats": repeats_text(t),
                }
                for t in tasks
            ],
            hide_index=True,
        )
    else:
        st.info("No tasks match these filters.")

    # Mark complete / undo
    to_do = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
    done = scheduler.filter_tasks(completed=True)
    col1, col2 = st.columns(2)
    with col1:
        if to_do:
            pick = st.selectbox("Task to complete", range(len(to_do)),
                                format_func=lambda i: to_do[i].label())
            if st.button("✅ Mark complete"):
                task = to_do[pick]
                next_task = scheduler.mark_task_complete(task)
                message = f"Completed {task.label()}."
                if next_task is not None:
                    message += f" Next one is due {next_task.due_date:%A, %b %d}."
                flash("success", message)
                st.rerun()
    with col2:
        if done:
            pick = st.selectbox("Completed task", range(len(done)),
                                format_func=lambda i: done[i].label())
            if st.button("↩️ Undo"):
                done[pick].mark_incomplete()
                flash("info", f"Marked {done[pick].label()} as not done.")
                st.rerun()
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ---

st.subheader(f"Schedule for {plan_date:%A, %B %d}")

if st.button("Generate schedule", type="primary"):
    st.session_state.show_plan = True

if st.session_state.get("show_plan"):
    if not owner.get_all_tasks():
        st.warning("Add at least one task before generating a schedule.")
    elif day_start >= day_end:
        st.error("The day must start before it ends.")
    else:
        timetable = scheduler.generate_plan()
        planned = scheduler.sort_by_time(list(timetable.values()))
        conflicts = scheduler.detect_conflicts()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Scheduled", len(planned))
        col2.metric("Busy time", f"{sum(t.duration_minutes for t in planned)} min")
        col3.metric("Couldn't fit", len(scheduler.unscheduled))
        col4.metric("Conflicts", len(conflicts))

        if planned:
            st.dataframe(
                [
                    {
                        "Time": f"{t.scheduled_at:%H:%M}-{end_time(t):%H:%M}",
                        "Task": t.label(),
                        "Priority": PRIORITY_BADGES[t.priority],
                        "Why here": scheduler.reasons[t],
                    }
                    for t in planned
                ],
                hide_index=True,
            )
        else:
            st.info("Nothing is due on this date.")

        if conflicts:
            for warning in conflicts:
                st.warning(warning)
        elif planned:
            st.success("No overlapping tasks: every pet's care fits without a clash.")

        for task in scheduler.sort_by_priority(scheduler.unscheduled):
            st.warning(f"Couldn't fit **{task.label()}** "
                       f"({PRIORITY_BADGES[task.priority]}): {scheduler.reasons[task]}")

        with st.expander("Plain-text explanation"):
            st.code(scheduler.explain_plan(), language=None)
