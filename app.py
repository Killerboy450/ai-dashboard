import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# ------------------ DATABASE ------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT
)
""")
conn.commit()

# ------------------ FUNCTIONS ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    c.execute("INSERT INTO users VALUES (?, ?)", (username, hash_password(password)))
    conn.commit()

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    return c.fetchone()

# ------------------ SESSION ------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ------------------ LOGIN UI ------------------
menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Signup":
    st.subheader("Create Account")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password", type='password')

    if st.button("Signup"):
        add_user(new_user, new_pass)
        st.success("Account created! Go to login")

elif choice == "Login":
    st.subheader("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state["logged_in"] = True
            st.success(f"Welcome {username} 🎉")
        else:
            st.error("Invalid credentials")

# ------------------ PROTECT APP ------------------
if not st.session_state["logged_in"]:
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
