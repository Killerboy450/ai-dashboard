import streamlit as st
import pandas as pd


# Simple password protection
PASSWORD = "H@_12"

password = st.text_input("Enter Password", type="password")

if password != PASSWORD:
    st.warning("Enter correct password to access dashboard 🔒")
    st.stop()
st.set_page_config(page_title="InsightAI Dashboard", layout="wide")

# Header
st.markdown("## 🚀 InsightAI Dashboard")
st.caption("Upload your data and get instant insights")

# Upload
file = st.file_uploader("📂 Upload CSV or Excel", type=["csv", "xlsx"])

if file:
    try:
        # Read file
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        st.success("File uploaded successfully ✅")

        # Clean column names
        df.columns = df.columns.str.strip()

        # Detect columns
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(exclude=['number']).columns.tolist()

        if not num_cols:
            st.error("No numeric columns found ❌")
            st.stop()

        # Sidebar
        st.sidebar.header("⚙️ Controls")

        category = st.sidebar.selectbox("Category", cat_cols if cat_cols else df.columns)
        value = st.sidebar.selectbox("Value", num_cols)

        chart_type = st.sidebar.selectbox("Chart", ["Bar", "Line", "Area"])

        # Filter
        if category in df.columns:
            options = df[category].dropna().unique()
            selected = st.sidebar.multiselect("Filter", options, default=options)
            df = df[df[category].isin(selected)]

        # KPIs
        total = df[value].sum()
        avg = df[value].mean()
        max_val = df[value].max()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", round(total, 2))
        col2.metric("Average", round(avg, 2))
        col3.metric("Max Value", round(max_val, 2))

        # Group data
        grouped = df.groupby(category)[value].sum().sort_values(ascending=False)

        # Charts
        st.subheader("📊 Visualization")

        if chart_type == "Bar":
            st.bar_chart(grouped)
        elif chart_type == "Line":
            st.line_chart(grouped)
        else:
            st.area_chart(grouped)

        # Data
        st.subheader("📄 Data Table")
        st.dataframe(df)

        # Smart Insights
        st.subheader("🧠 AI Insights")

        top = grouped.idxmax()
        bottom = grouped.idxmin()

        insights = f"""
📌 Top Category: {top}  
📉 Lowest Category: {bottom}  

📊 Total {value}: {round(total,2)}  
📈 Average {value}: {round(avg,2)}  

💡 Suggestions:
- Focus on {top} for better returns
- Improve performance in {bottom}
- Optimize allocation based on trends
"""

        st.success(insights)

        # Download
        st.subheader("📥 Export")

        st.download_button(
            "Download Clean Data",
            df.to_csv(index=False),
            "clean_data.csv",
            "text/csv"
        )

        st.download_button(
            "Download Insights Report",
            insights,
            "report.txt",
            "text/plain"
        )

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Upload a dataset to begin 🚀")
