"""Stage 2 - load, inspect, diagnose and clean the raw student data."""
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_CSV = BASE_DIR / "data" / "students.csv"
CLEAN_CSV = BASE_DIR / "reports" / "cleaned_students.csv"

SCORE_COLUMNS = ["attendance", "assignment_score", "exam_score"]
KEY_COLUMNS = ["student_id", "name", "department"]


def load_raw(path: Path = RAW_CSV) -> pd.DataFrame:
    return pd.read_csv(path)


def inspect(df: pd.DataFrame) -> None:
    """Print a first look at the data."""
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")
    print("First 5 rows:\n", df.head().to_string(index=False), "\n")
    print("Data types:\n", df.dtypes.to_string(), "\n")
    print("Descriptive statistics (raw):\n", df.describe().round(2).to_string(), "\n")


def find_issues(df: pd.DataFrame) -> dict:
    """Diagnose problems WITHOUT changing the data."""
    work = df.replace(r"^\s*$", np.nan, regex=True)
    issues = {"missing_values": work.isna().sum().to_dict()}

    ids = work["student_id"].astype("string").str.strip().str.upper()
    issues["exact_duplicate_rows"] = int(df.duplicated().sum())
    dup_mask = ids.duplicated(keep=False) & ids.notna()
    issues["rows_sharing_a_student_id"] = int(dup_mask.sum())
    issues["duplicate_student_ids"] = sorted(ids[dup_mask].unique().tolist())

    invalid = {}
    for col in SCORE_COLUMNS:
        num = pd.to_numeric(work[col], errors="coerce")
        invalid[col] = int(((num < 0) | (num > 100)).sum())
    issues["invalid_scores_out_of_0_100"] = invalid

    dept = work["department"].dropna().astype(str)
    issues["department_spellings_before"] = sorted(dept.unique().tolist())
    return issues


def print_issues(issues: dict) -> None:
    print("=== DATA QUALITY REPORT ===")
    print("Missing values per column:")
    for col, n in issues["missing_values"].items():
        print(f"  {col:<18}{n}")
    print(f"Exact duplicate rows        : {issues['exact_duplicate_rows']}")
    print(f"Rows sharing a student ID   : {issues['rows_sharing_a_student_id']} "
          f"-> {issues['duplicate_student_ids']}")
    print("Invalid scores (outside 0-100):")
    for col, n in issues["invalid_scores_out_of_0_100"].items():
        print(f"  {col:<18}{n}")
    print(f"Department spellings found  : {len(issues['department_spellings_before'])} "
          f"(should be 6)\n")


def clean(df: pd.DataFrame):
    """Return (cleaned_df, log). Each step records how many rows/values it touched."""
    log = {"rows_before": len(df)}
    df = df.replace(r"^\s*$", np.nan, regex=True).copy()

    # 1. standardise text
    df["student_id"] = df["student_id"].astype("string").str.strip().str.upper()
    for col in ["name", "department"]:
        df[col] = (df[col].astype("string").str.split().str.join(" ").str.title())

    # 2. drop rows missing a key identifier
    before = len(df)
    df = df.dropna(subset=KEY_COLUMNS)
    log["dropped_missing_id_name_or_department"] = before - len(df)

    # 3. duplicates (exact copies first, then reused IDs - keep first record)
    before = len(df)
    df = df.drop_duplicates()
    log["dropped_exact_duplicates"] = before - len(df)
    before = len(df)
    df = df.drop_duplicates(subset="student_id", keep="first")
    log["dropped_duplicate_student_ids"] = before - len(df)

    # 4. invalid scores -> NaN
    invalid_total = 0
    for col in SCORE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        bad = (df[col] < 0) | (df[col] > 100)
        invalid_total += int(bad.sum())
        df.loc[bad, col] = np.nan
    log["invalid_scores_set_to_missing"] = invalid_total

    # 5. exam score is the key measure: cannot be guessed -> drop
    before = len(df)
    df = df.dropna(subset=["exam_score"])
    log["dropped_missing_exam_score"] = before - len(df)

    # 6. attendance / assignment gaps -> department median
    imputed = 0
    for col in ["attendance", "assignment_score"]:
        imputed += int(df[col].isna().sum())
        df[col] = df[col].fillna(df.groupby("department")[col].transform("median"))
    log["values_imputed_with_dept_median"] = imputed

    df = df.sort_values("student_id").reset_index(drop=True)
    for col in ["student_id", "name", "department"]:
        df[col] = df[col].astype(str)
    df[SCORE_COLUMNS] = df[SCORE_COLUMNS].round(1)
    log["rows_after"] = len(df)
    return df, log


def export_clean(df: pd.DataFrame, path: Path = CLEAN_CSV) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


if __name__ == "__main__":
    raw = load_raw()
    inspect(raw)
    print_issues(find_issues(raw))
    cleaned, log = clean(raw)
    print("Cleaning log:", log)
    print("Saved:", export_clean(cleaned))
