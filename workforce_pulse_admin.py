
import streamlit as st
import mysql.connector
from mysql.connector import Error

st.set_page_config(
    page_title="Workforce Pulse | Admin",
    page_icon="🔐",
    layout="wide"
)

st.title("🔐 Workforce Pulse — Admin")
st.caption("Secure employee management portal")

# --------------------------------------------------
# ADMIN AUTHENTICATION
# Add admin credentials to Streamlit Secrets.
# Never use database credentials as admin credentials.
# --------------------------------------------------

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

if not st.session_state.admin_authenticated:
    st.subheader("Admin Login")

    with st.form("admin_login"):
        username = st.text_input("Admin username")
        password = st.text_input(
            "Admin password",
            type="password"
        )
        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            admin_secrets = st.secrets["admin"]

            if (
                username == admin_secrets["username"]
                and password == admin_secrets["password"]
            ):
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Invalid admin username or password.")

        except (KeyError, FileNotFoundError):
            st.error(
                "Admin credentials are not configured "
                "in Streamlit Secrets."
            )

    st.stop()

# --------------------------------------------------
# DATABASE CONNECTION — READ ONLY FOR INITIAL TEST
# --------------------------------------------------

st.success("Admin login successful.")

if st.button("Log out"):
    st.session_state.admin_authenticated = False
    st.rerun()

def get_connection():
    config = st.secrets["mysql"]

    return mysql.connector.connect(
        host=config["host"],
        port=int(config["port"]),
        user=config["user"],
        password=config["password"],
        database=config["database"],
        connection_timeout=10
    )

try:
    connection = get_connection()

    cursor = connection.cursor()

    # Read-only verification: no employee data is changed.
    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM employee_events")
    event_count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    col1, col2 = st.columns(2)

    col1.metric("Total Employees", employee_count)
    col2.metric("Total HR Events", event_count)

    st.success("Aiven database connection successful.")
    st.info(
        "Initial connection test only. "
        "Employee editing is not enabled in this version."
    )

except (Error, KeyError) as error:
    st.error(
        "Could not connect to the database. "
        "Check the app logs and database configuration."
    )
    # Do not display connection details or credentials.
