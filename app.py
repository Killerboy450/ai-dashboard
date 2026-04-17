import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

# ------------------ CONFIG ------------------
st.set_page_config(page_title="InsightAI Dashboard", layout="wide")

# ------------------ DATABASE ------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT
)
""")

# User data table
c.execute("""
CREATE TABLE IF NOT EXISTS user_data (
    username TEXT,
    filename TEXT,
    data TEXT
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

def save_user_data(username, df, filename):
    data_json = df.to_json()
    c.execute("INSERT INTO user_data VALUES (?, ?, ?)", (username, filename, data_json))
    conn.commit()

def get_user_files(username):
    c.execute("SELECT filename, data FROM user_data WHERE username=?", (username,))
    return c.fetchall()

def generate_pdf(text):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    for line in text.split("\n"):
        story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ------------------ SESSION ------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ------------------ LOGIN / SIGNUP ------------------
menu = ["Login", "Signup"]
choice = st.sidebar.selectbox("Menu", menu)

if not st.session_state["logged_in"]:

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
                st.session_state["user"] = username
                st.success(f"Welcome {username} 🎉")
                st.rerun()
            else:
                st.error("Invalid credentials")

# ------------------ DASHBOARD ------------------
if st.session_state["logged_in"]:

    st.sidebar.success(f"Logged in as {st.session_state['user']}")

    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.markdown("## 🚀 InsightAI Dashboard")
    st.caption("Upload your data and get instant insights")

    # Show saved files
    st.subheader("📁 Your Saved Files")
    files = get_user_files(st.session_state["user"])

    if files:
        for fname, _ in files:
            st.write(f"📄 {fname}")
    else:
        st.write("No saved files yet")

    # Upload
    file = st.file_uploader("📂 Upload CSV or Excel", type=["csv", "xlsx"])

    if file:
        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            st.success("File uploaded successfully ✅")

            df.columns = df.columns.str.strip()

            # Save data
            save_user_data(st.session_state["user"], df, file.name)

            num_cols = df.select_dtypes(include=['number']).columns.tolist()
            cat_cols = df.select_dtypes(exclude=['number']).columns.tolist()

            if not num_cols:
                st.error("No numeric columns found ❌")
                st.stop()

            st.sidebar.header("⚙️ Controls")

            category = st.sidebar.selectbox("Category", cat_cols if cat_cols else df.columns)
            value = st.sidebar.selectbox("Value", num_cols)
            chart_type = st.sidebar.selectbox("Chart", ["Bar", "Line", "Area", "Pie"])

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
            col3.metric("Max", round(max_val, 2))

            grouped = df.groupby(category)[value].sum()

            st.subheader("📊 Visualization")

            if chart_type == "Bar":
                st.bar_chart(grouped)
            elif chart_type == "Line":
                st.line_chart(grouped)
            elif chart_type == "Area":
                st.area_chart(grouped)
            else:
                st.pyplot(grouped.plot.pie(autopct='%1.1f%%').figure)

            st.subheader("📄 Data")
            st.dataframe(df)

            # Insights
            st.subheader("🧠 Insights")

            top = grouped.idxmax()
            bottom = grouped.idxmin()

            insights = f"""
Top Category: {top}
Lowest Category: {bottom}

Total: {round(total,2)}
Average: {round(avg,2)}

Focus on {top} and improve {bottom}.
"""

            st.success(insights)

            # Downloads
            st.subheader("📥 Download")

            st.download_button(
                "Download CSV",
                df.to_csv(index=False),
                "data.csv",
                "text/csv"
            )

            pdf = generate_pdf(insights)

            st.download_button(
                "Download PDF Report",
                pdf,
                "report.pdf",
                "application/pdf"
            )

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.info("Upload a dataset to begin 🚀")

else:
    st.stop()
