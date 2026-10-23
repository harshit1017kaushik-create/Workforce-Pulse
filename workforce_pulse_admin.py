import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import date

st.set_page_config(
    page_title="Workforce Pulse | Admin",
    page_icon="🔐",
    layout="wide",
)

# ---------- Admin login ----------
st.title("🔐 Workforce Pulse — Admin")
st.caption("Authorized employee management portal")

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.subheader("Admin Login")
    with st.form("admin_login"):
        username = st.text_input("Admin username")
        password = st.text_input("Admin password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            admin_secrets = st.secrets["admin"]
            if (
                username == str(admin_secrets["username"])
                and password == str(admin_secrets["password"])
            ):
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Invalid admin username or password.")
        except (KeyError, FileNotFoundError):
            st.error("Admin credentials are not configured in this app's Secrets.")
    st.stop()

top_left, top_right = st.columns([5, 1])
with top_right:
    if st.button("Log out"):
        st.session_state.admin_authenticated = False
        st.rerun()

# ---------- Aiven connection from Streamlit Secrets ----------
def get_connection():
    config = st.secrets["mysql"]
    return mysql.connector.connect(
        host=config["host"],
        port=int(config["port"]),
        user=config["user"],
        password=config["password"],
        database=config["database"],
        connection_timeout=10,
    )

@st.cache_data(ttl=30, show_spinner=False)
def load_data():
    """Read employee and event data. This function never writes to the database."""
    connection = get_connection()
    try:
        employees = pd.read_sql(
            """
            SELECT employee_id, employee_name, department, job_title, location,
                   joining_date, employment_status, exit_date
            FROM employees
            ORDER BY employee_id
            """,
            connection,
        )
        events = pd.read_sql(
            """
            SELECT event_id, employee_id, event_type, event_date, description, created_at
            FROM employee_events
            ORDER BY event_date DESC, event_id DESC
            LIMIT 100
            """,
            connection,
        )
        return employees, events
    finally:
        connection.close()

def record_event(cursor, employee_id, event_type, event_date, description):
    cursor.execute(
        """
        INSERT INTO employee_events (employee_id, event_type, event_date, description)
        VALUES (%s, %s, %s, %s)
        """,
        (employee_id, event_type, event_date, description),
    )

st.info("Changes made here are written to the Aiven database used by this admin app.")
if st.button("Refresh data"):
    load_data.clear()
    st.rerun()

try:
    employees, events = load_data()
except (Error, KeyError, ValueError):
    st.error("Could not load dashboard data. Check this app's Secrets and database permissions.")
    st.stop()

# ---------- Summary ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Employees", f"{len(employees):,}")
c2.metric("Active Employees", f"{int((employees['employment_status'] == 'Active').sum()):,}")
c3.metric("Resigned Employees", f"{int((employees['employment_status'] == 'Resigned').sum()):,}")
c4.metric("HR Events (loaded)", f"{len(events):,}")

st.divider()
st.subheader("Employee Directory")
search = st.text_input("Search by employee name, department, or job title")
directory = employees.copy()
if search.strip():
    term = search.strip().lower()
    mask = (
        directory["employee_name"].fillna("").astype(str).str.lower().str.contains(term, regex=False)
        | directory["department"].fillna("").astype(str).str.lower().str.contains(term, regex=False)
        | directory["job_title"].fillna("").astype(str).str.lower().str.contains(term, regex=False)
    )
    directory = directory[mask]
st.dataframe(directory, use_container_width=True, hide_index=True)

# Common choices taken from the existing app_v4.py.
DEPARTMENTS = [
    "IT", "HR", "Finance", "Sales", "Marketing",
    "Operations", "Customer Support", "Analytics",
]
LOCATIONS = [
    "Delhi", "Gurugram", "Noida", "Faridabad",
    "Ghaziabad", "Jaipur", "Chandigarh", "Lucknow",
]

# ---------- Add employee ----------
st.divider()
st.subheader("Add a New Employee")
st.caption("Employee record and Hired event are committed together.")

with st.form("add_employee_form", clear_on_submit=True):
    new_name = st.text_input("Employee name", max_chars=100)
    col_a, col_b = st.columns(2)
    with col_a:
        new_department = st.selectbox("Department", DEPARTMENTS)
        new_job_title = st.text_input("Job title", max_chars=100)
        new_location = st.selectbox("Location", LOCATIONS)
    with col_b:
        joining_date = st.date_input("Joining date", value=date.today(), max_value=date.today())
    confirm_add = st.checkbox("I confirm these employee details are correct.")
    add_submitted = st.form_submit_button("Add employee and record hire", type="primary")

if add_submitted:
    clean_name = new_name.strip()
    clean_title = new_job_title.strip()
    if not clean_name or not clean_title:
        st.warning("Enter both employee name and job title.")
    elif not confirm_add:
        st.warning("Please confirm the employee details before saving.")
    else:
        connection = None
        cursor = None
        try:
            connection = get_connection()
            connection.start_transaction()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT employee_id FROM employees
                WHERE LOWER(TRIM(employee_name)) = LOWER(TRIM(%s))
                  AND department = %s
                  AND COALESCE(job_title, '') = %s
                  AND joining_date = %s
                LIMIT 1 FOR UPDATE
                """,
                (clean_name, new_department, clean_title, joining_date),
            )
            duplicate = cursor.fetchone()
            if duplicate:
                raise ValueError(
                    f"A matching employee already exists (ID {duplicate['employee_id']})."
                )

            cursor.execute(
                """
                INSERT INTO employees
                    (employee_name, department, job_title, location,
                     joining_date, employment_status, exit_date)
                VALUES (%s, %s, %s, %s, %s, 'Active', NULL)
                """,
                (clean_name, new_department, clean_title, new_location, joining_date),
            )
            new_id = cursor.lastrowid
            record_event(cursor, new_id, "Hired", joining_date, f"{clean_name} joined the company")
            connection.commit()
            load_data.clear()
            st.success(f"Added {clean_name} (Employee ID {new_id}) and recorded the Hired event.")
            st.rerun()
        except ValueError as exc:
            if connection is not None:
                connection.rollback()
            st.warning(str(exc))
        except Error:
            if connection is not None:
                connection.rollback()
            st.error("The employee was not saved. Check the app logs and database permissions.")
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None and connection.is_connected():
                connection.close()

# ---------- Change department ----------
st.divider()
st.subheader("Change an Employee's Department")
active_employees = employees[employees["employment_status"].astype(str).eq("Active")].copy()

if active_employees.empty:
    st.info("There are no active employees available for a department change.")
else:
    employee_map = {
        int(row["employee_id"]): row
        for _, row in active_employees.iterrows()
    }
    selected_id = st.selectbox(
        "Select active employee",
        options=list(employee_map.keys()),
        format_func=lambda eid: (
            f'{eid} — {employee_map[eid]["employee_name"]} '
            f'(Current: {employee_map[eid]["department"]})'
        ),
        key="department_employee",
    )
    selected_row = employee_map[selected_id]
    current_department = str(selected_row["department"])
    destination_options = [d for d in DEPARTMENTS if d != current_department]
    if not destination_options:
        destination_options = sorted(
            d for d in employees["department"].dropna().astype(str).unique()
            if d != current_department
        )

    with st.form("change_department_form"):
        new_department_for_employee = st.selectbox(
            "New department", destination_options, key="destination_department"
        )
        confirm_department = st.checkbox("I confirm this department change.")
        change_submitted = st.form_submit_button("Save department change", type="primary")

    if change_submitted:
        if not confirm_department:
            st.warning("Please confirm the department change.")
        else:
            connection = None
            cursor = None
            try:
                connection = get_connection()
                connection.start_transaction()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT employee_name, department, employment_status
                    FROM employees WHERE employee_id = %s FOR UPDATE
                    """,
                    (selected_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Employee record not found. Refresh and try again.")
                if row["employment_status"] != "Active":
                    raise ValueError("Only active employees can change department.")
                old_department = row["department"]
                if old_department == new_department_for_employee:
                    raise ValueError("Employee is already in that department.")
                cursor.execute(
                    "UPDATE employees SET department = %s WHERE employee_id = %s",
                    (new_department_for_employee, selected_id),
                )
                record_event(
                    cursor, selected_id, "Department Changed", date.today(),
                    f"Department changed from {old_department} to {new_department_for_employee}",
                )
                connection.commit()
                load_data.clear()
                st.success(f"Updated department for {row['employee_name']}.")
                st.rerun()
            except ValueError as exc:
                if connection is not None:
                    connection.rollback()
                st.warning(str(exc))
            except Error:
                if connection is not None:
                    connection.rollback()
                st.error("Department change was not saved. Check app logs and database permissions.")
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

# ---------- Record resignation ----------
st.divider()
st.subheader("Record an Employee Resignation")
if active_employees.empty:
    st.info("There are no active employees available to resign.")
else:
    resignation_map = {
        int(row["employee_id"]): row
        for _, row in active_employees.iterrows()
    }
    with st.form("resignation_form"):
        resignation_id = st.selectbox(
            "Select active employee",
            options=list(resignation_map.keys()),
            format_func=lambda eid: (
                f'{eid} — {resignation_map[eid]["employee_name"]} '
                f'({resignation_map[eid]["department"]})'
            ),
            key="resignation_employee",
        )
        selected_joining = pd.to_datetime(
            resignation_map[resignation_id]["joining_date"], errors="coerce"
        )
        min_exit_date = selected_joining.date() if pd.notna(selected_joining) else date(1900, 1, 1)
        exit_date = st.date_input(
            "Exit date",
            value=max(date.today(), min_exit_date),
            min_value=min_exit_date,
            max_value=date.today(),
            key="resignation_exit_date",
        )
        reason = st.text_input("Reason / note (optional)", max_chars=200)
        confirm_resignation = st.checkbox("I confirm this employee is leaving the company.")
        resign_submitted = st.form_submit_button("Record resignation", type="primary")

    if resign_submitted:
        if not confirm_resignation:
            st.warning("Please confirm the resignation before saving.")
        else:
            connection = None
            cursor = None
            try:
                connection = get_connection()
                connection.start_transaction()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    """
                    SELECT employee_name, joining_date, employment_status
                    FROM employees WHERE employee_id = %s FOR UPDATE
                    """,
                    (resignation_id,),
                )
                row = cursor.fetchone()
                if not row:
                    raise ValueError("Employee record not found. Refresh and try again.")
                if row["employment_status"] != "Active":
                    raise ValueError("Only active employees can be marked as resigned.")
                actual_joining = pd.to_datetime(row["joining_date"], errors="coerce")
                if pd.notna(actual_joining) and exit_date < actual_joining.date():
                    raise ValueError("Exit date cannot be earlier than the joining date.")
                if exit_date > date.today():
                    raise ValueError("Exit date cannot be in the future.")

                cursor.execute(
                    """
                    UPDATE employees
                    SET employment_status = 'Resigned', exit_date = %s
                    WHERE employee_id = %s AND employment_status = 'Active'
                    """,
                    (exit_date, resignation_id),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Employee status did not change. Refresh and try again.")

                description = f"{row['employee_name']} resigned from the company"
                if reason.strip():
                    description += f" — {reason.strip()}"
                record_event(cursor, resignation_id, "Resigned", exit_date, description)
                connection.commit()
                load_data.clear()
                st.success(f"Recorded resignation for {row['employee_name']}.")
                st.rerun()
            except ValueError as exc:
                if connection is not None:
                    connection.rollback()
                st.warning(str(exc))
            except Error:
                if connection is not None:
                    connection.rollback()
                st.error("Resignation was not saved. Check app logs and database permissions.")
            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

# ---------- Recent events ----------
st.divider()
st.subheader("Latest HR Events")
if events.empty:
    st.info("No HR events found.")
else:
    st.dataframe(events, use_container_width=True, hide_index=True)

st.caption("Data refreshes automatically after successful changes; cached reads expire after 30 seconds.")
