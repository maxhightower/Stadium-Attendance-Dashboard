"""Download MLB `attendance.csv` (required) and `schedule_2019_2023.csv`
(optional) from the TidyTuesday 2023 dataset **without hitting the GitHub
API** — so there is *zero* chance of a 403 rate‑limit.

Approach
========
1. Generate the list of all Tuesdays in 2023 (TidyTuesday releases are
   always on Tuesdays).
2. Iterate newest ➜ oldest; for each date attempt to download
   `attendance.csv` directly from the raw URL.
3. The first date that returns HTTP 200 is used.
4. Download `schedule_2019_2023.csv` if present (it exists in the same
   folder for the relevant weeks).

Environment overrides
---------------------
* `TT_DATE_OVERRIDE` – e.g. `2023-03-21`; if set we try that date *only*.
"""
from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path
from typing import List

import requests

RAW_DIR = Path("data/raw"); RAW_DIR.mkdir(parents=True, exist_ok=True)
RAW_BASE = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2023/"
MANDATORY = "attendance.csv"; OPTIONAL = "schedule_2019_2023.csv"


def tuesdays_2023() -> List[str]:
    """Return all Tuesdays (ISO weekday 2) in 2023 as YYYY‑MM‑DD strings."""
    d = dt.date(2023, 1, 1)
    # advance to first Tuesday
    d += dt.timedelta(days=(1 - d.weekday()) % 7)  # weekday(): Mon=0 … Sun=6
    dates = []
    while d.year == 2023:
        dates.append(d.strftime("%Y-%m-%d"))
        d += dt.timedelta(days=7)
    return dates[::-1]  # newest first


def download(url: str, dest: Path) -> bool:
    r = requests.get(url, timeout=30)
    if r.status_code == 404:
        return False
    r.raise_for_status()
    dest.write_bytes(r.content)
    print(f"✔ {dest.relative_to(Path.cwd())} ({len(r.content)/1024:.1f} KB)")
    return True


def main() -> None:
    override = os.getenv("TT_DATE_OVERRIDE")
    dates = [override] if override else tuesdays_2023()

    chosen = None
    for date in dates:
        raw_att = f"{RAW_BASE}{date}/{MANDATORY}"
        if requests.head(raw_att, timeout=15).status_code == 200:
            chosen = date
            break
    if chosen is None:
        sys.exit("✖ Could not find any 2023 Tuesday folder with attendance.csv")

    print(f"📦 Using TidyTuesday dataset folder: {chosen}")
    # mandatory
    if not download(f"{RAW_BASE}{chosen}/{MANDATORY}", RAW_DIR / MANDATORY):
        sys.exit("✖ attendance.csv unexpectedly 404 – abort")
    # optional schedule
    download(f"{RAW_BASE}{chosen}/{OPTIONAL}", RAW_DIR / OPTIONAL)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"✖ {exc}")
        sys.exit(1)
