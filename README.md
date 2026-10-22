# Workforce Pulse — HR Analytics Dashboard

Workforce Pulse is a Python and Streamlit HR analytics dashboard connected to a MySQL database. It helps users explore workforce information through key performance indicators (KPIs), charts, filters, and an employee directory.

## Features

- Workforce KPIs, including employee counts and employment-status summaries
- Employee analysis by department and location
- Hiring and resignation trend visualizations
- Interactive dashboard filters
- Employee directory with selected employee details
- Read-only public dashboard: visitors cannot add employees, change departments, or record resignations

## Technology Stack

- Python
- Streamlit
- Pandas
- MySQL
- mysql-connector-python

## Project Structure

```text
workforce-pulse/
├── workforce_pulse_public.py
├── requirements.txt
└── README.md
```

## Running Locally

1. Install Python.
2. Clone this repository and open its folder.
3. Create and activate a virtual environment (recommended).
4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Configure the database connection using environment variables or Streamlit secrets. Do not put database passwords directly in source code or commit them to GitHub.
6. Start the app:

   ```bash
   streamlit run workforce_pulse_public.py
   ```

The dashboard requires a reachable MySQL database with the expected `employees` table. If the app also queries event data, the database must contain the expected `employee_events` table. A database running on your own computer (`localhost`) is not automatically accessible to a cloud-hosted app.

## Deployment

This repository can be deployed using Streamlit Community Cloud or another compatible hosting platform.

Before deployment:

- Configure the database connection securely in the hosting platform's secrets/settings.
- Use a hosted MySQL database that the app can securely reach.
- Confirm the app uses read-only database permissions where possible.
- Use fictional or appropriately anonymized employee data for a public portfolio demo.
- Review the employee directory and remove any information that should not be public.
- Never commit passwords, API keys, database dumps, or real employee records to a public repository.

## Access and Data Safety

This public version is intended for viewing and exploration only. It does not provide public forms for hiring, department changes, or resignation records. The database credentials must be kept private, and the database account used by the public dashboard should have only the permissions it needs to read dashboard data.

## Project Status

Deployment and database connectivity must be configured and tested for the target hosting environment. The README describes the intended setup; it does not claim that the hosted app is already live.

## Author

Harshit Kaushik

GitHub: https://github.com/harshit1017kaushik-create
