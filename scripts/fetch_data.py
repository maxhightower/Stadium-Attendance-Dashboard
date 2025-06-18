"""
Download NFL attendance data from the 2020-02-04 TidyTuesday release.

• Mandatory file: `attendance.csv`
• Optional file : `team_standings.html` (scraped from Pro-Football-Reference)

Both files are written to data/raw/.
"""
from pathlib import Path
import sys
import requests

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# TidyTuesday raw CSV (always available)
ATT_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/"
    "main/data/2020/2020-02-04/attendance.csv"
)

# Team standings page (HTML table) for extra context (optional)
STAND_URL = "https://www.pro-football-reference.com/years/2019/index.htm"


def download(url: str, dest: Path) -> bool:
    resp = requests.get(url, timeout=30)
    if resp.status_code == 404:
        return False
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"✔ {dest.relative_to(Path.cwd())} ({len(resp.content)/1024:.1f} KB)")
    return True


def main() -> None:
    print("📦 Downloading NFL attendance dataset (TidyTuesday 2020-02-04)")
    if not download(ATT_URL, RAW_DIR / "attendance.csv"):
        sys.exit("✖ attendance.csv not found — abort")

    # optional standings
    if not download(STAND_URL, RAW_DIR / "team_standings.html"):
        print("⚠ Could not fetch team standings — continuing without it")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.exit(f"✖ {exc}")
