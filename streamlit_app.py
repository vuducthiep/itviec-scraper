import json
import sqlite3

import pandas as pd
import streamlit as st


DB_PATH = "itviec.db"


@st.cache_data
def load_jobs() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            """
            SELECT
              url, title, level, company, salary, working_mode, location, posted_time,
              label, skills_json, job_description, requirements, benefits
            FROM jobs
            ORDER BY company, title
            """,
            conn,
        )
    finally:
        conn.close()


@st.cache_data
def load_skills() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql_query(
            """
            SELECT skill, COUNT(*) AS jobs
            FROM job_skills
            GROUP BY skill
            ORDER BY jobs DESC, skill ASC
            LIMIT 25
            """,
            conn,
        )
    finally:
        conn.close()


def parse_skills(value: str) -> str:
    try:
        return ", ".join(json.loads(value or "[]"))
    except json.JSONDecodeError:
        return ""


st.set_page_config(page_title="ITviec Dashboard", layout="wide")
st.title("ITviec Jobs Dashboard")

try:
    jobs = load_jobs()
    skills = load_skills()
except sqlite3.OperationalError:
    st.error("Chưa có itviec.db. Chạy `python import_to_sqlite.py` trước.")
    st.stop()

with st.sidebar:
    st.header("Filters")
    keyword = st.text_input("Search")
    locations = st.multiselect("Location", sorted(jobs["location"].dropna().unique()))
    modes = st.multiselect("Working mode", sorted(jobs["working_mode"].dropna().unique()))
    levels = st.multiselect("Level", sorted(jobs["level"].dropna().unique()))
    only_salary = st.checkbox("Has visible salary")

filtered = jobs.copy()
if keyword:
    haystack = (
        filtered["title"].fillna("")
        + " "
        + filtered["company"].fillna("")
        + " "
        + filtered["skills_json"].fillna("")
    )
    filtered = filtered[haystack.str.contains(keyword, case=False, na=False)]
if locations:
    filtered = filtered[filtered["location"].isin(locations)]
if modes:
    filtered = filtered[filtered["working_mode"].isin(modes)]
if levels:
    filtered = filtered[filtered["level"].isin(levels)]
if only_salary:
    filtered = filtered[
        filtered["salary"].fillna("").ne("")
        & ~filtered["salary"].fillna("").str.contains("Sign in", case=False)
    ]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Jobs", len(filtered))
col2.metric("Companies", filtered["company"].nunique())
col3.metric("Locations", filtered["location"].nunique())
col4.metric("Skills", skills["skill"].nunique())

left, right = st.columns(2)
with left:
    st.subheader("Top skills")
    st.bar_chart(skills.set_index("skill"))
with right:
    st.subheader("Working mode")
    st.bar_chart(filtered["working_mode"].value_counts())

st.subheader("Jobs")
table = filtered[
    ["title", "level", "company", "salary", "working_mode", "location", "posted_time", "label", "url"]
].copy()
st.dataframe(table, use_container_width=True, hide_index=True)

selected_url = st.selectbox("Open job detail", filtered["url"].tolist())
if selected_url:
    job = filtered[filtered["url"] == selected_url].iloc[0]
    st.markdown(f"### [{job['title']}]({job['url']})")
    st.write(f"**Company:** {job['company']}")
    st.write(f"**Level:** {job['level']}")
    st.write(f"**Salary:** {job['salary']}")
    st.write(f"**Skills:** {parse_skills(job['skills_json'])}")

    for label, field in [
        ("Job description", "job_description"),
        ("Requirements", "requirements"),
        ("Benefits", "benefits"),
    ]:
        value = job.get(field)
        if isinstance(value, str) and value.strip():
            with st.expander(label):
                st.write(value)
