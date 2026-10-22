
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "student-management-demo-key"

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "students.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                course TEXT NOT NULL,
                phone TEXT NOT NULL
            )
        """)


@app.route("/")
def home():
    search = request.args.get("search", "").strip()

    with get_db() as conn:
        if search:
            students = conn.execute("""
                SELECT * FROM students
                WHERE name LIKE ? OR email LIKE ? OR course LIKE ?
                ORDER BY id DESC
            """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
        else:
            students = conn.execute("""
                SELECT * FROM students ORDER BY id DESC
            """).fetchall()

        total = conn.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]

        courses = conn.execute(
            "SELECT COUNT(DISTINCT course) FROM students"
        ).fetchone()[0]

    return render_template(
        "index.html",
        students=students,
        total=total,
        courses=courses,
        search=search
    )


@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()
    phone = request.form.get("phone", "").strip()

    if not all([name, email, course, phone]):
        flash("Please fill in every field.", "error")
        return redirect(url_for("home"))

    if "@" not in email or "." not in email.split("@")[-1]:
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("home"))

    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO students (name, email, course, phone)
                VALUES (?, ?, ?, ?)
            """, (name, email, course, phone))

        flash("Student added successfully!", "success")

    except sqlite3.IntegrityError:
        flash("Could not save this student.", "error")

    return redirect(url_for("home"))


@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM students WHERE id = ?", (student_id,)
        )

    if cursor.rowcount:
        flash("Student record deleted.", "success")
    else:
        flash("Student record was not found.", "error")

    return redirect(url_for("home"))


initialize_database()

if __name__ == "__main__":
    app.run(debug=True)
