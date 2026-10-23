"""Stages 1 & 3 - SQLite storage, CRUD operations and SQL queries."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "students.db"

EDITABLE_FIELDS = {"name", "department", "attendance", "assignment_score", "exam_score"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    student_id       TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    department       TEXT NOT NULL,
    attendance       REAL CHECK (attendance       BETWEEN 0 AND 100),
    assignment_score REAL CHECK (assignment_score BETWEEN 0 AND 100),
    exam_score       REAL CHECK (exam_score       BETWEEN 0 AND 100)
);
"""


@contextmanager
def connect(db_path: Path = DB_PATH):
    """Open a connection, commit on success, always close."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_table(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)


def load_dataframe(df: pd.DataFrame, db_path: Path = DB_PATH) -> int:
    """(Re)build the students table from a DataFrame."""
    with connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS students")
        conn.executescript(SCHEMA)
        cols = ["student_id", "name", "department", "attendance",
                "assignment_score", "exam_score"]
        conn.executemany(
            f"INSERT INTO students ({','.join(cols)}) VALUES (?,?,?,?,?,?)",
            df[cols].itertuples(index=False, name=None),
        )
        return conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]


# ------------------------------ CRUD ------------------------------
def add_student(student_id, name, department, attendance, assignment_score,
                exam_score, db_path: Path = DB_PATH) -> bool:
    try:
        with connect(db_path) as conn:
            conn.execute("INSERT INTO students VALUES (?,?,?,?,?,?)",
                         (student_id, name, department, attendance,
                          assignment_score, exam_score))
        return True
    except sqlite3.IntegrityError as err:      # duplicate ID or CHECK failure
        print(f"  ! Could not add {student_id}: {err}")
        return False


def get_student(student_id, db_path: Path = DB_PATH) -> pd.DataFrame:
    with connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM students WHERE student_id = ?",
                                 conn, params=(student_id,))


def view_students(limit: int = 20, db_path: Path = DB_PATH) -> pd.DataFrame:
    with connect(db_path) as conn:
        return pd.read_sql_query("SELECT * FROM students ORDER BY student_id LIMIT ?",
                                 conn, params=(limit,))


def update_student(student_id, db_path: Path = DB_PATH, **fields) -> bool:
    fields = {k: v for k, v in fields.items() if k in EDITABLE_FIELDS}
    if not fields:
        print("  ! No valid fields to update")
        return False
    assignments = ", ".join(f"{k} = ?" for k in fields)   # keys are whitelisted
    try:
        with connect(db_path) as conn:
            cur = conn.execute(f"UPDATE students SET {assignments} WHERE student_id = ?",
                               (*fields.values(), student_id))
            return cur.rowcount > 0
    except sqlite3.IntegrityError as err:
        print(f"  ! Could not update {student_id}: {err}")
        return False


def delete_student(student_id, db_path: Path = DB_PATH) -> bool:
    with connect(db_path) as conn:
        cur = conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        return cur.rowcount > 0


# ------------------------------ SQL queries ------------------------------
def _query(sql: str, params=(), db_path: Path = DB_PATH) -> pd.DataFrame:
    with connect(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def top_students(n: int = 10, db_path: Path = DB_PATH) -> pd.DataFrame:
    """Highest final scores (30% assignments + 70% exam)."""
    return _query("""
        SELECT student_id, name, department, attendance, assignment_score, exam_score,
               ROUND(0.3 * assignment_score + 0.7 * exam_score, 2) AS final_score
        FROM students
        ORDER BY final_score DESC
        LIMIT ?""", (n,), db_path)


def average_by_department(db_path: Path = DB_PATH) -> pd.DataFrame:
    return _query("""
        SELECT department,
               COUNT(*)                                   AS students,
               ROUND(AVG(attendance), 2)                  AS avg_attendance,
               ROUND(AVG(assignment_score), 2)            AS avg_assignment,
               ROUND(AVG(exam_score), 2)                  AS avg_exam,
               ROUND(AVG(0.3 * assignment_score + 0.7 * exam_score), 2) AS avg_final
        FROM students
        GROUP BY department
        ORDER BY avg_final DESC""", db_path=db_path)


def low_attendance(threshold: float = 75, db_path: Path = DB_PATH) -> pd.DataFrame:
    return _query("""
        SELECT student_id, name, department, attendance, exam_score
        FROM students
        WHERE attendance < ?
        ORDER BY attendance ASC""", (threshold,), db_path)


# ------------------------------ simple CLI ------------------------------
def _menu() -> None:
    actions = "1) View  2) Add  3) Update  4) Delete  5) Top 10  6) Dept averages  7) Low attendance  0) Exit"
    while True:
        print("\n" + actions)
        choice = input("Choose: ").strip()
        if choice == "0":
            break
        elif choice == "1":
            print(view_students(25).to_string(index=False))
        elif choice == "2":
            try:
                add_student(input("ID: ").strip().upper(), input("Name: ").strip().title(),
                            input("Department: ").strip().title(),
                            float(input("Attendance: ")), float(input("Assignment: ")),
                            float(input("Exam: ")))
            except ValueError:
                print("  ! Scores must be numbers")
        elif choice == "3":
            sid = input("ID to update: ").strip().upper()
            field = input(f"Field {sorted(EDITABLE_FIELDS)}: ").strip()
            value = input("New value: ").strip()
            if field in {"attendance", "assignment_score", "exam_score"}:
                try:
                    value = float(value)
                except ValueError:
                    print("  ! Must be a number")
                    continue
            print("Updated" if update_student(sid, **{field: value}) else "Not updated")
        elif choice == "4":
            print("Deleted" if delete_student(input("ID to delete: ").strip().upper())
                  else "ID not found")
        elif choice == "5":
            print(top_students().to_string(index=False))
        elif choice == "6":
            print(average_by_department().to_string(index=False))
        elif choice == "7":
            print(low_attendance().to_string(index=False))


if __name__ == "__main__":
    _menu()
