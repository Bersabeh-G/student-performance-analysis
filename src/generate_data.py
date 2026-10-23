"""Generate a realistic, deliberately messy student dataset (data/students.csv).

The data is fictional. Real-world problems are injected on purpose so the
cleaning stage has something meaningful to find:
  * missing values        * duplicate rows / conflicting duplicate IDs
  * out-of-range scores   * inconsistent department spelling
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "data" / "students.csv"

FIRST = ["Abel", "Hanna", "Daniel", "Sara", "Michael", "Meron", "Yonas", "Liya",
         "Samuel", "Tigist", "Kevin", "Amina", "David", "Ruth", "Brian", "Fatima",
         "Joseph", "Selam", "Peter", "Zainab", "Henok", "Mary", "Ahmed", "Eden",
         "Lucas", "Bethel", "Omar", "Grace", "Nathan", "Hiwot", "Ethan", "Rahel",
         "Ibrahim", "Mia", "Dawit", "Chloe", "Kidus", "Aisha", "Tomas", "Nardos"]
LAST = ["Tesfaye", "Bekele", "Alemu", "Haile", "Kebede", "Girma", "Tadesse", "Wolde",
        "Mekonnen", "Assefa", "Johnson", "Smith", "Khan", "Garcia", "Ali", "Brown",
        "Mohammed", "Negash", "Lemma", "Abebe", "Hussein", "Taylor", "Kassa", "Demissie",
        "Yilma", "Chen", "Patel", "Mulugeta", "Desta", "Hailu", "Gebru", "Ayele",
        "Wilson", "Tilahun", "Zewdu", "Fikre", "Berhanu", "Okafor", "Mensah", "Adane"]

# department -> average ability of its students
DEPARTMENTS = {
    "Computer Science": 71,
    "Electrical Engineering": 66,
    "Business Administration": 72,
    "Mechanical Engineering": 64,
    "Biology": 69,
    "Mathematics": 70,
}


def generate(n_students: int = 150, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # unique names
    combos = [(f, l) for f in FIRST for l in LAST]
    picks = rng.choice(len(combos), size=n_students, replace=False)
    names = [f"{combos[i][0]} {combos[i][1]}" for i in picks]

    depts = rng.choice(list(DEPARTMENTS), size=n_students)
    attendance = np.clip(rng.normal(80, 13, n_students), 35, 100)
    ability = np.array([rng.normal(DEPARTMENTS[d], 8) for d in depts])
    # attendance genuinely influences performance (+ random noise)
    exam = np.clip(ability + 0.35 * (attendance - 80) + rng.normal(0, 7, n_students), 5, 100)
    assignment = np.clip(ability + 0.15 * (attendance - 80) + rng.normal(5, 8, n_students), 10, 100)

    df = pd.DataFrame({
        "student_id": [f"S2024{i:03d}" for i in range(1, n_students + 1)],
        "name": names,
        "department": depts,
        "attendance": attendance.round(1),
        "assignment_score": assignment.round(1),
        "exam_score": exam.round(1),
    })

    # ---------- inject real-world problems ----------
    idx = rng.choice(n_students, size=24, replace=False)
    df.loc[idx[0:3], "attendance"] = np.nan          # missing attendance
    df.loc[idx[3:5], "assignment_score"] = np.nan    # missing assignment
    df.loc[idx[5:7], "exam_score"] = np.nan          # missing exam
    df.loc[idx[7], "name"] = np.nan                  # missing name
    df.loc[idx[8], "department"] = np.nan            # missing department
    df.loc[idx[9], "exam_score"] = 105.0             # invalid: > 100
    df.loc[idx[10], "exam_score"] = -8.0             # invalid: negative
    df.loc[idx[11], "assignment_score"] = 130.0      # invalid: > 100
    df.loc[idx[12], "attendance"] = 112.0            # invalid: > 100
    # inconsistent spelling / whitespace
    df.loc[idx[13:15], "department"] = df.loc[idx[13:15], "department"].str.lower()
    df.loc[idx[15:17], "department"] = df.loc[idx[15:17], "department"].str.upper()
    df.loc[idx[17:19], "department"] = " " + df.loc[idx[17:19], "department"] + " "
    df.loc[idx[19], "name"] = "  " + str(df.loc[idx[19], "name"]).lower() + " "

    # duplicates: 3 exact copies + 2 conflicting records with a reused ID
    exact = df.iloc[rng.choice(n_students, 3, replace=False)]
    conflict = df.iloc[rng.choice(n_students, 2, replace=False)].copy()
    conflict["exam_score"] = (conflict["exam_score"].fillna(60) - 10).round(1)
    df = pd.concat([df, exact, conflict], ignore_index=True)
    return df


if __name__ == "__main__":
    RAW_CSV.parent.mkdir(parents=True, exist_ok=True)
    data = generate()
    data.to_csv(RAW_CSV, index=False)
    print(f"Wrote {len(data)} raw records to {RAW_CSV}")
