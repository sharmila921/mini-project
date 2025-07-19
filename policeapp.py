import streamlit as st
import pandas as pd
import pymysql
import datetime
import plotly.express as px

# Database Connection
def new_connection():
    """Establishes a new connection to the MySQL database."""
    try:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="S123@saai", # Ensure this password is correct for your setup
            database="policelog",
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        st.error(f"Connection Error: {e}")
        return None

def fetch_data(query):
    """Fetches data from the database using the given SQL query."""
    conn = new_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                if rows:
                    df = pd.DataFrame(rows)
                else:
                    df = pd.DataFrame()  # Return an empty DataFrame if no rows
                return df
        except Exception as e:
            st.error(f"Query Error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    else:
        return pd.DataFrame()

def insert_data(query):
    """Inserts data into the database using the given SQL query."""
    conn = new_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Failed to insert log: {e}")
            return False
        finally:
            conn.close()
    return False

# Streamlit UI Configuration
st.set_page_config(page_title="🚓 SecureCheck: Police Post Dashboard", layout="wide")
st.title("🚓 SecureCheck: Police Post Dashboard")

# Sidebar Menu for Navigation
menu = st.sidebar.selectbox(
    "Navigate",
    ["Home", "View Logs", "Run Query", "Add Logs"]
)

# --- Home Page ---
if menu == "Home":
    st.subheader("Welcome to SecureCheck ✅")
    st.write("""
    This dashboard provides a comprehensive overview and management tool for police traffic stop logs.
    You can:
    - **View Logs:** Filter and inspect detailed records of traffic stops.
    - **Run Query:** Gain insights through various statistical analyses and visualizations of stop data.
    - **Add Logs:** Easily input new traffic stop information into the system.
    """)
    st.image("https://placehold.co/600x300/ADD8E6/000000?text=Police+Dashboard+Image", caption="SecureCheck Dashboard Overview")


# --- View Logs Page ---
elif menu == "View Logs":
    st.subheader("📋 View Vehicle Logs with Filters")

    st.write("Use the filters below to narrow down logs:")

    # Input fields for filtering
    vehicle_input = st.text_input("🔍 Search by Vehicle Number")
    violation_input = st.text_input("🔍 Search by Violation")
    country_input = st.text_input("🌍 Search by Country")

    # Base query to fetch all traffic stops
    query = "SELECT * FROM traffic_stops WHERE 1=1"

    # Dynamically add filters to the query based on user input
    if vehicle_input:
        query += f" AND vehicle_number LIKE '%{vehicle_input}%'"
    if violation_input:
        query += f" AND violation LIKE '%{violation_input}%'"
    if country_input:
        query += f" AND country_name LIKE '%{country_input}%'"

    # Fetch data based on the constructed query
    df = fetch_data(query)

    if not df.empty:
        # Format 'stop_time' for better display if it's a datetime object
        if 'stop_time' in df.columns:
            # Assuming stop_time might be a datetime.timedelta or datetime.datetime
            # Convert to string to ensure consistent display
            df['stop_time'] = df['stop_time'].apply(lambda x: str(x).split()[-1] if pd.notnull(x) and ' ' in str(x) else str(x))

        st.success(f"✅ Showing {len(df)} matching logs")
        st.dataframe(df)
    else:
        st.warning("⚠️ No matching logs found. Try adjusting your filters.")


# --- Data Analytics Page ---
elif menu == "Run Query":
    st.subheader("📊 Data Analytics & Visuals")

    # Dropdown to select different analysis options
    analysis_option = st.selectbox(
        "Choose an analysis to run:",
        [
            "Violations & Gender & Drug Overview",
            "Top 10 Vehicles in Drug-Related Stops",
            "Most Frequently Searched Vehicles",
            "Driver Age Group with Highest Arrest Rate",
            "Gender Distribution by Country",
            "Race & Gender with Highest Search Rate",
            "Time of Day with Most Stops",
            "Average Stop Duration by Violation",
            "Are Night Stops More Likely to Lead to Arrests?",
            "Violations Associated with Searches or Arrests",
            "Most Common Violations for Drivers Under 25",
            "Violation Rarely Resulting in Search or Arrest",
            "Countries with Highest Drug-Related Stop Rates",
            "Arrest Rate by Country & Violation",
            "Country with Most Searches Conducted",
            "Yearly Breakdown of Stops & Arrests by Country",
            "Driver Violation Trends by Age & Race",
            "Stops by Year, Month, Hour",
            "Violations with High Search & Arrest Rates",
            "Driver Demographics by Country",
            "Top 5 Violations with Highest Arrest Rates"
        ]
    )

    # Execute query and display results based on selected analysis option
    if analysis_option == "Violations & Gender & Drug Overview":
        query = "SELECT * FROM traffic_stops"
        df = fetch_data(query)

        if not df.empty:
            st.write("## Violation Counts")
            violation_counts = df['violation'].value_counts().reset_index()
            violation_counts.columns = ['violation', 'count']
            fig = px.bar(violation_counts, x='violation', y='count',
                         title="Distribution of Violation Types", color='violation')
            st.plotly_chart(fig, use_container_width=True)

            st.write("## Driver Gender Distribution")
            gender_counts = df['driver_gender'].value_counts().reset_index()
            gender_counts.columns = ['gender', 'count']
            fig2 = px.pie(gender_counts, names='gender', values='count',
                          title="Driver Gender Distribution")
            st.plotly_chart(fig2, use_container_width=True)

            st.write("## Drug-Related Stops Overview")
            drug_counts = df.groupby(['country_name', 'drugs_related_stop']).size().reset_index(name='count')
            fig3 = px.bar(
                drug_counts,
                x='country_name',
                y='count',
                color='drugs_related_stop',
                barmode='group',
                labels={'count': 'Number of Stops', 'country_name': 'Country', 'drugs_related_stop': 'Drugs Related (True/False)'},
                title="Drug-Related vs Non-Drug-Related Stops by Country"
            )
            st.plotly_chart(fig3, use_container_width=True)

        else:
            st.warning("No data available for this analysis.")

    # Other analysis options (SQL queries)
    else:
        query = "" # Initialize query string

        if analysis_option == "Top 10 Vehicles in Drug-Related Stops":
            query = """
                SELECT vehicle_number, COUNT(*) AS stop_count
                FROM traffic_stops
                WHERE drugs_related_stop = TRUE
                GROUP BY vehicle_number
                ORDER BY stop_count DESC
                LIMIT 10;
            """
        elif analysis_option == "Most Frequently Searched Vehicles":
            query = """
                SELECT vehicle_number, COUNT(*) AS search_count
                FROM traffic_stops
                WHERE search_type IS NOT NULL AND search_type != 'No Search' AND search_type != ''
                GROUP BY vehicle_number
                ORDER BY search_count DESC
                LIMIT 10;
            """
        elif analysis_option == "Driver Age Group with Highest Arrest Rate":
            query = """
                SELECT
                    CASE
                        WHEN driver_age < 18 THEN 'Under 18'
                        WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                        WHEN driver_age BETWEEN 26 AND 40 THEN '26-40'
                        WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
                        ELSE '60+'
                    END AS age_group,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
                    ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate_pct
                FROM traffic_stops
                WHERE driver_age IS NOT NULL
                GROUP BY age_group
                ORDER BY arrest_rate_pct DESC;
            """
        elif analysis_option == "Gender Distribution by Country":
            query = """
                SELECT country_name, driver_gender, COUNT(*) AS stop_count
                FROM traffic_stops
                WHERE driver_gender IS NOT NULL AND country_name IS NOT NULL
                GROUP BY country_name, driver_gender
                ORDER BY country_name, stop_count DESC;
            """
        elif analysis_option == "Race & Gender with Highest Search Rate":
            query = """
                SELECT driver_race, driver_gender, COUNT(*) AS search_count,
                       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM traffic_stops WHERE search_type IS NOT NULL AND search_type != 'No Search' AND search_type != ''), 2) AS search_rate_pct
                FROM traffic_stops
                WHERE search_type IS NOT NULL AND search_type != 'No Search' AND search_type != ''
                AND driver_race IS NOT NULL AND driver_gender IS NOT NULL
                GROUP BY driver_race, driver_gender
                ORDER BY search_rate_pct DESC
                LIMIT 5; -- Showing top 5 for better overview
            """
        elif analysis_option == "Time of Day with Most Stops":
            query = """
                SELECT HOUR(stop_time) AS hour_of_day, COUNT(*) AS stop_count
                FROM traffic_stops
                WHERE stop_time IS NOT NULL
                GROUP BY hour_of_day
                ORDER BY stop_count DESC;
            """
        elif analysis_option == "Average Stop Duration by Violation":
            query = """
                SELECT violation, stop_duration, COUNT(*) AS count
                FROM traffic_stops
                WHERE violation IS NOT NULL AND stop_duration IS NOT NULL
                GROUP BY violation, stop_duration
                ORDER BY violation, count DESC;
            """
        elif analysis_option == "Are Night Stops More Likely to Lead to Arrests?":
            query = """
                SELECT
                    CASE
                        WHEN HOUR(stop_time) >= 20 OR HOUR(stop_time) < 6 THEN 'Night'
                        ELSE 'Day'
                    END AS time_period,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
                    ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS arrest_rate_pct
                FROM traffic_stops
                WHERE stop_time IS NOT NULL
                GROUP BY time_period
                ORDER BY arrest_rate_pct DESC;
            """
        elif analysis_option == "Violations Associated with Searches or Arrests":
            query = """
                SELECT violation, COUNT(*) AS count
                FROM traffic_stops
                WHERE (search_type IS NOT NULL AND search_type != '' AND search_type != 'No Search') OR stop_outcome = 'Arrest'
                AND violation IS NOT NULL
                GROUP BY violation
                ORDER BY count DESC;
            """
        elif analysis_option == "Most Common Violations for Drivers Under 25":
            query = """
                SELECT violation, COUNT(*) AS count
                FROM traffic_stops
                WHERE driver_age < 25 AND violation IS NOT NULL
                GROUP BY violation
                ORDER BY count DESC
                LIMIT 10;
            """
        elif analysis_option == "Violation Rarely Resulting in Search or Arrest":
            query = """
                SELECT violation,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN (search_type IS NOT NULL AND search_type != '' AND search_type != 'No Search') OR stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS searched_or_arrested,
                    ROUND(SUM(CASE WHEN (search_type IS NOT NULL AND search_type != '' AND search_type != 'No Search') OR stop_outcome = 'Arrest' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS pct_leading_to_action
                FROM traffic_stops
                WHERE violation IS NOT NULL
                GROUP BY violation
                ORDER BY pct_leading_to_action ASC
                LIMIT 5; -- Showing top 5 lowest rates
            """
        elif analysis_option == "Countries with Highest Drug-Related Stop Rates":
            query = """
                SELECT country_name,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_stops,
                    ROUND(SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS drug_stop_rate_pct
                FROM traffic_stops
                WHERE country_name IS NOT NULL
                GROUP BY country_name
                ORDER BY drug_stop_rate_pct DESC;
            """
        elif analysis_option == "Arrest Rate by Country & Violation":
            query = """
                SELECT country_name, violation,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
                    ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS arrest_rate_pct
                FROM traffic_stops
                WHERE country_name IS NOT NULL AND violation IS NOT NULL
                GROUP BY country_name, violation
                ORDER BY arrest_rate_pct DESC;
            """
        elif analysis_option == "Country with Most Searches Conducted":
            query = """
                SELECT country_name, COUNT(*) AS search_count
                FROM traffic_stops
                WHERE search_type IS NOT NULL AND search_type != '' AND search_type != 'No Search'
                AND country_name IS NOT NULL
                GROUP BY country_name
                ORDER BY search_count DESC
                LIMIT 1;
            """
        elif analysis_option == "Yearly Breakdown of Stops & Arrests by Country":
            query = """
                SELECT YEAR(stop_date) AS year, country_name,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
                    ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS arrest_rate_pct
                FROM traffic_stops
                WHERE stop_date IS NOT NULL AND country_name IS NOT NULL
                GROUP BY year, country_name
                ORDER BY year, country_name;
            """
        elif analysis_option == "Driver Violation Trends by Age & Race":
            query = """
                SELECT driver_race,
                    CASE
                        WHEN driver_age < 18 THEN 'Under 18'
                        WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                        WHEN driver_age BETWEEN 26 AND 40 THEN '26-40'
                        WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
                        ELSE '60+'
                    END AS age_group,
                    violation,
                    COUNT(*) AS stop_count
                FROM traffic_stops
                WHERE driver_race IS NOT NULL AND driver_age IS NOT NULL AND violation IS NOT NULL
                GROUP BY driver_race, age_group, violation
                ORDER BY stop_count DESC;
            """
        elif analysis_option == "Stops by Year, Month, Hour":
            query = """
                SELECT
                    YEAR(stop_date) AS year,
                    MONTH(stop_date) AS month,
                    HOUR(stop_time) AS hour,
                    COUNT(*) AS stop_count
                FROM traffic_stops
                WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL
                GROUP BY year, month, hour
                ORDER BY year, month, hour;
            """
        elif analysis_option == "Violations with High Search & Arrest Rates":
            query = """
                SELECT violation,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN search_type IS NOT NULL AND search_type != '' AND search_type != 'No Search' THEN 1 ELSE 0 END) AS searches,
                    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
                    ROUND(SUM(CASE WHEN search_type IS NOT NULL AND search_type != '' AND search_type != 'No Search' THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS search_rate_pct,
                    ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS arrest_rate_pct
                FROM traffic_stops
                WHERE violation IS NOT NULL
                GROUP BY violation
                ORDER BY arrest_rate_pct DESC, search_rate_pct DESC;
            """
        elif analysis_option == "Driver Demographics by Country":
            query = """
                SELECT country_name, driver_gender, driver_race,
                    CASE
                        WHEN driver_age < 18 THEN 'Under 18'
                        WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                        WHEN driver_age BETWEEN 26 AND 40 THEN '26-40'
                        WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
                        ELSE '60+'
                    END AS age_group,
                    COUNT(*) AS stop_count
                FROM traffic_stops
                WHERE country_name IS NOT NULL AND driver_gender IS NOT NULL AND driver_race IS NOT NULL AND driver_age IS NOT NULL
                GROUP BY country_name, driver_gender, driver_race, age_group
                ORDER BY country_name, driver_gender, driver_race, age_group;
            """
        elif analysis_option == "Top 5 Violations with Highest Arrest Rates":
            query = """
                SELECT violation,
                    COUNT(*) AS total_stops,
                    SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END) AS arrests,
                    ROUND(SUM(CASE WHEN stop_outcome = 'Arrest' THEN 1 ELSE 0 END)/COUNT(*) * 100, 2) AS arrest_rate_pct
                FROM traffic_stops
                WHERE violation IS NOT NULL
                GROUP BY violation
                ORDER BY arrest_rate_pct DESC
                LIMIT 5;
            """
        
        # Fetch and display data for the selected analysis
        df = fetch_data(query)
        if not df.empty:
            st.dataframe(df)
        else:
            st.warning("No data found for this analysis query.")


# --- Add Logs Page ---
elif menu == "Add Logs":
    st.subheader("➕ Add New Traffic Stop Log")

    # Input fields for the new log entry
    vehicle_number = st.text_input("🚗 Vehicle Number", key="add_vehicle_number")
    driver_age = st.number_input("👤 Driver Age", min_value=16, max_value=100, value=27, key="add_driver_age")
    driver_gender = st.selectbox("🚻 Driver Gender", ["M", "F", "Other"], key="add_driver_gender")
    driver_race = st.text_input("🌈 Driver Race", key="add_driver_race")
    violation = st.text_input("⚠️ Violation", key="add_violation")
    country_name = st.text_input("🌍 Country Name", key="add_country_name")
    stop_date = st.date_input("📅 Stop Date", value=datetime.date.today(), key="add_stop_date")
    stop_time = st.time_input("⏰ Stop Time", value=datetime.time(14, 30), key="add_stop_time")
    search_type = st.text_input("🔎 Search Type (Type 'No Search' if there was no search)", key="add_search_type")
    stop_outcome = st.selectbox("✅ Stop Outcome", ["Citation", "Warning", "Arrest"], key="add_stop_outcome")
    stop_duration = st.selectbox(
        "⏱️ Stop Duration",
        ["0-5 Min", "6-15 Min", "16-30 Min", "30+ Min"],
        key="add_stop_duration"
    )
    drugs_related_stop = st.checkbox("💊 Drugs Related Stop?", key="add_drugs_related_stop")

    if st.button("➕ Add Log", key="add_log_button"):
        # Format stop_time for SQL insertion
        formatted_stop_time = stop_time.strftime("%H:%M:%S")

        # Handle search_type: if empty, insert 'No Search', otherwise insert the provided value
        # Ensure proper SQL string literal formatting
        search_type_for_sql = f"'{search_type.strip()}'" if search_type.strip() else "'No Search'"

        # Construct the SQL INSERT query
        query = f"""
            INSERT INTO traffic_stops (
                driver_age,
                driver_gender,
                driver_race,
                violation,
                stop_time,
                stop_date,
                search_type,
                stop_outcome,
                stop_duration,
                drugs_related_stop,
                country_name,
                vehicle_number
            )
            VALUES (
                {driver_age},
                '{driver_gender}',
                '{driver_race}',
                '{violation}',
                '{formatted_stop_time}',
                '{stop_date}',
                {search_type_for_sql},
                '{stop_outcome}',
                '{stop_duration}',
                {1 if drugs_related_stop else 0},
                '{country_name}',
                '{vehicle_number}'
            );
        """

        # Attempt to insert data and provide feedback
        if insert_data(query):
            st.success("✅ Log added successfully!")

            # Build a readable prediction statement for the user
            readable_time = stop_time.strftime("%I:%M %p").lstrip("0")
            search_statement = "A search was conducted" if search_type.strip() else "No search was conducted"
            drug_statement = "drug-related." if drugs_related_stop else "not drug-related."

            prediction_statement = (
                f"🚗 A {driver_age}-year-old "
                f"{'male' if driver_gender == 'M' else 'female'} {driver_race} driver "
                f"was stopped for **{violation}** at **{readable_time}** in **{country_name}**. "
                f"{search_statement}, and they received a **{stop_outcome.lower()}**. "
                f"The stop lasted **{stop_duration}** and was **{drug_statement}**"
            )
            st.info(prediction_statement)
        else:
            st.error("❌ Failed to add log. Please check the input and database connection.")

