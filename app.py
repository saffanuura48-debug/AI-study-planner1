from flask import Flask, render_template, request, redirect, session, flash
import pyodbc

app = Flask(__name__)
app.secret_key = "studyplanner"


# =========================
# DATABASE CONNECTION
# =========================

conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=SAFFA;'
    'DATABASE=studyplanner;'
    'Trusted_Connection=yes;'
)


# =========================
# ADMIN CHECK
# =========================

def is_admin():

    if 'user' not in session:
        return False

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (session['user'],)
    )

    user = cursor.fetchone()

    if user and user[4]:

        if user[4].lower() == 'admin':
            return True

    return False


# =========================
# HOME PAGE
# =========================

@app.route('/')
def home():

    return render_template('index.html')


# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password,
                role,
                study_streak
            )

            VALUES(?,?,?,?,?)
            """,

            (
                name,
                email,
                password,
                'student',
                0
            )
        )

        conn.commit()

        return redirect('/login')

    return render_template('register.html')


# =========================
# USER LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=? AND password=?
            """,

            (
                email,
                password
            )
        )

        user = cursor.fetchone()

        if user:

            session['user'] = email

            return redirect('/dashboard')

    return render_template('login.html')


# =========================
# ADMIN LOGIN
# =========================

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=?
            AND password=?
            AND role='admin'
            """,

            (
                email,
                password
            )
        )

        admin = cursor.fetchone()

        if admin:

            session['user'] = email

            return redirect('/admin_dashboard')

    return render_template('admin_login.html')


# =========================
# USER DASHBOARD
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/login')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects")

    subjects = cursor.fetchall()

    return render_template(
        'dashboard.html',
        subjects=subjects
    )


# =========================
# ADMIN DASHBOARD
# =========================

@app.route('/admin_dashboard')
def admin_dashboard():

    if not is_admin():
        return redirect('/admin_login')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM subjects")
    subjects = cursor.fetchall()

    return render_template(
        'admin_dashboard.html',
        users=users,
        subjects=subjects
    )


# =========================
# ADD SUBJECT
# =========================

@app.route('/add_subject', methods=['POST'])
def add_subject():

    subject = request.form['subject']
    difficulty = request.form['difficulty']
    exam_date = request.form['exam_date']
    hours = request.form['hours']
    progress = request.form['progress']
    reminder = request.form['reminder']

    ai_tip = ""

    if difficulty == "Hard":

        ai_tip = "Study this subject daily"

    elif difficulty == "Medium":

        ai_tip = "Revise this subject regularly"

    else:

        ai_tip = "Easy subject keep practicing"

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO subjects
        (
            subject_name,
            difficulty,
            exam_date,
            study_hours,
            progress,
            reminder,
            ai_tip,
            completed_hours
        )

        VALUES(?,?,?,?,?,?,?,?)
        """,

        (
            subject,
            difficulty,
            exam_date,
            hours,
            progress,
            reminder,
            ai_tip,
            0
        )
    )

    conn.commit()

    return redirect('/dashboard')


# =========================
# DELETE SUBJECT
# =========================

@app.route('/delete/<int:id>')
def delete(id):

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM subjects WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect('/dashboard')


# =========================
# EDIT SUBJECT
# =========================

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    cursor = conn.cursor()

    if request.method == 'POST':

        subject = request.form['subject']
        difficulty = request.form['difficulty']
        exam_date = request.form['exam_date']
        hours = request.form['hours']
        progress = request.form['progress']
        reminder = request.form['reminder']

        cursor.execute(
            """
            UPDATE subjects

            SET
                subject_name=?,
                difficulty=?,
                exam_date=?,
                study_hours=?,
                progress=?,
                reminder=?

            WHERE id=?
            """,

            (
                subject,
                difficulty,
                exam_date,
                hours,
                progress,
                reminder,
                id
            )
        )

        conn.commit()

        return redirect('/dashboard')

    cursor.execute(
        "SELECT * FROM subjects WHERE id=?",
        (id,)
    )

    subject = cursor.fetchone()

    return render_template(
        'edit.html',
        subject=subject
    )


# =========================
# AI SCHEDULE
# =========================

@app.route('/schedule')
def schedule():

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects")

    subjects = cursor.fetchall()

    timetable = []

    for s in subjects:

        if s[2] == "Hard":

            hours = 4

        elif s[2] == "Medium":

            hours = 2

        else:

            hours = 1

        timetable.append({

            "subject": s[1],
            "hours": hours,
            "progress": s[5],
            "tip": s[7]

        })

    return render_template(
        'schedule.html',
        timetable=timetable
    )


# =========================
# NOTES
# =========================

@app.route('/notes', methods=['GET', 'POST'])
def notes():

    saved_note = ""

    if request.method == 'POST':

        note = request.form['note']

        with open("notes.txt", "w") as file:

            file.write(note)

        saved_note = note

    else:

        try:

            with open("notes.txt", "r") as file:

                saved_note = file.read()

        except:

            saved_note = ""

    return render_template(
        'notes.html',
        saved_note=saved_note
    )


# =========================
# NOTIFICATIONS
# =========================

@app.route('/notifications')
def notifications():

    return render_template('notifications.html')


# =========================
# TIMER
# =========================

@app.route('/timer')
def timer():

    return render_template('timer.html')


# =========================
# PROFILE
# =========================

@app.route('/profile')
def profile():

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (session['user'],)
    )

    user = cursor.fetchone()

    return render_template(
        'profile.html',
        user=user
    )


# =========================
# SETTINGS
# =========================

@app.route('/settings', methods=['GET', 'POST'])
def settings():

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        new_password = request.form['new_password']

        confirm_password = request.form['confirm_password']

        if new_password == confirm_password:

            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE users
                SET password=?
                WHERE email=?
                """,

                (
                    new_password,
                    session['user']
                )
            )

            conn.commit()

            flash("Password Updated Successfully")

    return render_template('settings.html')


# =========================
# ANALYTICS
# =========================

@app.route('/analytics')
def analytics():

    if not is_admin():
        return redirect('/admin_login')

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cursor.fetchone()[0]

    return render_template(
        'analytics.html',
        total_users=total_users,
        total_subjects=total_subjects
    )


# =========================
# REPORTS
# =========================

@app.route('/reports')
def reports():

    if not is_admin():
        return redirect('/admin_login')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects")

    subjects = cursor.fetchall()

    return render_template(
        'reports.html',
        subjects=subjects
    )


# =========================
# MANAGE USERS
# =========================

@app.route('/manage_users')
def manage_users():

    if not is_admin():
        return redirect('/admin_login')

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")

    users = cursor.fetchall()

    return render_template(
        'manage_users.html',
        users=users
    )


# =========================
# DELETE USER
# =========================

@app.route('/delete_user/<int:id>')
def delete_user(id):

    if not is_admin():
        return redirect('/admin_login')

    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id=?",
        (id,)
    )

    conn.commit()

    return redirect('/manage_users')


# =========================
# ADMIN SETTINGS
# =========================

@app.route('/admin_settings')
def admin_settings():

    if not is_admin():
        return redirect('/admin_login')

    return render_template(
        'admin_settings.html'
    )


# =========================
# ADMIN NOTIFICATIONS
# =========================

@app.route('/admin_notifications')
def admin_notifications():

    if not is_admin():
        return redirect('/admin_login')

    return render_template(
        'admin_notifications.html'
    )


# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# =========================
# RUN APP
# =========================

if __name__ == '__main__':

    app.run(debug=True)