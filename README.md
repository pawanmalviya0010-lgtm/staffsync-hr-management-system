# StaffSync — HR Management System

A college major-project starter built with **Python Flask + MySQL**.

## Features in this working starter
- Session-based login with hashed passwords and admin/employee roles
- Admin dashboard with employee, department, pending leave, and attendance counts
- Employee create, list, search, edit, and delete
- Attendance recording and history
- Employee leave requests and admin approval/rejection
- Payroll entry and role-aware payroll list
- Parameterized SQL queries and basic form validation

## Requirements
- Python 3.10+
- MySQL Server 8+
- pip

## Setup (Windows)
1. Install Python and MySQL Server. During MySQL setup, remember your database password.
2. Open MySQL Workbench or a terminal and run `schema.sql`.
   - Workbench: open the file, connect to your local server, and execute it.
   - Terminal: `mysql -u root -p < schema.sql`
3. Open a terminal in this project folder.
4. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Set database environment variables in the same terminal (replace the password):
   ```bat
   set DB_HOST=localhost
   set DB_USER=root
   set DB_PASSWORD=your_mysql_password
   set DB_NAME=staffsync
   set SECRET_KEY=change-this-to-a-long-random-value
   ```
7. Create your administrator:
   ```bash
   python seed_admin.py
   ```
   Enter an admin name, email, and password when prompted.
8. Start the server:
   ```bash
   python app.py
   ```
9. Visit `http://127.0.0.1:5000` and sign in with the admin credentials you created.

## Setup (macOS / Linux)
Use `source .venv/bin/activate`, then export variables:
```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD='your_mysql_password'
export DB_NAME=staffsync
export SECRET_KEY='change-this-to-a-long-random-value'
python seed_admin.py
python app.py
```

## Employee login
When an admin adds an employee, the starter creates an employee login if the email is not already used. The temporary password is `Welcome123!`. This is for local demonstration only; change it before real use. A password-change screen is not included yet.

## Main routes
- `/login`, `/logout`
- `/dashboard`
- `/employees` (admin)
- `/employees/new` (admin)
- `/attendance`
- `/leave`
- `/payroll`

## Important project notes
- This is a learning/demo implementation, not production-ready HR software.
- Before real deployment, add CSRF protection, password reset/change, stronger validation, audit logging, pagination, secure cookie settings, and tests. Do not store real employee data until security hardening is complete.
- Payroll here is a recordkeeping example, not a statutory payroll/tax calculator.
