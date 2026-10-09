# Gemini AI answer evaluation
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
def evaluate_answer(question, answer):
    if not client:
        return {
            "score": 0,
            "feedback": "AI is not configured. Check your API key.",
            "suggestion": "Configure your Gemini API key."
        }

    if not answer.strip():
        return {
            "score": 0,
            "feedback": "No answer provided.",
            "suggestion": "Try answering the question."
        }

    prompt = f"""
    You are a technical interview evaluator.

    Question: {question}
    Candidate's answer: {answer}

    Evaluate correctness, relevance and clarity.
    Return:
    Score: a number out of 10
    Feedback: specific strengths and mistakes
    Suggestion: how to improve the answer
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return {
            "score": 0,
            "feedback": response.text,
            "suggestion": "Review the feedback and improve your answer."
        }

    except Exception as e:
        return {
            "score": 0,
            "feedback": f"AI evaluation failed: {e}",
            "suggestion": "Check the API key and try again."
        }
import os, json, sqlite3, hashlib, secrets, re
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, g

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-for-local-development')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_MODE = os.environ.get('DB_MODE', 'sqlite').lower()  # use mysql after setting MySQL credentials
SQLITE_PATH = os.path.join(BASE_DIR, 'mock_interview.db')

QUESTION_BANK = {
    'Python': [
        ('What is Python, and what are two of its key features?', 'Python is a high-level, interpreted programming language. Features include readable syntax, dynamic typing, a large standard library, and cross-platform support.'),
        ('What is the difference between a list and a tuple?', 'Lists are mutable; tuples are immutable. Lists use square brackets and tuples commonly use parentheses.'),
        ('What is a dictionary in Python?', 'A dictionary stores key-value pairs and is mutable. Keys must be hashable and unique.'),
        ('Explain mutable and immutable data types with examples.', 'Mutable objects can change in place, such as lists and dictionaries. Immutable examples include strings, integers, and tuples.'),
        ('What is the purpose of a function?', 'A function is a reusable block of code that can accept parameters and return a result.'),
        ('What is exception handling?', 'try and except handle runtime errors; finally can run cleanup code whether an exception occurs or not.'),
        ('What is the difference between == and is?', '== compares values, while is checks whether two references point to the same object.'),
        ('What is a list comprehension?', 'A concise way to create a list from an iterable, optionally applying an expression and condition.'),
        ('What is OOP? Name its main concepts.', 'Object-oriented programming organizes code around classes and objects. Common concepts include encapsulation, inheritance, polymorphism, and abstraction.'),
        ('What is the difference between append() and extend()?', 'append adds one item to a list; extend adds each item from an iterable.'),
    ],
    'SQL': [
        ('What is SQL used for?', 'SQL is used to define, query, insert, update, and manage data in relational databases.'),
        ('What is the difference between WHERE and HAVING?', 'WHERE filters rows before grouping; HAVING filters groups after GROUP BY.'),
        ('What is a primary key?', 'A primary key uniquely identifies each row and cannot contain NULL values.'),
        ('What is a foreign key?', 'A foreign key references a key in another or the same table and helps enforce referential integrity.'),
        ('Explain INNER JOIN and LEFT JOIN.', 'INNER JOIN returns matching rows; LEFT JOIN returns all left-table rows plus matching right-table rows.'),
        ('What does GROUP BY do?', 'GROUP BY groups rows with matching values so aggregate functions can be applied to each group.'),
        ('What is normalization?', 'Normalization structures relational tables to reduce redundant data and update anomalies.'),
        ('What is the difference between DELETE, TRUNCATE, and DROP?', 'DELETE removes selected rows, TRUNCATE removes all rows efficiently, and DROP removes the table itself.'),
        ('What is an aggregate function? Give examples.', 'Aggregate functions calculate a result from multiple rows, such as COUNT, SUM, AVG, MIN, and MAX.'),
        ('What is an index?', 'An index can speed up data retrieval but uses storage and can add overhead to writes.'),
    ],
    'HR': [
        ('Tell me about yourself.', 'Give a concise introduction covering your education, relevant skills, a project, and the role you want.'),
        ('Why should we hire you as a fresher?', 'Connect your fundamentals, willingness to learn, reliability, and practical project work to the role.'),
        ('What are your strengths?', 'Choose genuine strengths and support each with a brief example.'),
        ('What is one area you are improving?', 'Name a real but manageable development area and explain the concrete steps you are taking.'),
        ('Tell me about a challenge you faced and how you handled it.', 'Use a clear situation, action, and result; focus on your own contribution.'),
        ('How do you respond to feedback?', 'Explain that you listen, clarify expectations, apply feedback, and check whether your work improved.'),
        ('How do you prioritize multiple tasks?', 'Compare deadlines and impact, break work into steps, communicate risks, and track progress.'),
        ('Why do you want this role?', 'Link the responsibilities to your interests, current skills, and what you want to learn.'),
        ('Where do you see yourself in three years?', 'Describe realistic growth in skills, responsibility, and contribution without overpromising.'),
        ('Do you have any questions for us?', 'Ask about onboarding, team collaboration, success measures, or learning opportunities.'),
    ],
    'Web Development': [
        ('What is the difference between HTML, CSS, and JavaScript?', 'HTML structures content, CSS styles it, and JavaScript adds behavior and interactivity.'),
        ('What is semantic HTML?', 'Semantic elements such as header, nav, main, and article communicate the meaning of page sections.'),
        ('What is the CSS box model?', 'Each element consists of content, padding, border, and margin.'),
        ('What is responsive web design?', 'Responsive design adapts layout to different screens using flexible layouts, media queries, and scalable assets.'),
        ('What is the difference between id and class in CSS?', 'An id should uniquely identify an element; a class can be reused across multiple elements.'),
        ('What is the DOM?', 'The Document Object Model represents a web document as a tree that scripts can read and modify.'),
        ('What is an HTTP request?', 'It is a message sent by a client to a server to request a resource or perform an operation.'),
        ('What is the difference between GET and POST?', 'GET typically retrieves data and sends parameters in the URL; POST typically submits data in the request body.'),
        ('What is a Flask route?', 'A route maps a URL and HTTP method to a Python view function.'),
        ('Why is input validation important?', 'It checks that submitted data is expected and safe before the application processes or stores it.'),
    ],
}


def connect_db():
    if DB_MODE == 'mysql':
        import mysql.connector
        return mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', '3306')),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            database=os.environ.get('MYSQL_DATABASE', 'ai_mock_interview'),
        )
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if DB_MODE == 'mysql':
        import mysql.connector
        # Database must exist first; create it using the included schema.sql.
        conn = connect_db()
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, email VARCHAR(190) NOT NULL UNIQUE, password_hash VARCHAR(255) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS interview_results (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, category VARCHAR(80) NOT NULL, total_questions INT NOT NULL, attempted INT NOT NULL, score INT NOT NULL, answers_json LONGTEXT NOT NULL, feedback_json LONGTEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))''')
        conn.commit(); cur.close(); conn.close()
        return
    conn = sqlite3.connect(SQLITE_PATH)
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS interview_results (
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
      category TEXT NOT NULL, total_questions INTEGER NOT NULL,
      attempted INTEGER NOT NULL, score INTEGER NOT NULL,
      answers_json TEXT NOT NULL, feedback_json TEXT NOT NULL,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    ''')
    conn.commit(); conn.close()


def query(sql, params=(), one=False):
    conn = connect_db()
    if DB_MODE == 'mysql':
        cur = conn.cursor(dictionary=True)
        cur.execute(sql.replace('?', '%s'), params)
        row = cur.fetchone() if one else cur.fetchall()
        cur.close(); conn.close()
        return row
    cur = conn.execute(sql, params)
    row = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return row


def execute(sql, params=()):
    conn = connect_db()
    if DB_MODE == 'mysql':
        cur = conn.cursor()
        cur.execute(sql.replace('?', '%s'), params)
        last_id = cur.lastrowid
        conn.commit(); cur.close(); conn.close()
        return last_id
    cur = conn.execute(sql, params)
    last_id = cur.lastrowid
    conn.commit(); conn.close()
    return last_id


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200_000).hex()
    return f'{salt}${digest}'


def verify_password(password, stored):
    try:
        salt, digest = stored.split('$', 1)
        return secrets.compare_digest(hash_password(password, salt).split('$', 1)[1], digest)
    except (ValueError, AttributeError):
        return False


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please sign in to start an interview.', 'info')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped


def score_answer(answer, model_answer):
    """Transparent offline rubric feedback, not an LLM-generated evaluation."""
    cleaned = re.findall(r"[a-zA-Z0-9+#]+", (answer or '').lower())
    reference = set(re.findall(r"[a-zA-Z0-9+#]+", model_answer.lower()))
    meaningful = {w for w in reference if len(w) > 2}
    overlap = len(set(cleaned) & meaningful) / max(1, len(meaningful))
    length_factor = min(len(cleaned) / 35, 1)
    score = round(min(100, overlap * 75 + length_factor * 25)) if cleaned else 0
    if not cleaned:
        feedback = 'No answer submitted. Try writing 2–4 clear sentences.'
    elif len(cleaned) < 8:
        feedback = 'Your answer is very brief. Add a definition, explanation, and a small example.'
    elif score >= 70:
        feedback = 'Good start. Your answer includes several relevant concepts. Make it stronger with a specific example.'
    elif score >= 40:
        feedback = 'Partially covered. Add the key terms and explain how the concept works.'
    else:
        feedback = 'Needs more detail. Start with a direct definition, then add the main points and an example.'
    return {'score': score, 'feedback': feedback, 'word_count': len(cleaned)}


@app.context_processor
def inject_globals():
    return {'current_user': session.get('user_name'), 'year': datetime.now().year}


@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return render_template('index.html', categories=list(QUESTION_BANK.keys()))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if len(name) < 2 or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email) or len(password) < 8:
            flash('Enter a valid name and email. Password must be at least 8 characters.', 'error')
            return render_template('auth.html', mode='register')
        try:
            uid = execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)', (name, email, hash_password(password)))
        except Exception:
            flash('That email may already be registered. Try signing in.', 'error')
            return render_template('auth.html', mode='register')
        session.update(user_id=uid, user_name=name, user_email=email)
        flash('Account created. You are ready to practise!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('auth.html', mode='register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = query('SELECT * FROM users WHERE email = ?', (email,), one=True)
        if user and verify_password(password, user['password_hash']):
            session.update(user_id=user['id'], user_name=user['name'], user_email=user['email'])
            return redirect(url_for('dashboard'))
        flash('Email or password is incorrect.', 'error')
    return render_template('auth.html', mode='login')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    results = query('SELECT * FROM interview_results WHERE user_id = ? ORDER BY id DESC LIMIT 8', (session['user_id'],))
    all_results = query('SELECT COUNT(*) AS total, COALESCE(AVG(score), 0) AS avg_score FROM interview_results WHERE user_id = ?', (session['user_id'],), one=True)
    return render_template('dashboard.html', categories=QUESTION_BANK, results=results, stats=all_results)


@app.route('/interview', methods=['GET', 'POST'])
@login_required
def interview():
    category = request.values.get('category', 'Python')
    if category not in QUESTION_BANK:
        category = 'Python'
    if request.method == 'POST':
        answers = [request.form.get(f'answer_{i}', '').strip() for i in range(len(QUESTION_BANK[category]))]
        feedback = [
            evaluate_answer(QUESTION_BANK[category][i][0], a)
            for i, a in enumerate(answers)
        ]
        attempted = sum(bool(a) for a in answers)
        score = round(sum(item['score'] for item in feedback) / len(feedback)) if feedback else 0
        result_id = execute('INSERT INTO interview_results (user_id, category, total_questions, attempted, score, answers_json, feedback_json) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (session['user_id'], category, len(answers), attempted, score, json.dumps(answers), json.dumps(feedback)))
        return redirect(url_for('result_detail', result_id=result_id))
    return render_template('interview.html', category=category, questions=[q[0] for q in QUESTION_BANK[category]], categories=list(QUESTION_BANK.keys()))


@app.route('/results/<int:result_id>')
@login_required
def result_detail(result_id):
    result = query('SELECT * FROM interview_results WHERE id = ? AND user_id = ?', (result_id, session['user_id']), one=True)
    if not result:
        flash('Result not found.', 'error')
        return redirect(url_for('dashboard'))
    answers = json.loads(result['answers_json'])
    feedback = json.loads(result['feedback_json'])
    questions = [q[0] for q in QUESTION_BANK.get(result['category'], [])]
    expected = [q[1] for q in QUESTION_BANK.get(result['category'], [])]
    return render_template('results.html', result=result, answers=answers, feedback=feedback, questions=questions, expected=expected)


@app.route('/history')
@login_required
def history():
    results = query('SELECT * FROM interview_results WHERE user_id = ? ORDER BY id DESC', (session['user_id'],))
    return render_template('history.html', results=results)


@app.route('/health')
def health():
    return {'status': 'ok', 'database_mode': DB_MODE}


init_db()
if __name__ == '__main__':
    app.run(debug=True)
