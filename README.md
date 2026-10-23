# Student Performance Data Analysis System

A complete data-analysis project that stores student records in **SQLite**, cleans messy data with **Pandas**,
answers questions with **SQL**, and presents findings with **Matplotlib**.

The dataset is fictional (155 raw records) and was generated with realistic, deliberately injected data-quality
problems so every stage has real work to do.

## Project structure

```
student-performance-analysis/
├── data/students.csv                  # raw (messy) dataset - 155 rows
├── database/students.db               # SQLite database built from the cleaned data
├── src/
│   ├── generate_data.py               # creates the raw dataset (seeded, reproducible)
│   ├── data_cleaning.py               # load, inspect, diagnose, clean, export
│   ├── database.py                    # SQLite CRUD + SQL queries + interactive menu
│   └── data_analysis.py               # statistics, charts, summary report
├── visualizations/
│   ├── department_averages.png
│   ├── score_distribution.png
│   └── attendance_vs_score.png        # bonus chart
├── reports/
│   ├── cleaned_students.csv           # cleaned dataset (144 rows)
│   └── analysis_summary.csv           # summary report
├── main.py                            # runs the whole pipeline
├── requirements.txt
└── README.md
```

## How to run

```bash
pip install -r requirements.txt
python main.py                  # full pipeline: clean -> database -> SQL -> analysis -> charts -> reports
python src/database.py          # optional: interactive menu (view / add / update / delete / queries)
python -m src.generate_data     # optional: regenerate the raw CSV (run from project root)
```

## Stages

| # | Stage | Where | What it does |
|---|-------|-------|--------------|
| 1 | Data management | `database.py` | `add_student`, `view_students`, `get_student`, `update_student`, `delete_student`. The table has a primary key and `CHECK` constraints, so duplicate IDs and scores outside 0-100 are rejected by the database itself. |
| 2 | Data cleaning | `data_cleaning.py` | Reports missing values, duplicate IDs and invalid scores, then cleans (see below). |
| 3 | SQL queries | `database.py` | `top_students()`, `average_by_department()`, `low_attendance()` |
| 4 | Data analysis | `data_analysis.py` | Averages, pass rates, attendance-performance correlation and attendance bands. |
| 5 | Visualization | `data_analysis.py` | Department averages bar chart, score histograms, attendance scatter plot. |
| 6 | Reporting | `data_analysis.py` | Exports `cleaned_students.csv` and `analysis_summary.csv`. |

### Grading rules (editable constants in `data_analysis.py`)
- **Final score** = 30% assignment + 70% exam
- **Pass mark** = 60
- **Low attendance** = below 75%

## Data cleaning results

| Problem found in raw data | Action taken |
|---|---|
| 12 department spellings (should be 6): `biology`, `BIOLOGY`, ` Biology ` ... | Trim, collapse spaces, title-case |
| Missing name or department (2 rows) | Row dropped - student cannot be identified |
| 3 exact duplicate rows | Removed |
| 2 conflicting records re-using an existing `student_id` | First record kept |
| 4 invalid scores (exam 105 and -8, assignment 130, attendance 112) | Set to missing |
| Missing exam score (2 original + 2 from invalid values) | Row dropped - the key measure should not be guessed |
| Missing attendance / assignment (7 values) | Filled with the department median |

**155 raw rows -> 144 clean rows.**

## Key findings

- Overall average final score is **69.6** (std 10.2) and the overall **pass rate is 84.7%**.
- **Computer Science** leads (avg 73.8). **Mechanical Engineering** is lowest (avg 65.9, pass rate only 66.7%).
- Attendance has a **moderate positive correlation with exam score (r = 0.31)** and almost none with assignment score (r = 0.04).
  Each extra 10 percentage points of attendance is associated with about **+2.2 final-score points**.
- 42 students (29%) are below 75% attendance. They average **65.6** vs **71.3** for the rest, and their pass rate is **78.6%** vs **87.3%**.

> Correlation is not causation: motivated students may both attend more and score higher.
> The dataset is synthetic, so the numbers illustrate the method, not a real institution.

## Possible extensions
- Add a Flask/Streamlit front-end on top of `database.py`
- Add a `grade` column (A-F) and analyse grade distribution
- Add semesters/courses as a second table and practise SQL `JOIN`s
