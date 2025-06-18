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

def ensure_view(con):
    """
    Create a view `attendance_week` that adds a proper DATE column
    (Monday of each NFL week) and a simplified `attendance` field.
    """
    con.execute(
        """
        CREATE OR REPLACE VIEW attendance_week AS
        SELECT
            team,
            team_name,
            year,
            week,
            -- Monday of the given ISO week becomes our date
            STRPTIME(year || '-' || week || '-1', '%Y-%W-%w') AS game_date,
            weekly_attendance AS attendance
        FROM attendance
        WHERE weekly_attendance IS NOT NULL
        """
    )

# ──────────────────────────────────────────────────────────────
# 2. Queries
# ──────────────────────────────────────────────────────────────
def rolling(con, team: str) -> pd.DataFrame:
    query = f"""
        WITH base AS (
            SELECT
                game_date,
                attendance,
                ROW_NUMBER() OVER (ORDER BY game_date) rn
            FROM attendance_week
            WHERE team_name = '{team}'
        )
        SELECT
            game_date,
            AVG(attendance) OVER (
                ORDER BY rn
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ) AS roll_att
        FROM base
        ORDER BY game_date;
    """
    return con.execute(query).fetchdf()


def weekday(con, team: str) -> pd.DataFrame:
    query = f"""
        SELECT
            STRFTIME(game_date, '%w') AS weekday,
            year,
            AVG(attendance) AS avg_att
        FROM attendance_week
        WHERE team_name = '{team}'
        GROUP BY 1, 2
        ORDER BY 2, 1;
    """
    return con.execute(query).fetchdf()


def annual(con, team: str) -> pd.DataFrame:
    query = f"""
        SELECT
            year,
            SUM(attendance) / 1000.0 AS total_att_k
        FROM attendance_week
        WHERE team_name = '{team}'
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
    ensure_view(con)

    fig1 = px.line(
        rolling(con, team),
        x="game_date",
        y="roll_att",
        labels={"roll_att": "3-Game Avg Attendance", "game_date": "Date"},
        title="Rolling Home-Game Attendance"
    )
    df_wd = weekday(con, team)
    # Make sure weekdays appear in logical order (Sun-Sat) in the heat-map
    weekday_order = ["0", "1", "2", "3", "4", "5", "6"]
    df_wd["weekday"] = pd.Categorical(df_wd["weekday"], categories=weekday_order, ordered=True)

    fig2 = px.imshow(
        df_wd.pivot(index="weekday", columns="year", values="avg_att"),
        aspect="auto",
        labels=dict(color="Avg Attendance"),
        title="Average Attendance by Weekday & Season",
    )

    # Optional: nicer y-axis tick labels
    fig2.update_yaxes(
        tickmode="array",
        tickvals=list(range(7)),
        ticktext=["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    )

    df_yr = annual(con, team)
    fig3 = px.line(
        df_yr,
        x="year",
        y="total_att_k",
        markers=True,
        labels={"total_att_k": "Total Attendance (thousands)", "year": "Season"},
        title="Season-over-Season Total Attendance",
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

