"""
Build a DuckDB from the raw attendance CSV and generate an interactive
Plotly HTML dashboard.

Run:
    python scripts/build_dashboard.py --team "Dallas Cowboys"
"""
import argparse
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
from jinja2 import Template

RAW_DIR   = Path("data/raw")
DB_PATH   = Path("data/stadium.duckdb")
HTML_OUT  = Path("html/dashboard.html")
ATT_CSV   = RAW_DIR / "attendance.csv"

# ──────────────────────────────────────────────────────────────
# 1. Prepare DuckDB
# ──────────────────────────────────────────────────────────────
def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH)
    con.execute(
        "CREATE OR REPLACE TABLE attendance AS "
        "SELECT * FROM read_csv_auto(?)",
        (str(ATT_CSV),),
    )
    con.close()


# ──────────────────────────────────────────────────────────────
# 2. Queries
# ──────────────────────────────────────────────────────────────
def rolling(con, team: str) -> pd.DataFrame:
    query = f"""
        WITH base AS (
            SELECT date, attendance, capacity,
                   ROW_NUMBER() OVER (ORDER BY date) rn
            FROM attendance
            WHERE team = '{team}'
        )
        SELECT date,
               AVG(attendance) OVER (ORDER BY rn
                                     ROWS BETWEEN 2 PRECEDING
                                     AND CURRENT ROW) AS roll_att,
               AVG(capacity) OVER (ORDER BY rn
                                   ROWS BETWEEN 2 PRECEDING
                                   AND CURRENT ROW) AS roll_cap
        FROM base
        ORDER BY date;
    """
    return con.execute(query).fetchdf()


def weekday(con, team: str) -> pd.DataFrame:
    query = f"""
        SELECT STRFTIME(date,'%w') AS weekday,
               CAST(STRFTIME(date,'%Y') AS INT) AS season,
               AVG(attendance * 1.0 / capacity) AS sell
        FROM attendance
        WHERE team = '{team}'
        GROUP BY 1,2
        ORDER BY 2,1;
    """
    return con.execute(query).fetchdf()


def annual(con, team: str) -> pd.DataFrame:
    query = f"""
        SELECT CAST(STRFTIME(date,'%Y') AS INT) AS season,
               AVG(attendance * 1.0 / capacity) AS sell
        FROM attendance
        WHERE team = '{team}'
        GROUP BY 1
        ORDER BY 1;
    """
    return con.execute(query).fetchdf()


# ──────────────────────────────────────────────────────────────
# 3. Build the dashboard
# ──────────────────────────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><title>NFL Attendance Dashboard</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>body{font-family:Arial;margin:0} .plot{width:90%;margin:40px auto}</style>
</head><body>
<h1 style="text-align:center">{{ team }} – Attendance Dashboard</h1>
<div class="plot" id="fig1"></div>
<div class="plot" id="fig2"></div>
<div class="plot" id="fig3"></div>
<script>
Plotly.newPlot('fig1', {{ fig1.data|safe }}, {{ fig1.layout|safe }});
Plotly.newPlot('fig2', {{ fig2.data|safe }}, {{ fig2.layout|safe }});
Plotly.newPlot('fig3', {{ fig3.data|safe }}, {{ fig3.layout|safe }});
</script>
</body></html>
"""

def ensure_table(con):
    """Create or replace attendance table if it doesn't exist."""
    exists = con.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_name = 'attendance'"
    ).fetchone()
    if not exists:
        con.execute(
            "CREATE OR REPLACE TABLE attendance AS "
            "SELECT * FROM read_csv_auto(?)",
            (str(ATT_CSV),),
        )
        print("✔ attendance table created (DuckDB)")

def build_dashboard(team: str = "Dallas Cowboys") -> None:
    if not ATT_CSV.exists():
        raise FileNotFoundError("attendance.csv missing – run fetch_data.py first")

    if not DB_PATH.exists():
        init_db()

    con = duckdb.connect(DB_PATH, read_only=True)
    ensure_table(con)

    fig1 = px.line(
        rolling(con, team),
        x="date",
        y=["roll_att", "roll_cap"],
        labels={"value": "3-Game Avg", "date": "Date"},
        title="Rolling Attendance vs Capacity",
    )
    fig2 = px.imshow(
        weekday(con, team).pivot("weekday", "season", "sell"),
        aspect="auto",
        labels=dict(color="Sell-through"),
        title="Weekday Effect",
    )
    fig3 = px.line(
        annual(con, team),
        x="season",
        y="sell",
        markers=True,
        title="Season-over-Season Sell-through",
    )
    con.close()

    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(
        Template(HTML_TEMPLATE).render(
            team=team, fig1=fig1.to_dict(), fig2=fig2.to_dict(), fig3=fig3.to_dict()
        ),
        encoding="utf-8",
    )
    print(f"✔ Dashboard saved to {HTML_OUT.relative_to(Path.cwd())}")


# ──────────────────────────────────────────────────────────────
# 4. CLI entry-point
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build NFL attendance dashboard")
    parser.add_argument("--team", default="Dallas Cowboys", help="Team name (as it appears in CSV)")
    args = parser.parse_args()
    build_dashboard(args.team)

