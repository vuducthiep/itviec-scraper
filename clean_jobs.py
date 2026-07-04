import argparse
import json
import re
from pathlib import Path


def clean_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_list(values):
    seen = set()
    result = []
    for value in values or []:
        item = clean_text(value)
        key = item.casefold()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
    return result


def normalize_location(value):
    text = clean_text(value)
    aliases = {
        "hanoi": "Ha Noi",
        "ha noi": "Ha Noi",
        "ho chi minh": "Ho Chi Minh",
        "hcm": "Ho Chi Minh",
        "da nang": "Da Nang",
    }
    return aliases.get(text.casefold(), text)


def normalize_working_mode(value):
    text = clean_text(value)
    low = text.casefold()
    if "remote" in low:
        return "Remote"
    if "hybrid" in low:
        return "Hybrid"
    if "office" in low:
        return "At office"
    return text


def infer_level(title):
    text = clean_text(title).casefold()
    patterns = [
        ("Intern", r"\bintern(ship)?\b"),
        ("Fresher", r"\bfresher\b"),
        ("Junior", r"\b(junior|jr)\b"),
        ("Middle", r"\b(middle|mid)\b"),
        ("Senior", r"\b(senior|sr)\b"),
        ("Lead", r"\blead\b"),
        ("Principal", r"\bprincipal\b"),
        ("Manager", r"\bmanager\b"),
        ("Expert", r"\bexpert\b"),
    ]
    return "/".join(level for level, pattern in patterns if re.search(pattern, text))


def parse_salary_usd(value):
    text = clean_text(value)
    low = text.casefold()
    if not text or any(x in low for x in ["sign in", "negotiable", "competitive", "attractive"]):
        return None, None

    nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*", text)]
    if not nums:
        return None, None

    if "up to" in low:
        return None, nums[0]
    if len(nums) == 1:
        return nums[0], nums[0]
    return nums[0], nums[1]


def load_jobs(json_path: Path, state_path: Path):
    if json_path.exists() and json_path.stat().st_size:
        return json.loads(json_path.read_text(encoding="utf-8"))

    state = json.loads(state_path.read_text(encoding="utf-8"))
    detailed = state.get("detailed") or {}
    return list(detailed.values()) if detailed else state.get("allJobs", [])


def clean_job(job):
    tags = clean_list(job.get("tags"))
    skills = clean_list(job.get("skills") or tags)
    salary_min, salary_max = parse_salary_usd(job.get("salary"))

    cleaned = dict(job)
    cleaned.update(
        {
            "jobKey": clean_text(job.get("jobKey")),
            "slug": clean_text(job.get("slug")),
            "title": clean_text(job.get("title")),
            "level": infer_level(job.get("title")),
            "url": clean_text(job.get("url")),
            "company": clean_text(job.get("company")),
            "companySlug": clean_text(job.get("companySlug")),
            "salary": clean_text(job.get("salary")),
            "salaryMinUsd": salary_min,
            "salaryMaxUsd": salary_max,
            "workingMode": normalize_working_mode(job.get("workingMode")),
            "location": normalize_location(job.get("location")),
            "tags": tags,
            "skills": skills,
            "postedTime": clean_text(job.get("postedTime")),
            "label": clean_text(job.get("label")).upper(),
            "reasons": clean_text(job.get("reasons")),
            "jobDescription": clean_text(job.get("jobDescription")),
            "requirements": clean_text(job.get("requirements")),
            "benefits": clean_text(job.get("benefits")),
            "companyInfo": {
                clean_text(k): clean_text(v)
                for k, v in (job.get("companyInfo") or {}).items()
                if clean_text(k) and clean_text(v)
            },
        }
    )
    return cleaned


def clean_jobs(jobs):
    by_url = {}
    for job in jobs:
        cleaned = clean_job(job)
        if cleaned["url"]:
            by_url[cleaned["url"]] = cleaned
    return list(by_url.values())


def self_test():
    lo, hi = parse_salary_usd("1,100 - 2,000 USD")
    assert (lo, hi) == (1100, 2000)
    assert parse_salary_usd("Up to $3200") == (None, 3200)
    assert normalize_location("hanoi") == "Ha Noi"
    assert clean_list([" Python ", "python", "", "SQL"]) == ["Python", "SQL"]
    assert infer_level("[Hanoi] Principal/ Senior Golang Engineer") == "Senior/Principal"


def main():
    parser = argparse.ArgumentParser(description="Clean ITviec scraped jobs without changing the scraper flow.")
    parser.add_argument("--json", default="itviec-jobs.json")
    parser.add_argument("--state", default="itviec-state.json")
    parser.add_argument("--out", default="itviec-jobs-clean.json")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        print("Self-test passed")
        return

    jobs = clean_jobs(load_jobs(Path(args.json), Path(args.state)))
    Path(args.out).write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(jobs)} cleaned jobs to {args.out}")


if __name__ == "__main__":
    main()
