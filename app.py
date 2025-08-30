import os
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def get_db_connection():
    conn = sqlite3.connect('tpet.db',check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

@app.context_processor
def inject_user():
    if "teacher_id" in session:
        conn, cursor = get_db_connection()
        row = cursor.execute("SELECT name FROM teachers WHERE id = ?", (session["teacher_id"],)).fetchone()
        conn.close()
        if row:
            return {"name": row["name"]}
    return {"name": None}

@app.route("/")
def index():

    if "teacher_id" in session:
        return redirect("/class")

    else:
        return render_template("login.html")
    

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        conn, cursor = get_db_connection()
        username = request.form.get("username").lower()
        password = request.form.get("password")
       
        if not username or not password:
            message = "Username and/or password cannot be blank"
            return render_template("login.html", message = message)
        row = cursor.execute(
                "SELECT * FROM teachers WHERE username = ?", (username,)).fetchone()
        if not row or not check_password_hash(
            row["password"], password):
            message = "Username and/or password are wrong"
            return render_template("login.html", message = message)
        conn.close()
        session["teacher_id"] = row["id"]
        return redirect("/class")


    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
    if request.method == "POST":
        conn, cursor = get_db_connection()
        name = request.form.get("name").lower()
        username = request.form.get("username").lower()
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        hashed = generate_password_hash(password)

        if not name or not username or not password or not confirm:
            message = "Please fill all the required information."
            return render_template("/register.html", message=message)

        usernames_list = cursor.execute("SELECT username FROM teachers").fetchall()
        print(usernames_list)
        for row in usernames_list:
            if username == row["username"]:
                message = "Username was already taken."
                return render_template("/register.html", message=message)
            if password != confirm:
                message = "Passwords do not match."
                return render_template("/register.html", message=message)

        cursor.execute(
                "INSERT INTO teachers (name,username,password) VALUES (?,?,?)", (name, username, hashed))
        conn.commit()
        conn.close()
        message = "Registration succesfull. You can login now."
        return render_template("/login.html", message=message)
    
    return render_template("register.html")      

@app.route("/class", methods=["GET", "POST"])
def classes():
    conn, cursor = get_db_connection()
    row = cursor.execute("SELECT * FROM teachers WHERE id = ?", (session["teacher_id"],)).fetchone()
    name = row["name"]
    classes = cursor.execute("""
    SELECT 
        c.id, 
        c.name,
        (SELECT COUNT(*) FROM students s WHERE s.class_id = c.id) AS student_count,
        (SELECT COUNT(*) FROM class_notes n WHERE n.class_id = c.id) AS note_count,
        (SELECT COUNT(*) FROM exams e WHERE e.class_id = c.id) AS exam_count
    FROM classes c
    WHERE c.teacher_id = ?
    """, (session["teacher_id"],)).fetchall()
    total_classes = cursor.execute(
    "SELECT COUNT(*) FROM classes WHERE teacher_id = ?", 
    (session["teacher_id"],)
    ).fetchone()[0]
    conn.close()

    if request.method == "POST":
        if "name" in request.form:  # Add class
            class_name = request.form.get("name")
            conn, cursor = get_db_connection()
            cursor.execute(
                "INSERT INTO classes(name, teacher_id) VALUES(?,?)",
                (class_name, session["teacher_id"])
            )
            conn.commit()
            conn.close()
            return redirect("/class")

        elif "remove_id" in request.form:  # Delete class
            class_id = request.form.get("remove_id")
            conn, cursor = get_db_connection()
            cursor.execute(
                "DELETE FROM classes WHERE id = ? AND teacher_id = ?",
                (class_id, session["teacher_id"])
            )
            conn.commit()
            conn.close()
            flash("Class deleted.")
            return redirect("/class")

    return render_template("class.html", name=name, classes=classes, total_classes=total_classes)

@app.route("/students/add/<int:class_id>", methods=["GET", "POST"])
def add_student(class_id):
    conn, cursor = get_db_connection()
    # Check if class belongs to the logged-in teacher
    class_row = cursor.execute(
        "SELECT * FROM classes WHERE id = ? AND teacher_id = ?",
        (class_id, session["teacher_id"])
    ).fetchone()

    if not class_row:
        conn.close()
        flash("Class not found or unauthorized.")
        return redirect("/class")

    if request.method == "POST":
        student_name = request.form.get("name")
        if not student_name:
            flash("Student name cannot be blank.")
            return render_template("add_student.html", class_row=class_row)

        cursor.execute(
            "INSERT INTO students (name, class_id) VALUES (?, ?)",
            (student_name, class_id)
        )
        conn.commit()
        conn.close()
        flash("Student added successfully.")
        return redirect("/class")

    conn.close()
    return render_template("add_student.html", class_row=class_row)

@app.route("/class/<int:class_id>", methods=["GET", "POST"])
def class_detail(class_id):
    conn, cursor = get_db_connection()

    # Verify teacher owns this class
    class_row = cursor.execute(
        "SELECT * FROM classes WHERE id = ? AND teacher_id = ?",
        (class_id, session["teacher_id"])
    ).fetchone()
    if not class_row:
        conn.close()
        flash("Class not found or unauthorized.")
        return redirect("/class")

    # Handle POST requests (add/remove students, lessons, notes, exams)
    if request.method == "POST":
        # Add Exam
        if "exam_name" in request.form:
            exam_name = request.form.get("exam_name")
            exam_date = request.form.get("exam_date")
            if exam_name:
                cursor.execute(
                    "INSERT INTO exams (class_id, name, date) VALUES (?, ?, ?)",
                    (class_id, exam_name, exam_date)
                )
                conn.commit()
                flash("Exam added.")
        
        # Remove Exam
        elif "remove_exam_id" in request.form:
            exam_id = request.form.get("remove_exam_id")
            cursor.execute(
                "DELETE FROM exams WHERE id = ? AND class_id = ?",
                (exam_id, class_id)
            )
            conn.commit()
            flash("Exam removed.")

        # ... Keep your other POST handlers here (students, lessons, notes)
        elif "name" in request.form:
            student_name = request.form.get("name")
            if student_name:
                cursor.execute(
                    "INSERT INTO students (name, class_id) VALUES (?, ?)",
                    (student_name, class_id)
                )
                conn.commit()
                flash(f"{student_name} added to students!")

        # Remove Student
        elif "remove_id" in request.form:
            student_id = request.form.get("remove_id")

            # Fetch the student name first
            student_row = cursor.execute(
                "SELECT name FROM students WHERE id = ? AND class_id = ?",
                (student_id, class_id)
            ).fetchone()

            if student_row:
                student_name = student_row["name"]

                # Delete the student
                cursor.execute(
                    "DELETE FROM students WHERE id = ? AND class_id = ?",
                    (student_id, class_id)
                )
                conn.commit()

                flash(f"{student_name} removed from students!")
            else:
                flash("Student not found or unauthorized.")
        
        # Add Lesson Plan
        elif "lesson_content" in request.form:
            lesson_date = request.form.get("lesson_date")
            lesson_content = request.form.get("lesson_content")
            if lesson_content and lesson_date:
                cursor.execute(
                    "INSERT INTO lesson_plans (class_id, date, content) VALUES (?, ?, ?)",
                    (class_id, lesson_date, lesson_content)
                )
                conn.commit()
                flash("Lesson plan added.")

        # Remove Lesson Plan
        elif "remove_lesson_id" in request.form:
            lesson_id = request.form.get("remove_lesson_id")
            cursor.execute(
                "DELETE FROM lesson_plans WHERE id = ? AND class_id = ?",
                (lesson_id, class_id)
            )
            conn.commit()
            flash("Lesson plan removed.")

        # Add Class Note
        elif "class_note" in request.form:
            note_content = request.form.get("class_note")
            if note_content:
                cursor.execute(
                    "INSERT INTO class_notes (class_id, content) VALUES (?, ?)",
                    (class_id, note_content)
                )
                conn.commit()
                flash("Class note added.")

        # Remove Class Note
        elif "remove_class_note_id" in request.form:
            note_id = request.form.get("remove_class_note_id")
            cursor.execute(
                "DELETE FROM class_notes WHERE id = ? AND class_id = ?",
                (note_id, class_id)
            )
            conn.commit()
            flash("Class note removed.")
    # Fetch data for template
    students = cursor.execute(
        "SELECT * FROM students WHERE class_id = ? ORDER BY name", (class_id,)
    ).fetchall()
    students_with_notes = [(s, []) for s in students]  # Notes handled in student_detail

    lesson_plans = cursor.execute(
        "SELECT * FROM lesson_plans WHERE class_id = ? ORDER BY date DESC", (class_id,)
    ).fetchall()
    
    class_notes = cursor.execute(
        "SELECT * FROM class_notes WHERE class_id = ? ORDER BY created_at DESC", (class_id,)
    ).fetchall()
    
    exams = cursor.execute(
        "SELECT * FROM exams WHERE class_id = ? ORDER BY date DESC", (class_id,)
    ).fetchall()

    conn.close()
    return render_template(
        "class_detail.html",
        class_row=class_row,
        students_with_notes=students_with_notes,
        lesson_plans=lesson_plans,
        class_notes=class_notes,
        exams=exams
    )


@app.route("/exam/<int:exam_id>/add_scores", methods=["GET", "POST"])
def add_exam_scores(exam_id):
    conn, cursor = get_db_connection()

    # Get exam and class info
    exam = cursor.execute(
        "SELECT * FROM exams WHERE id = ?", (exam_id,)
    ).fetchone()
    if not exam:
        conn.close()
        flash("Exam not found.")
        return redirect("/class")

    # Verify teacher owns the class
    class_row = cursor.execute(
        "SELECT * FROM classes WHERE id = ? AND teacher_id = ?",
        (exam["class_id"], session["teacher_id"])
    ).fetchone()

    if not class_row:
        conn.close()
        flash("Unauthorized.")
        return redirect("/class")

    # Get all students in class
    students = cursor.execute(
        "SELECT * FROM students WHERE class_id = ?",
        (exam["class_id"],)
    ).fetchall()

    if request.method == "POST":
        for student in students:
            score = request.form.get(f"score_{student['id']}")
            if score:
                # Insert or update score
                existing = cursor.execute(
                    "SELECT * FROM exam_results WHERE exam_id = ? AND student_id = ?",
                    (exam_id, student['id'])
                ).fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE exam_results SET score = ? WHERE id = ?",
                        (score, existing["id"])
                    )
                else:
                    cursor.execute(
                        "INSERT INTO exam_results (exam_id, student_id, score) VALUES (?, ?, ?)",
                        (exam_id, student['id'], score)
                    )
        conn.commit()
        flash("Scores saved.")

        # refresh results after saving
        results = cursor.execute(
            "SELECT * FROM exam_results WHERE exam_id = ?",
            (exam_id,)
        ).fetchall()
        results_dict = {r["student_id"]: r["score"] for r in results}

        conn.close()
      
        return render_template("add_exam_scores.html", exam=exam, students=students, results=results_dict, class_row=class_row)

    # Get existing results
    results = cursor.execute(
        "SELECT * FROM exam_results WHERE exam_id = ?",
        (exam_id,)
    ).fetchall()
    results_dict = {r["student_id"]: r["score"] for r in results}

    conn.close()
    return render_template("add_exam_scores.html", exam=exam, students=students, results=results_dict, class_row=class_row)

@app.route("/class/<int:class_id>/exams/add", methods=["GET", "POST"])
def add_exam(class_id):
    conn, cursor = get_db_connection()
    class_row = cursor.execute(
        "SELECT * FROM classes WHERE id = ? AND teacher_id = ?",
        (class_id, session["teacher_id"])
    ).fetchone()
    if not class_row:
        conn.close()
        flash("Class not found or unauthorized.")
        return redirect("/class")

    if request.method == "POST":
        exam_name = request.form.get("name")
        exam_date = request.form.get("date")
        if not exam_name:
            flash("Exam name cannot be blank.")
            return render_template("add_exam.html", class_row=class_row)
        cursor.execute(
            "INSERT INTO exams (class_id, name, date) VALUES (?, ?, ?)",
            (class_id, exam_name, exam_date)
        )
        conn.commit()
        conn.close()
        flash("Exam added successfully.")
        return redirect(f"/class/{class_id}/exams")

    conn.close()
    return render_template("add_exam.html", class_row=class_row)

@app.route("/class/<int:class_id>/exams")
def class_exams(class_id):
    conn, cursor = get_db_connection()
    class_row = cursor.execute(
        "SELECT * FROM classes WHERE id = ? AND teacher_id = ?",
        (class_id, session["teacher_id"])
    ).fetchone()
    if not class_row:
        conn.close()
        flash("Class not found or unauthorized.")
        return redirect("/class")

    exams = cursor.execute(
        "SELECT * FROM exams WHERE class_id = ?",
        (class_id,)
    ).fetchall()
    conn.close()
    return render_template("class_exams.html", class_row=class_row, exams=exams)

@app.route("/exam/<int:exam_id>/results", methods=["GET", "POST"])
def exam_results(exam_id):
    
    conn, cursor = get_db_connection()
    exam = cursor.execute(
        "SELECT * FROM exams e JOIN classes c ON e.class_id = c.id WHERE e.id = ? AND c.teacher_id = ?",
        (exam_id, session["teacher_id"])
    ).fetchone()

    if not exam:
        conn.close()
        flash("Exam not found or unauthorized.")
        return redirect("/class")
    
    class_row = {
        "id": exam["class_id"],
        "name": exam["class_name"]
    }

    students = cursor.execute(
        "SELECT * FROM students WHERE class_id = ?",
        (exam["class_id"],)
    ).fetchall()

    if request.method == "POST":
        for student in students:
            score = request.form.get(f"score_{student['id']}")
            if score:
                # Update if exists, else insert
                existing = cursor.execute(
                    "SELECT * FROM exam_results WHERE exam_id = ? AND student_id = ?",
                    (exam_id, student["id"])
                ).fetchone()
                if existing:
                    cursor.execute(
                        "UPDATE exam_results SET score = ? WHERE id = ?",
                        (score, existing["id"])
                    )
                else:
                    cursor.execute(
                        "INSERT INTO exam_results (exam_id, student_id, score) VALUES (?, ?, ?)",
                        (exam_id, student["id"], score)
                    )
        conn.commit()
        conn.close()
        flash("Scores saved.")
        return redirect(f"/exam/{exam_id}/results")

    # Get existing results
    results = cursor.execute(
        "SELECT * FROM exam_results WHERE exam_id = ?",
        (exam_id,)
    ).fetchall()
    results_dict = {r["student_id"]: r["score"] for r in results}

    conn.close()
    return render_template("exam_results.html", exam=exam, students=students, results=results_dict, class_row=class_row)

@app.route("/student/<int:student_id>", methods=["GET", "POST"])
def student_detail(student_id):
    conn, cursor = get_db_connection()

    # Get student and verify class belongs to teacher
    student = cursor.execute(
        "SELECT s.*, c.teacher_id, c.id AS class_id, c.name AS class_name "
        "FROM students s JOIN classes c ON s.class_id = c.id "
        "WHERE s.id = ? AND c.teacher_id = ?",
        (student_id, session["teacher_id"])
    ).fetchone()

    if not student:
        conn.close()
        flash("Student not found or unauthorized.")
        return redirect("/class")

    # Get exams for the student's class
    exams = cursor.execute(
        "SELECT * FROM exams WHERE class_id = ?",
        (student["class_id"],)
    ).fetchall()

    # Get exam results for this student
    results = cursor.execute(
        "SELECT * FROM exam_results WHERE student_id = ?",
        (student_id,)
    ).fetchall()
    results_dict = {r["exam_id"]: r["score"] for r in results}
    # Get student notes
    student_notes = cursor.execute(
        "SELECT * FROM student_notes WHERE student_id = ? ORDER BY created_at DESC",
        (student_id,)
    ).fetchall()

    if request.method == "POST":
        if "remove_result_exam_id" in request.form:
            exam_id = request.form.get("remove_result_exam_id")
            cursor.execute(
                "DELETE FROM exam_results WHERE exam_id = ? AND student_id = ?",
                (exam_id, student_id)
            )
            conn.commit()
            flash("Exam result removed.")
            return redirect(f"/student/{student_id}")
   
  # Handle removing a note
    if request.method == "POST":
        if "student_note" in request.form:  # Add note
            content = request.form.get("student_note")
            if content:
                cursor.execute(
                     "INSERT INTO student_notes (student_id, content) VALUES (?, ?)",
                    (student_id, content)
                )
                conn.commit()
                flash("Note added.")
                return redirect(f"/student/{student_id}")

        elif "remove_note_id" in request.form:  # Remove note
            note_id = request.form.get("remove_note_id")
            cursor.execute(
                 "DELETE FROM student_notes WHERE id = ? AND student_id = ?",
                (note_id, student_id)
            )
            conn.commit()
            flash("Note removed.")
            return redirect(f"/student/{student_id}")   
            
    conn.close()
    return render_template(
        "student_detail.html",
        student=student,
        exams=exams,
        results=results_dict,
        student_notes=student_notes
)

if __name__ == "__main__":
    app.run(debug=True) 