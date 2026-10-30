from flask import send_file
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__, static_folder='static')
app.secret_key = 'secret123'

conn = sqlite3.connect('tasks.db', check_same_thread=False)

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT NOT NULL,
    due_date TEXT,
    priority TEXT,
    category TEXT,
    complete INTEGER DEFAULT 0,
    username TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
''')

conn.commit()

@app.route('/', methods=['GET', 'POST'])
def home():

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        task = request.form["task"]

        due_date = request.form["due_date"]

        priority = request.form["priority"]

        category = request.form["category"]

        cursor.execute(
            '''
            INSERT INTO tasks
            (task, due_date, priority, category, username)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (
                task,
                due_date,
                priority,
                category,
                session['user']
            )
        )

        conn.commit()

        return redirect('/')

    search = request.args.get('search')
    sort = request.args.get('sort')
    priority = request.args.get('priority')
    category = request.args.get('category')
    due_date = request.args.get('due_date')

    query = """
    SELECT * FROM tasks
    WHERE username=?
    """

    params = [session['user']]

    if search:
        query += " AND task LIKE ?"
        params.append(f"%{search}%")

    if priority:
        query += " AND priority=?"
        params.append(priority)

    if category:
        query += " AND category=?"
        params.append(category)
    if due_date:
        query += " AND due_date=?"
        params.append(due_date)

    if sort == "date":
        query += " ORDER BY due_date ASC"

    elif sort == "latest":
        query += " ORDER BY id DESC"

    elif sort == "priority":
        query += """
            ORDER BY
            CASE
                WHEN priority='High' THEN 1
                WHEN priority='Medium' THEN 2
                WHEN priority='Low' THEN 3
            END
        """

    cursor.execute(query, params)
    tasks = cursor.fetchall()
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE username=?",
        (session['user'],)
    )
    total_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE username=? AND complete=1",
        (session['user'],)
    )
    completed_tasks = cursor.fetchone()[0]

    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)
    else:
        progress = 0
    return render_template(
    'index.html',
    tasks=tasks,
    username=session['user'],
    current_date=str(date.today()),
    progress=progress
)
@app.route('/delete/<int:id>')
def delete(id):

    if 'user' not in session:
        return redirect('/login')

    cursor.execute(
        '''
        DELETE FROM tasks
        WHERE id=? AND username=?
        ''',
        (
            id,
            session['user']
        )
    )

    conn.commit()

    return redirect('/')

    
@app.route('/complete/<int:id>')
def complete(id):

    if 'user' not in session:
        return redirect('/login')

    cursor.execute(
        '''
        UPDATE tasks
        SET complete = 1
        WHERE id=? AND username=?
        ''',
        (
            id,
            session['user']
        )
    )

    conn.commit()

    return redirect('/')

   
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        if user:
            return "Username already exists"

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )

        conn.commit()

        return redirect('/')

    return render_template('signup.html')
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor.execute(
            'SELECT * FROM users WHERE username=? AND password=?',
            (username, password)
        )

        user = cursor.fetchone()

        if user:

            session['user'] = username

            return redirect('/')

    return render_template('login.html')
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/login')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':

        task = request.form['task']
        due_date = request.form['due_date']
        priority = request.form['priority']
        category = request.form['category']

        cursor.execute(
            '''
            UPDATE tasks
            SET task=?, due_date=?, priority=?, category=?
            WHERE id=? AND username=?
            ''',
            (
                task,
                due_date,
                priority,
                category,
                id,
                session['user']
            )
        )

        conn.commit()

        return redirect('/')

    cursor.execute(
        '''
        SELECT *
        FROM tasks
        WHERE id=? AND username=?
        ''',
        (
            id,
            session['user']
        )
    )

    task = cursor.fetchone()

    return render_template(
        'edit.html',
        task=task
    )
    
@app.route('/pending')
def pending():

    if 'user' not in session:
        return redirect('/login')

    cursor.execute(
        '''
        SELECT * FROM tasks
        WHERE username=? AND complete=0
        ''',
        (session['user'],)
    )

    tasks = cursor.fetchall()
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE username=?",
        (session['user'],)
    )
    total_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE username=? AND complete=1",
        (session['user'],)
    )
    completed_tasks = cursor.fetchone()[0]

    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)
    else:
        progress = 0
    return render_template(
    "index.html",
    tasks=tasks,
    username=session["user"],
    current_date=str(date.today()),
    progress=progress
)

@app.route('/completed')
def completed():

    if 'user' not in session:
        return redirect('/login')

    cursor.execute(
        '''
        SELECT * FROM tasks
        WHERE username=? AND complete=1
        ''',
        (session['user'],)
    )

    tasks = cursor.fetchall()

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE username=?",
        (session['user'],)
    )
    total_tasks = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE username=? AND complete=1",
        (session['user'],)
    )
    completed_tasks = cursor.fetchone()[0]

    if total_tasks > 0:
        progress = int((completed_tasks / total_tasks) * 100)
    else:
        progress = 0

    return render_template(
        "index.html",
        tasks=tasks,
        username=session['user'],
        current_date=str(date.today()),
        progress=progress
    )
@app.route('/settings')
def settings():

    if 'user' not in session:
        return redirect('/login')

    return render_template(
        'index.html',
        tasks=[],
        username=session['user'],
        current_date=str(date.today()),
        progress=0
    )

@app.route("/export_pdf")
def export_pdf():

    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT task, due_date, priority, category
        FROM tasks
        WHERE username=?
        """,
        (session['user'],)
    )

    tasks = cursor.fetchall()
    conn.close()

    pdf_file = "tasks_report.pdf"

    doc = SimpleDocTemplate(pdf_file)
    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph("Cloud Task Manager Report", styles["Title"])
    )

    content.append(Spacer(1, 20))

    for task in tasks:

        text = (
            f"Task: {task[0]} | "
            f"Due: {task[1]} | "
            f"Priority: {task[2]} | "
            f"Category: {task[3]}"
        )

        content.append(Paragraph(text, styles["Normal"]))
        content.append(Spacer(1, 10))

    doc.build(content)

    return send_file(
        pdf_file,
        as_attachment=True
    )
if __name__ == '__main__':
    app.run(debug=True)