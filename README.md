# Workforce Pulse — HR Analytics Dashboard

**A live, read-only HR analytics dashboard built with Python, Streamlit, and MySQL.**

## Overview

Workforce Pulse is an HR analytics project that presents employee information and workforce metrics through an interactive web dashboard. It connects to a MySQL database hosted on Aiven and allows users to explore workforce data through KPIs, charts, and visual summaries.

## Live Demo

[[Open Workforce Pulse](https://workforce-pulse-jf7mdeifddaoudctxawezn.streamlit.app)
](https://workforce-pulse-jf7mdeifddauodctxawezn.streamlit.app/)
## Features

- **HR analytics dashboard:** View employee-related information and workforce metrics.
- **KPI cards:** Review key workforce indicators.
- **Data visualizations:** Explore workforce data using charts and graphs.
- **MySQL integration:** Retrieve data from a hosted MySQL database.
- **Cloud deployment:** Access the dashboard through Streamlit Community Cloud.
- **Read-only public access:** Dashboard visitors can view analytics without using employee-management actions.

## Technology Stack

- **Programming language:** Python
- **Dashboard framework:** Streamlit
- **Data manipulation:** Pandas
- **Database:** MySQL
- **Database hosting:** Aiven
- **Deployment:** Streamlit Community Cloud
- **Version control:** Git and GitHub

## Architecture

MySQL Database (Aiven) → Python and MySQL Connector → Streamlit Dashboard → Public Viewer

## Project Structure

```text
Workforce_Pulse/
├── workforce_pulse_public.py
├── requirements.txt
└── README.md
```

## Run Locally

1. Clone this repository.
2. Install the dependencies.
3. Configure the database credentials securely using Streamlit Secrets.
4. Start the application.

```bash
git clone https://github.com/harshit1017kaushik-create/Workforce_Pulse.git
cd Workforce_Pulse
pip install -r requirements.txt
streamlit run workforce_pulse_public.py
```

Configure the required `[mysql]` settings in `.streamlit/secrets.toml` before running the app locally. Never commit database passwords or other secrets to GitHub.

## Learning Outcomes

- Connecting a Python application to a MySQL database.
- Building a dashboard with Streamlit.
- Presenting employee data through KPIs and visualizations.
- Deploying a Python application to the cloud.
- Separating public dashboard access from employee-management actions.

## Author

**Harshit Kaushik**

Computer Science and Engineering | Data Analytics Projects
