from datetime import date, time

import streamlit as st
from pawpal_system import (
    Frequency, Owner, Pet, Priority, Scheduler, Task, TaskCategory, to_minutes, to_time,
)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption(
    "Plan care tasks for all your pets based on priority, time windows, and your preferences."
)

# --- Owner (kept in session_state so pets and tasks survive reruns) ---

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_name)
owner: Owner = st.session_state.owner
owner.name = owner_name

with st.expander("Preferred times"):
    st.caption("The scheduler places each kind of task as close to its preferred time as it can.")
    with st.form("preference_form"):
        col1, col2 = st.columns(2)
        with col1:
            pref_category = st.selectbox(
                "Task category", list(TaskCategory), format_func=lambda c: c.value.title()
            )
        with col2:
            pref_time = st.time_input("Preferred time", value=time(7, 30), step=300)
        if st.form_submit_button("Save preference"):
            owner.set_preference(pref_category, pref_time)

    for category, preferred in list(owner.preferences.items()):
        col1, col2 = st.columns([3, 1])
        col1.write(f"**{category.value.title()}** around {preferred:%H:%M}")
        if col2.button("Remove", key=f"remove_pref_{category.value}"):
            owner.remove_preference(category)
            st.rerun()

st.divider()

# --- Add a pet ---

st.subheader("Add a Pet")
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
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as error:
                st.error(str(error))

if owner.pets:
    st.table([
        {"Name": p.name, "Age": p.age, "Breed": p.breed, "Tasks": len(p.tasks)}
        for p in owner.pets
    ])
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a task ---

st.subheader("Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("task_form"):
        task_pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
        col1, col2 = st.columns(2)
        with col1:
            description = st.text_input("Description", value="Morning walk")
            category = st.selectbox(
                "Category", list(TaskCategory), format_func=lambda c: c.value.title()
            )
            priority = st.selectbox(
                "Priority", list(Priority), index=2, format_func=lambda p: p.name.title()
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
                st.success(f"Added {task.label()}.")
            except ValueError as error:
                st.error(str(error))

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table([
        {
            "Pet": t.pet.name if t.pet else "",
            "Task": t.description,
            "Category": t.category.value.title(),
            "Priority": t.priority.name.title(),
            "Minutes": t.duration_minutes,
            "Window": f"{t.available_from:%H:%M}-{t.available_until:%H:%M}",
            "Repeats": t.frequency.value.title()
            + (f" ({WEEKDAYS[t.weekday]})" if t.frequency is Frequency.WEEKLY else ""),
            "Done": "✅" if t.completed else "",
        }
        for t in all_tasks
    ])
elif owner.pets:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Build schedule ---

st.subheader("Build Schedule")
col1, col2, col3 = st.columns(3)
with col1:
    plan_date = st.date_input("Plan date", value=date.today())
with col2:
    day_start = st.time_input("Day starts", value=time(7, 0), step=300)
with col3:
    day_end = st.time_input("Day ends", value=time(21, 0), step=300)

if st.button("Generate schedule", type="primary"):
    if not all_tasks:
        st.warning("Add at least one task before generating a schedule.")
    elif day_start >= day_end:
        st.error("The day must start before it ends.")
    else:
        scheduler = Scheduler(owner, plan_date=plan_date, day_start=day_start, day_end=day_end)
        timetable = scheduler.generate_plan()

        st.markdown(f"#### Schedule for {plan_date:%A, %B %d}")
        if timetable:
            st.table([
                {
                    "Time": f"{start:%H:%M}-"
                            f"{to_time(to_minutes(start) + task.duration_minutes):%H:%M}",
                    "Task": task.label(),
                    "Priority": task.priority.name.title(),
                    "Why": scheduler.reasons[task],
                }
                for start, task in timetable.items()
            ])
        else:
            st.info("No tasks are due on this date.")

        for task in scheduler.unscheduled:
            st.warning(f"Could not fit **{task.label()}**: {scheduler.reasons[task]}")

        with st.expander("Plain-text explanation"):
            st.code(scheduler.explain_plan(), language=None)
