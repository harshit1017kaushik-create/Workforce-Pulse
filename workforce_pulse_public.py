import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error

st.set_page_config(
    page_title="Workforce Pulse | HR Analytics",
    page_icon="👥",
    layout="wide",
)

st.title("👥 Workforce Pulse")
st.caption("Public read-only HR analytics dashboard.")
st.info("Public demo: dashboard viewing only. Employee management actions are disabled.")

# Configure these values in Streamlit Community Cloud -> App settings -> Secrets.
# Never place database credentials in source code or a public GitHub repository.
if "mysql" not in st.secrets:
    st.error("Database connection is not configured. The app owner must add MySQL settings in Streamlit Secrets.")
    st.stop()

try:
    db_host = st.secrets["mysql"]["host"]
    db_port = int(st.secrets["mysql"]["port"])
    db_user = st.secrets["mysql"]["user"]
    db_password = st.secrets["mysql"]["password"]
    db_name = st.secrets["mysql"]["database"]
except Exception:
    st.error("MySQL settings are incomplete. Check the app's Streamlit Secrets configuration.")
    st.stop()

if st.sidebar.button("Refresh dashboard", type="primary"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=30, show_spinner=False)
def load_employees(host, port, user, password, database):
    connection = mysql.connector.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        database=database,
        connection_timeout=8,
    )
    try:
        return pd.read_sql(
            """
            SELECT employee_id, employee_name, department, job_title, location,
                   joining_date, employment_status, exit_date
            FROM employees
            ORDER BY employee_id
            """,
            connection,
        )
    finally:
        connection.close()

try:
    with st.spinner("Loading dashboard data..."):
        employees = load_employees(db_host, db_port, db_user, db_password, db_name)
except Exception:
    st.error("Could not load dashboard data. The app owner should check the hosted MySQL connection and database permissions.")
    st.stop()

if employees.empty:
    st.warning("No employee records are available to display.")
    st.stop()

for col in ["joining_date", "exit_date"]:
    employees[col] = pd.to_datetime(employees[col], errors="coerce")

# ---------- Filters ----------
st.sidebar.divider()
st.sidebar.subheader("Dashboard Filters")

departments = sorted(employees["department"].dropna().astype(str).unique().tolist())
selected_departments = st.sidebar.multiselect(
    "Department",
    options=departments,
    default=departments,
)
statuses = sorted(employees["employment_status"].dropna().astype(str).unique().tolist())
selected_statuses = st.sidebar.multiselect(
    "Employment status",
    options=statuses,
    default=statuses,
)

filtered = employees[
    employees["department"].astype(str).isin(selected_departments)
    & employees["employment_status"].astype(str).isin(selected_statuses)
].copy()

total_count = len(filtered)
active_count = int((filtered["employment_status"] == "Active").sum())
resigned_count = int((filtered["employment_status"] == "Resigned").sum())
department_count = int(filtered["department"].nunique())

# ---------- KPI cards ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Employees in View", f"{total_count:,}")
k2.metric("Active Employees", f"{active_count:,}")
k3.metric("Resigned Employees", f"{resigned_count:,}")
k4.metric("Departments in View", f"{department_count:,}")

st.divider()

# ---------- Charts ----------
left, right = st.columns(2)

with left:
    st.subheader("Employees by Department")
    if filtered.empty:
        st.info("No employees match the selected filters.")
    else:
        dept_counts = (
            filtered.groupby("department", dropna=False)
            .size()
            .reset_index(name="Employees")
            .sort_values("Employees", ascending=False)
        )
        st.bar_chart(dept_counts, x="department", y="Employees", use_container_width=True)

with right:
    st.subheader("Hiring Trend by Month")
    hiring = filtered.dropna(subset=["joining_date"]).copy()
    if hiring.empty:
        st.info("No joining-date data is available for the selected filters.")
    else:
        hiring["Month"] = hiring["joining_date"].dt.to_period("M").astype(str)
        monthly_hires = (
            hiring.groupby("Month")
            .size()
            .reset_index(name="Hires")
            .sort_values("Month")
        )
        st.line_chart(monthly_hires, x="Month", y="Hires", use_container_width=True)

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("Employment Status")
    if filtered.empty:
        st.info("No employees match the selected filters.")
    else:
        status_counts = (
            filtered.groupby("employment_status")
            .size()
            .reset_index(name="Employees")
        )
        st.bar_chart(status_counts, x="employment_status", y="Employees", use_container_width=True)

with right:
    st.subheader("Employees by Location")
    if filtered.empty:
        st.info("No employees match the selected filters.")
    else:
        location_counts = (
            filtered.groupby("location", dropna=False)
            .size()
            .reset_index(name="Employees")
            .sort_values("Employees", ascending=False)
        )
        location_counts["location"] = location_counts["location"].fillna("Not specified")
        st.bar_chart(location_counts, x="location", y="Employees", use_container_width=True)

st.divider()
st.subheader("Resignations by Month")
resigned_rows = filtered[
    (filtered["employment_status"] == "Resigned")
    & filtered["exit_date"].notna()
].copy()
if resigned_rows.empty:
    st.info("No resignation records with an exit date are available for the selected filters yet.")
else:
    resigned_rows["Month"] = resigned_rows["exit_date"].dt.to_period("M").astype(str)
    monthly_resignations = (
        resigned_rows.groupby("Month")
        .size()
        .reset_index(name="Resignations")
        .sort_values("Month")
    )
    st.bar_chart(monthly_resignations, x="Month", y="Resignations", use_container_width=True)

st.divider()
st.subheader("Employee Directory")
if filtered.empty:
    st.info("No employees match the selected filters.")
else:
    public_directory = filtered[["employee_name", "department", "job_title", "location", "employment_status"]].copy()
    st.dataframe(
        public_directory.rename(columns={
            "employee_name": "Employee Name",
            "department": "Department",
            "job_title": "Job Title",
            "location": "Location",
            "employment_status": "Status",
        }),
        use_container_width=True,
        hide_index=True,
    )

st.caption("Read-only public demo. Employee management actions and HR event history are not available on this page.")
