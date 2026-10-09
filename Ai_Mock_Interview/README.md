# MockMate — AI Mock Interview Platform

A beginner-friendly Flask project with registration/login, four interview categories, a one-question-at-a-time practice flow, answer feedback, a score summary, and saved interview history.

## Important about the feedback

This version uses a transparent **offline keyword-and-answer-length rubric**. It does not call itself a real AI model and does not require a paid API key. It is suitable as a first working version. A genuine LLM evaluation can be added later if a free/local model or API is configured.

## Run it on Windows

1. Open this folder in VS Code.
2. Open Terminal → New Terminal.
3. Create and activate a virtual environment (recommended):

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install requirements:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start the website:

   ```powershell
   python app.py
   ```

6. Open `http://127.0.0.1:5000` in your browser and create an account.

SQLite is the default, so the project works even while the MySQL password is being recovered. The database file `mock_interview.db` is created automatically in this folder.

## Switch to MySQL later

1. Open MySQL Workbench and run `schema.sql` after you regain access to MySQL.
2. In the VS Code terminal, set these variables for the current PowerShell window:

   ```powershell
   $env:DB_MODE="mysql"
   $env:MYSQL_HOST="localhost"
   $env:MYSQL_PORT="3306"
   $env:MYSQL_USER="root"
   $env:MYSQL_PASSWORD="YOUR_MYSQL_PASSWORD"
   $env:MYSQL_DATABASE="ai_mock_interview"
   python app.py
   ```

The app creates the two tables if they are missing. Keep your real password private and do not upload it to GitHub.

## Features

- Account registration and sign-in with salted PBKDF2 password hashes
- Python, SQL, HR, and Web Development practice categories (10 questions each)
- Previous/Next question navigation and answer word counts
- Results summary with per-question feedback and key-concept reference answers
- Dashboard stats and saved session history
- Responsive layout for laptop and mobile screens

## Project files

- `app.py` — Flask routes, database access, authentication, question bank and rubric feedback
- `templates/` — all HTML pages
- `static/style.css` — responsive styling
- `schema.sql` — MySQL database setup
