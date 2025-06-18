"""Download the latest MLB attendance & schedule CSVs from TidyTuesday.

Instead of hard‑coding one week that may move or be renamed, we query the
GitHub API for the **first 2023 folder that contains the two files we
need** (`attendance.csv`, `schedule_2019_2023.csv`).

If the API ever changes directory structure, you can set the environment
variable `TT_DATE_OVERRIDE` to a date folder like `2023-03-21` and the
script will use that directly.
"""
from __future__ import annotations

import os
import sys
import requests
from pathlib import Path
from typing import Optional, Dict

RAW_BASE = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2023/"
)
API_BASE = (
    "https://api.github.com/repos/rfordatascience/tidytuesday/contents/data/2023"
)

REQUIRED_FILES = {
    "attendance.csv": None,
    "schedule_2019_2023.csv": None,
}

def github_listdir(dir_url: str) -> list[Dict]:
    """Return JSON listing for a directory via GitHub API."""
    r = requests.get(dir_url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"GitHub API error {r.status_code}: {dir_url}")
    return r.json()


def find_date_folder() -> str:
    """Find the first 2023 directory that contains all required CSVs."""
    override = os.getenv("TT_DATE_OVERRIDE")
    if override:
        return override

    # Step 1: list all date directories under data/2023
    root_listing = github_listdir(API_BASE)
    date_dirs = [item["name"] for item in root_listing if item["type"] == "dir"]
    # sort ascending so earliest date first (or use reversed for most recent)
    for date in sorted(date_dirs):
        sub_listing = github_listdir(f"{API_BASE}/{date}")
        names = {x["name"] for x in sub_listing}
        if all(req in names for req in REQUIRED_FILES):
            return date
    raise RuntimeError("Could not find a 2023 date directory with both required CSVs.")


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    kb = len(resp.content) / 1024
    print(f"✔ {dest.relative_to(Path.cwd())} ({kb:.1f} KB)")


def main() -> None:
    date = find_date_folder()
    print(f"Using TidyTuesday folder: {date}")

    for fname in REQUIRED_FILES.keys():
        raw_url = f"{RAW_BASE}{date}/{fname}"
        download(raw_url, Path("data/raw") / fname)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"✖ {exc}")
        sys.exit(1)