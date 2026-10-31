
import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================
# 1. PAGE CONFIGURATION
# =====================================

st.set_page_config(
    page_title="AirScope - Air Quality Explorer",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 AirScope")
st.subheader("India's Air Quality Explorer")

st.write(
    "Explore air pollution levels, compare Indian cities "
    "and understand air quality through data."
)

st.caption(
    "Note: The included dataset is illustrative practice data, "
    "not official or live CPCB monitoring data."
)

# =====================================
# 2. LOAD DATASET
# =====================================

st.sidebar.title("Dataset")

uploaded_file = st.sidebar.file_uploader(
    "Upload your CSV file",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        raw_data = pd.read_csv(uploaded_file)
    else:
        raw_data = pd.read_csv("air_quality_india.csv")
except Exception as error:
    st.error(f"Unable to load dataset: {error}")
    st.stop()

required_columns = ["City", "Date", "AQI"]

if not all(col in raw_data.columns for col in required_columns):
    st.error("Dataset must contain City, Date and AQI columns.")
    st.stop()

# =====================================
# 3. DATASET PREVIEW
# =====================================

st.header("1. Dataset Preview")

st.write("Our original air quality dataset:")

st.dataframe(
    raw_data.head(15),
    use_container_width=True
)

# =====================================
# 4. DATA INFORMATION
# =====================================

st.header("2. Data Information")

col1, col2, col3 = st.columns(3)

col1.metric("Total Rows", raw_data.shape[0])
col2.metric("Total Columns", raw_data.shape[1])
col3.metric(
    "Missing Values",
    int(raw_data.isnull().sum().sum())
)

with st.expander("View Data Types and Missing Values"):

    info = pd.DataFrame({
        "Column": raw_data.columns,
        "Data Type": raw_data.dtypes.astype(str).values,
        "Missing Values": raw_data.isnull().sum().values
    })

    st.dataframe(info, use_container_width=True)

with st.expander("Statistical Summary"):

    st.dataframe(
        raw_data.describe(include="all").transpose(),
        use_container_width=True
    )

# =====================================
# 5. DATA CLEANING
# =====================================

st.header("3. Data Cleaning")

clean_data = raw_data.copy()

# Remove duplicate records

initial_rows = len(clean_data)

clean_data = clean_data.drop_duplicates()

duplicates_removed = initial_rows - len(clean_data)

# Convert date column

clean_data["Date"] = pd.to_datetime(
    clean_data["Date"],
    errors="coerce"
)

# Convert numerical columns

numeric_columns = [
    "AQI", "PM2_5", "PM10",
    "NO2", "SO2", "CO", "O3"
]

for column in numeric_columns:

    if column in clean_data.columns:

        clean_data[column] = pd.to_numeric(
            clean_data[column],
            errors="coerce"
        )

# Remove rows missing essential information

clean_data = clean_data.dropna(
    subset=["City", "Date", "AQI"]
)

# Fill missing pollutant values using median

for column in numeric_columns:

    if column in clean_data.columns and column != "AQI":

        clean_data[column] = clean_data[column].fillna(
            clean_data[column].median()
        )

# Create AQI categories

def aqi_category(aqi):

    if aqi <= 50:
        return "Good"

    elif aqi <= 100:
        return "Satisfactory"

    elif aqi <= 200:
        return "Moderate"

    elif aqi <= 300:
        return "Poor"

    elif aqi <= 400:
        return "Very Poor"

    else:
        return "Severe"


clean_data["AQI_Category"] = clean_data["AQI"].apply(
    aqi_category
)

# Display cleaning results

c1, c2, c3 = st.columns(3)

c1.metric("Duplicates Removed", duplicates_removed)
c2.metric("Clean Records", len(clean_data))
c3.metric(
    "Missing Values Remaining",
    int(clean_data.isnull().sum().sum())
)

st.success("Data cleaning completed successfully!")

with st.expander("View Cleaned Dataset"):

    st.dataframe(
        clean_data,
        use_container_width=True
    )

# Download cleaned dataset

csv_file = clean_data.to_csv(index=False).encode("utf-8")

st.download_button(
    "Download Cleaned Dataset",
    data=csv_file,
    file_name="airscope_cleaned_data.csv",
    mime="text/csv"
)

# =====================================
# 6. DATA FILTERS
# =====================================

st.header("4. Data Visualisation")

st.sidebar.header("Explore Data")

cities = sorted(clean_data["City"].unique())

selected_cities = st.sidebar.multiselect(
    "Select Cities",
    cities,
    default=cities
)

min_date = clean_data["Date"].min().date()
max_date = clean_data["Date"].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered_data = clean_data[
    clean_data["City"].isin(selected_cities)
].copy()

if isinstance(date_range, tuple) and len(date_range) == 2:

    start_date, end_date = date_range

    filtered_data = filtered_data[
        (filtered_data["Date"].dt.date >= start_date) &
        (filtered_data["Date"].dt.date <= end_date)
    ]

if filtered_data.empty:

    st.warning("No data available for the selected filters.")
    st.stop()

# =====================================
# 7. AQI SUMMARY CARDS
# =====================================

average_aqi = filtered_data["AQI"].mean()

highest_aqi = filtered_data["AQI"].max()

lowest_aqi = filtered_data["AQI"].min()

k1, k2, k3 = st.columns(3)

k1.metric("Average AQI", f"{average_aqi:.1f}")

k2.metric("Highest AQI", f"{highest_aqi:.0f}")

k3.metric("Lowest AQI", f"{lowest_aqi:.0f}")

# =====================================
# 8. CITY-WISE AQI COMPARISON
# =====================================

st.subheader("City-wise AQI Comparison")

city_average = (
    filtered_data.groupby("City")["AQI"]
    .mean()
    .reset_index()
    .sort_values("AQI", ascending=False)
)

fig1 = px.bar(
    city_average,
    x="City",
    y="AQI",
    color="AQI",
    title="Average AQI Across Cities",
    labels={"AQI": "Average AQI"}
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

# =====================================
# 9. AQI TREND ANALYSIS
# =====================================

st.subheader("AQI Trend Over Time")

trend_data = (
    filtered_data.groupby("Date")["AQI"]
    .mean()
    .reset_index()
)

fig2 = px.line(
    trend_data,
    x="Date",
    y="AQI",
    markers=True,
    title="Air Quality Trend"
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# =====================================
# 10. AQI CATEGORY DISTRIBUTION
# =====================================

st.subheader("AQI Category Distribution")

category_data = (
    filtered_data["AQI_Category"]
    .value_counts()
    .reset_index()
)

category_data.columns = ["Category", "Count"]

fig3 = px.pie(
    category_data,
    names="Category",
    values="Count",
    hole=0.4,
    title="Distribution of Air Quality Categories"
)

st.plotly_chart(
    fig3,
    use_container_width=True
)

# =====================================
# 11. POLLUTANT ANALYSIS
# =====================================

st.subheader("Pollutant Level Analysis")

pollutants = [
    col for col in
    ["PM2_5", "PM10", "NO2", "SO2", "CO", "O3"]
    if col in filtered_data.columns
]

if pollutants:

    pollutant_average = (
        filtered_data[pollutants]
        .mean()
        .reset_index()
    )

    pollutant_average.columns = [
        "Pollutant",
        "Average Value"
    ]

    fig4 = px.bar(
        pollutant_average,
        x="Pollutant",
        y="Average Value",
        title="Average Pollutant Levels"
    )

    st.plotly_chart(
        fig4,
        use_container_width=True
    )

# =====================================
# 12. AUTOMATIC INSIGHT
# =====================================

st.subheader("Air Quality Insight")

worst_city = city_average.iloc[0]["City"]

worst_value = city_average.iloc[0]["AQI"]

st.info(
    f"{worst_city} has the highest average AQI "
    f"({worst_value:.1f}) among the selected cities "
    "for the chosen date range."
)

# =====================================
# 13. FINAL DATA TABLE
# =====================================

st.subheader("Explore Filtered Records")

st.dataframe(
    filtered_data,
    use_container_width=True
)

st.divider()

st.caption(
    "AirScope | Built using Python, Pandas, "
    "Streamlit and Plotly"
)

