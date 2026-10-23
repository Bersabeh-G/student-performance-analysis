"""Stages 4, 5 & 6 - statistics, charts and the CSV summary report."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # render to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import database

BASE_DIR = Path(__file__).resolve().parent.parent
VIS_DIR = BASE_DIR / "visualizations"
REPORT_CSV = BASE_DIR / "reports" / "analysis_summary.csv"

ASSIGNMENT_WEIGHT, EXAM_WEIGHT = 0.3, 0.7
PASS_MARK = 60            # final score needed to pass
LOW_ATTENDANCE = 75       # % below which attendance is "low"


def load_students() -> pd.DataFrame:
    """Read the students table from SQLite and add the final score + pass flag."""
    with database.connect() as conn:
        df = pd.read_sql_query("SELECT * FROM students", conn)
    df["final_score"] = (ASSIGNMENT_WEIGHT * df["assignment_score"]
                         + EXAM_WEIGHT * df["exam_score"]).round(2)
    df["passed"] = df["final_score"] >= PASS_MARK
    return df


# ------------------------------ analysis ------------------------------
def _plain(d: dict) -> dict:
    """Convert numpy scalars to plain Python numbers for clean printing."""
    return {k: (_plain(v) if isinstance(v, dict) else v.item() if hasattr(v, "item") else v)
            for k, v in d.items()}


def overall_stats(df: pd.DataFrame) -> dict:
    return _plain({
        "students": len(df),
        "avg_attendance": round(df["attendance"].mean(), 2),
        "avg_assignment": round(df["assignment_score"].mean(), 2),
        "avg_exam": round(df["exam_score"].mean(), 2),
        "avg_final": round(df["final_score"].mean(), 2),
        "median_final": round(df["final_score"].median(), 2),
        "std_final": round(df["final_score"].std(), 2),
        "pass_rate_pct": round(df["passed"].mean() * 100, 1),
    })


def department_stats(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("department")
              .agg(students=("student_id", "count"),
                   avg_attendance=("attendance", "mean"),
                   avg_exam=("exam_score", "mean"),
                   avg_final=("final_score", "mean"),
                   pass_rate_pct=("passed", lambda s: s.mean() * 100))
              .round(2).sort_values("avg_final", ascending=False).reset_index())


def attendance_relationship(df: pd.DataFrame) -> dict:
    corr = {c: round(df["attendance"].corr(df[c]), 3)
            for c in ["exam_score", "assignment_score", "final_score"]}
    slope, intercept = np.polyfit(df["attendance"], df["final_score"], 1)
    low = df[df["attendance"] < LOW_ATTENDANCE]
    ok = df[df["attendance"] >= LOW_ATTENDANCE]
    return _plain({
        "correlation": corr,
        "points_per_10pct_attendance": round(slope * 10, 2),
        "low_attendance_students": len(low),
        "low_att_avg_final": round(low["final_score"].mean(), 2),
        "low_att_pass_rate_pct": round(low["passed"].mean() * 100, 1),
        "good_att_avg_final": round(ok["final_score"].mean(), 2),
        "good_att_pass_rate_pct": round(ok["passed"].mean() * 100, 1),
    })


def attendance_bands(df: pd.DataFrame) -> pd.DataFrame:
    bands = pd.cut(df["attendance"], [0, 60, 75, 90, 100.01],
                   labels=["<60%", "60-74%", "75-89%", "90-100%"], right=False)
    return (df.groupby(bands, observed=True)
              .agg(students=("student_id", "count"),
                   avg_final=("final_score", "mean"),
                   pass_rate_pct=("passed", lambda s: s.mean() * 100))
              .round(2).reset_index().rename(columns={"attendance": "attendance_band"}))


# ------------------------------ charts ------------------------------
def plot_department_averages(dept: pd.DataFrame, path: Path = VIS_DIR / "department_averages.png"):
    path.parent.mkdir(parents=True, exist_ok=True)
    d = dept.sort_values("avg_final")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(d["department"], d["avg_final"], color="#3b82f6")
    ax.bar_label(bars, fmt="%.1f", padding=3)
    ax.axvline(PASS_MARK, color="#dc2626", linestyle="--", label=f"Pass mark ({PASS_MARK})")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Average final score")
    ax.set_title("Average Final Score by Department")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_score_distribution(df: pd.DataFrame, path: Path = VIS_DIR / "score_distribution.png"):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, col, color, title in [(axes[0], "exam_score", "#10b981", "Exam Scores"),
                                  (axes[1], "final_score", "#8b5cf6", "Final Scores")]:
        ax.hist(df[col], bins=15, color=color, edgecolor="white")
        ax.axvline(df[col].mean(), color="black", linestyle="--",
                   label=f"Mean = {df[col].mean():.1f}")
        if col == "final_score":
            ax.axvline(PASS_MARK, color="#dc2626", linestyle=":", label=f"Pass mark = {PASS_MARK}")
        ax.set_title(f"Distribution of {title}")
        ax.set_xlabel("Score")
        ax.legend()
    axes[0].set_ylabel("Number of students")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_attendance_vs_score(df: pd.DataFrame, path: Path = VIS_DIR / "attendance_vs_score.png"):
    """Bonus chart: attendance vs final score with a trend line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5.5))
    colors = np.where(df["passed"], "#3b82f6", "#ef4444")
    ax.scatter(df["attendance"], df["final_score"], c=colors, alpha=0.7)
    slope, intercept = np.polyfit(df["attendance"], df["final_score"], 1)
    xs = np.linspace(df["attendance"].min(), df["attendance"].max(), 50)
    ax.plot(xs, slope * xs + intercept, color="black", label="Trend line")
    ax.axhline(PASS_MARK, color="#dc2626", linestyle="--", alpha=0.6)
    ax.set_xlabel("Attendance (%)")
    ax.set_ylabel("Final score")
    r = df["attendance"].corr(df["final_score"])
    ax.set_title(f"Attendance vs Final Score (r = {r:.2f})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ------------------------------ report ------------------------------
def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for k, v in overall_stats(df).items():
        rows.append(("overall", "all students", k, v))
    for _, r in department_stats(df).iterrows():
        for k in ["students", "avg_attendance", "avg_exam", "avg_final", "pass_rate_pct"]:
            rows.append(("department", r["department"], k, r[k]))
    rel = attendance_relationship(df)
    for k, v in rel["correlation"].items():
        rows.append(("attendance_relationship", "pearson_r_with_attendance", k, v))
    for k, v in rel.items():
        if k != "correlation":
            rows.append(("attendance_relationship", "summary", k, v))
    for _, r in attendance_bands(df).iterrows():
        for k in ["students", "avg_final", "pass_rate_pct"]:
            rows.append(("attendance_band", str(r["attendance_band"]), k, r[k]))
    return pd.DataFrame(rows, columns=["section", "group", "metric", "value"])


def export_summary(df: pd.DataFrame, path: Path = REPORT_CSV) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    build_summary(df).to_csv(path, index=False)
    return path
