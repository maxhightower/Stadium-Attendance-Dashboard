from pathlib import Path
import requests

DATA_SOURCES = {
    "attendance.csv": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2023/2023-03-28/attendance.csv",
    "schedule_2019_2023.csv": "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2023/2023-03-28/schedule_2019_2023.csv",
}

def download(url: str, dest: Path):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"✔ downloaded {dest.name} ({len(resp.content)/1_000:.1f} KB)")


def main():
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    for fname, url in DATA_SOURCES.items():
        download(url, raw_dir / fname)

if __name__ == "__main__":
    main()
