"""Run the full Student Performance Analysis pipeline:  python main.py"""
import pandas as pd

from src import data_analysis as analysis
from src import data_cleaning as cleaning
from src import database, generate_data

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)


def banner(text: str) -> None:
    print("\n" + "=" * 70 + f"\n{text}\n" + "=" * 70)


def main() -> None:
    # ---- 0. dataset ----
    if not generate_data.RAW_CSV.exists():
        generate_data.RAW_CSV.parent.mkdir(exist_ok=True)
        generate_data.generate().to_csv(generate_data.RAW_CSV, index=False)

    # ---- 2. load, inspect, diagnose, clean ----
    banner("STAGE 2 - DATA INSPECTION & CLEANING")
    raw = cleaning.load_raw()
    cleaning.inspect(raw)
    cleaning.print_issues(cleaning.find_issues(raw))
    cleaned, log = cleaning.clean(raw)
    print("Cleaning log:")
    for k, v in log.items():
        print(f"  {k:<42}{v}")
    print("Cleaned dataset saved to:", cleaning.export_clean(cleaned))

    # ---- 1. database + CRUD demo ----
    banner("STAGE 1 - DATABASE & CRUD")
    n = database.load_dataframe(cleaned)
    print(f"Loaded {n} cleaned records into SQLite ({database.DB_PATH.name})")
    print("\nVIEW (first 5):\n", database.view_students(5).to_string(index=False))
    database.add_student("S9999", "Test Student", "Biology", 88, 75, 70)
    print("\nADD    ->", database.get_student("S9999").to_dict("records"))
    database.add_student("S9999", "Duplicate", "Biology", 80, 80, 80)   # rejected: same ID
    database.add_student("S9998", "Bad Score", "Biology", 80, 80, 150)  # rejected: CHECK
    database.update_student("S9999", exam_score=82.5, attendance=91)
    print("UPDATE ->", database.get_student("S9999").to_dict("records"))
    database.delete_student("S9999")
    print("DELETE ->", "gone" if database.get_student("S9999").empty else "still there")

    # ---- 3. SQL queries ----
    banner("STAGE 3 - SQL QUERIES")
    print("Top 10 students:\n", database.top_students(10).to_string(index=False))
    print("\nAverage by department:\n", database.average_by_department().to_string(index=False))
    low = database.low_attendance(analysis.LOW_ATTENDANCE)
    print(f"\nStudents with attendance < {analysis.LOW_ATTENDANCE}%: {len(low)}")
    print(low.head(10).to_string(index=False))

    # ---- 4. analysis ----
    banner("STAGE 4 - DATA ANALYSIS")
    df = analysis.load_students()
    print("Overall:", analysis.overall_stats(df))
    print("\nBy department:\n", analysis.department_stats(df).to_string(index=False))
    rel = analysis.attendance_relationship(df)
    print("\nAttendance vs performance:")
    for k, v in rel.items():
        print(f"  {k}: {v}")
    print("\nBy attendance band:\n", analysis.attendance_bands(df).to_string(index=False))

    # ---- 5. charts ----
    banner("STAGE 5 - VISUALIZATION")
    dept = analysis.department_stats(df)
    for p in (analysis.plot_department_averages(dept),
              analysis.plot_score_distribution(df),
              analysis.plot_attendance_vs_score(df)):
        print("Saved", p)

    # ---- 6. report ----
    banner("STAGE 6 - REPORTING")
    print("Saved", analysis.export_summary(df))
    print("Saved", cleaning.CLEAN_CSV)


if __name__ == "__main__":
    main()
