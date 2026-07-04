import argparse
import json
import sqlite3
from pathlib import Path


DEFAULT_DB = "itviec.db"


def load_jobs(json_path: Path, state_path: Path) -> list[dict]:
    if json_path.exists() and json_path.stat().st_size > 0:
        return json.loads(json_path.read_text(encoding="utf-8"))

    if state_path.exists() and state_path.stat().st_size > 0:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        detailed = state.get("detailed") or {}
        if detailed:
            return list(detailed.values())
        return state.get("allJobs") or []

    raise FileNotFoundError(
        f"Could not find data in {json_path} or {state_path}. Run `node scraper.js` first."
    )


def as_json(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS job_skills;
        DROP TABLE IF EXISTS jobs;

        CREATE TABLE jobs (
          url TEXT PRIMARY KEY,
          job_key TEXT,
          slug TEXT,
          title TEXT,
          level TEXT,
          company TEXT,
          company_slug TEXT,
          salary TEXT,
          working_mode TEXT,
          location TEXT,
          posted_time TEXT,
          label TEXT,
          tags_json TEXT,
          skills_json TEXT,
          reasons TEXT,
          job_description TEXT,
          requirements TEXT,
          benefits TEXT,
          company_info_json TEXT,
          scraped_at TEXT
        );

        CREATE TABLE job_skills (
          url TEXT NOT NULL,
          skill TEXT NOT NULL,
          PRIMARY KEY (url, skill),
          FOREIGN KEY (url) REFERENCES jobs(url)
        );

        CREATE INDEX idx_jobs_company ON jobs(company);
        CREATE INDEX idx_jobs_location ON jobs(location);
        CREATE INDEX idx_jobs_working_mode ON jobs(working_mode);
        CREATE INDEX idx_job_skills_skill ON job_skills(skill);
        """
    )


def insert_jobs(conn: sqlite3.Connection, jobs: list[dict]) -> None:
    rows = []
    skill_rows = []

    for job in jobs:
        url = job.get("url")
        if not url:
            continue

        tags = job.get("tags") or []
        skills = job.get("skills") or tags
        company_info = job.get("companyInfo") or {}

        rows.append(
            (
                url,
                job.get("jobKey"),
                job.get("slug"),
                job.get("title"),
                job.get("level"),
                job.get("company"),
                job.get("companySlug"),
                job.get("salary"),
                job.get("workingMode"),
                job.get("location"),
                job.get("postedTime"),
                job.get("label"),
                as_json(tags),
                as_json(skills),
                job.get("reasons"),
                job.get("jobDescription"),
                job.get("requirements"),
                job.get("benefits"),
                json.dumps(company_info, ensure_ascii=False),
                job.get("scrapedAt"),
            )
        )

        for skill in dict.fromkeys(skills):
            if skill:
                skill_rows.append((url, skill))

    conn.executemany(
        """
        INSERT OR REPLACE INTO jobs (
          url, job_key, slug, title, level, company, company_slug, salary, working_mode,
          location, posted_time, label, tags_json, skills_json, reasons,
          job_description, requirements, benefits, company_info_json, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO job_skills (url, skill) VALUES (?, ?)",
        skill_rows,
    )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import ITviec scraper data to SQLite.")
    parser.add_argument("--json", default="itviec-jobs.json")
    parser.add_argument("--state", default="itviec-state.json")
    parser.add_argument("--db", default=DEFAULT_DB)
    args = parser.parse_args()

    jobs = load_jobs(Path(args.json), Path(args.state))
    conn = sqlite3.connect(args.db)
    try:
        create_schema(conn)
        insert_jobs(conn, jobs)
    finally:
        conn.close()

    print(f"Imported {len(jobs)} jobs into {args.db}")


if __name__ == "__main__":
    main()
