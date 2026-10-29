import os
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-development-secret")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "staffsync"),
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query(sql, params=(), one=False, commit=False):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        return cur.fetchone() if one else cur.fetchall()
    finally:
        cur.close()
        conn.close()

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    return {"current_year": datetime.now().year}

@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query("SELECT id, full_name, email, password_hash, role, employee_id FROM users WHERE email=%s", (email,), one=True)
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session.update(user_id=user["id"], name=user["full_name"], email=user["email"],
                           role=user["role"], employee_id=user["employee_id"])
            flash("Welcome back, " + user["full_name"] + "!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    if session["role"] == "admin":
        stats = {
            "employees": query("SELECT COUNT(*) n FROM employees WHERE status='Active'", one=True)["n"],
            "departments": query("SELECT COUNT(*) n FROM departments", one=True)["n"],
            "pending": query("SELECT COUNT(*) n FROM leave_requests WHERE status='Pending'", one=True)["n"],
            "today": query("SELECT COUNT(*) n FROM attendance WHERE attendance_date=%s AND status='Present'", (date.today(),), one=True)["n"],
        }
        recent = query("""SELECT e.employee_code, e.full_name, a.status, a.check_in
                          FROM attendance a JOIN employees e ON e.id=a.employee_id
                          WHERE a.attendance_date=%s ORDER BY a.id DESC LIMIT 6""", (date.today(),))
        return render_template("dashboard.html", stats=stats, recent=recent)
    employee = query("SELECT * FROM employees WHERE id=%s", (session.get("employee_id"),), one=True) if session.get("employee_id") else None
    attendance = query("SELECT attendance_date, status, check_in, check_out FROM attendance WHERE employee_id=%s ORDER BY attendance_date DESC LIMIT 5",
                       (employee["id"],)) if employee else []
    leaves = query("SELECT leave_type, start_date, end_date, status FROM leave_requests WHERE employee_id=%s ORDER BY id DESC LIMIT 5",
                   (employee["id"],)) if employee else []
    return render_template("dashboard.html", employee=employee, attendance=attendance, leaves=leaves)

@app.route("/employees")
@admin_required
def employees():
    search = request.args.get("q", "").strip()
    rows = query("""SELECT e.*, d.name department_name FROM employees e
                    LEFT JOIN departments d ON d.id=e.department_id
                    WHERE e.full_name LIKE %s OR e.employee_code LIKE %s OR e.email LIKE %s
                    ORDER BY e.id DESC""", (f"%{search}%", f"%{search}%", f"%{search}%"))
    return render_template("employees.html", employees=rows, search=search)

@app.route("/employees/new", methods=["GET", "POST"])
@admin_required
def employee_new():
    departments = query("SELECT * FROM departments ORDER BY name")
    if request.method == "POST":
        form = request.form
        try:
            employee_id = query("""INSERT INTO employees
                (employee_code, full_name, email, phone, department_id, job_title, hire_date, salary, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (form["employee_code"].strip(), form["full_name"].strip(), form["email"].strip().lower(),
                 form.get("phone","").strip(), form.get("department_id") or None, form.get("job_title","").strip(),
                 form.get("hire_date") or None, form.get("salary") or 0, form.get("status","Active")), commit=True)
            # Create employee login with temporary password if email is unique.
            if query("SELECT id FROM users WHERE email=%s", (form["email"].strip().lower(),), one=True) is None:
                query("INSERT INTO users (full_name,email,password_hash,role,employee_id) VALUES (%s,%s,%s,'employee',%s)",
                      (form["full_name"].strip(), form["email"].strip().lower(),
                       generate_password_hash("Welcome123!"), employee_id), commit=True)
            flash("Employee added. If a login was created, temporary password is Welcome123! Change it before real use.", "success")
            return redirect(url_for("employees"))
        except Error as exc:
            flash("Could not save employee. Check that employee code and email are unique. Details: " + str(exc), "danger")
    return render_template("employee_form.html", employee=None, departments=departments)

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@admin_required
def employee_edit(employee_id):
    employee = query("SELECT * FROM employees WHERE id=%s", (employee_id,), one=True)
    if not employee:
        abort(404)
    departments = query("SELECT * FROM departments ORDER BY name")
    if request.method == "POST":
        f = request.form
        query("""UPDATE employees SET employee_code=%s, full_name=%s, email=%s, phone=%s,
                 department_id=%s, job_title=%s, hire_date=%s, salary=%s, status=%s WHERE id=%s""",
              (f["employee_code"].strip(), f["full_name"].strip(), f["email"].strip().lower(),
               f.get("phone","").strip(), f.get("department_id") or None, f.get("job_title","").strip(),
               f.get("hire_date") or None, f.get("salary") or 0, f.get("status","Active"), employee_id), commit=True)
        flash("Employee updated.", "success")
        return redirect(url_for("employees"))
    return render_template("employee_form.html", employee=employee, departments=departments)

@app.route("/employees/<int:employee_id>/delete", methods=["POST"])
@admin_required
def employee_delete(employee_id):
    query("DELETE FROM employees WHERE id=%s", (employee_id,), commit=True)
    flash("Employee record deleted.", "success")
    return redirect(url_for("employees"))

@app.route("/attendance", methods=["GET", "POST"])
@login_required
def attendance():
    is_admin = session["role"] == "admin"
    if request.method == "POST":
        if not is_admin:
            abort(403)
        employee_id = request.form.get("employee_id")
        att_date = request.form.get("attendance_date") or date.today().isoformat()
        status = request.form.get("status", "Present")
        check_in = request.form.get("check_in") or None
        check_out = request.form.get("check_out") or None
        query("""INSERT INTO attendance (employee_id, attendance_date, status, check_in, check_out)
                 VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE status=VALUES(status),
                 check_in=VALUES(check_in), check_out=VALUES(check_out)""",
              (employee_id, att_date, status, check_in, check_out), commit=True)
        flash("Attendance saved.", "success")
        return redirect(url_for("attendance"))
    if is_admin:
        rows = query("""SELECT a.*, e.full_name, e.employee_code FROM attendance a
                        JOIN employees e ON e.id=a.employee_id ORDER BY a.attendance_date DESC, a.id DESC LIMIT 100""")
        staff = query("SELECT id, full_name, employee_code FROM employees WHERE status='Active' ORDER BY full_name")
    else:
        emp = query("SELECT id FROM employees WHERE id=%s", (session.get("employee_id"),), one=True) if session.get("employee_id") else None
        rows = query("""SELECT a.*, e.full_name, e.employee_code FROM attendance a JOIN employees e ON e.id=a.employee_id
                        WHERE a.employee_id=%s ORDER BY a.attendance_date DESC LIMIT 100""", (emp["id"],)) if emp else []
        staff = []
    return render_template("attendance.html", rows=rows, staff=staff, is_admin=is_admin, today=date.today().isoformat())

@app.route("/leave", methods=["GET", "POST"])
@login_required
def leave():
    if request.method == "POST":
        employee = query("SELECT id FROM employees WHERE id=%s", (session.get("employee_id"),), one=True)
        if not employee:
            flash("Your account is not linked to an employee profile. Ask an administrator.", "danger")
            return redirect(url_for("leave"))
        f = request.form
        query("""INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, reason)
                 VALUES (%s,%s,%s,%s,%s)""",
              (employee["id"], f["leave_type"], f["start_date"], f["end_date"], f["reason"].strip()), commit=True)
        flash("Leave request submitted.", "success")
        return redirect(url_for("leave"))
    if session["role"] == "admin":
        rows = query("""SELECT l.*, e.full_name, e.employee_code FROM leave_requests l
                        JOIN employees e ON e.id=l.employee_id ORDER BY l.id DESC""")
    else:
        rows = query("""SELECT l.*, e.full_name, e.employee_code FROM leave_requests l
                        JOIN employees e ON e.id=l.employee_id WHERE l.employee_id=%s ORDER BY l.id DESC""",
                     (session.get("employee_id"),))
    return render_template("leave.html", rows=rows, is_admin=session["role"] == "admin")

@app.route("/leave/<int:leave_id>/<decision>", methods=["POST"])
@admin_required
def leave_decision(leave_id, decision):
    if decision not in ("Approved", "Rejected"):
        abort(400)
    query("UPDATE leave_requests SET status=%s WHERE id=%s AND status='Pending'", (decision, leave_id), commit=True)
    flash("Leave request " + decision.lower() + ".", "success")
    return redirect(url_for("leave"))

@app.route("/payroll")
@login_required
def payroll():
    if session["role"] == "admin":
        rows = query("""SELECT p.*, e.full_name, e.employee_code FROM payroll p JOIN employees e ON e.id=p.employee_id
                        ORDER BY p.pay_period DESC, e.full_name""")
    else:
        rows = query("""SELECT p.*, e.full_name, e.employee_code FROM payroll p JOIN employees e ON e.id=p.employee_id
                        WHERE e.id=%s ORDER BY p.pay_period DESC""", (session.get("employee_id"),))
    staff = query("SELECT id, full_name, employee_code FROM employees WHERE status='Active' ORDER BY full_name") if session["role"] == "admin" else []
    if request.method == "POST":
        pass
    return render_template("payroll.html", rows=rows, staff=staff, is_admin=session["role"] == "admin")

@app.route("/payroll/create", methods=["POST"])
@admin_required
def payroll_create():
    f = request.form
    basic = float(f.get("basic_salary") or 0)
    allowance = float(f.get("allowances") or 0)
    deductions = float(f.get("deductions") or 0)
    if min(basic, allowance, deductions) < 0:
        flash("Amounts cannot be negative.", "danger")
    else:
        query("""INSERT INTO payroll (employee_id,pay_period,basic_salary,allowances,deductions,net_salary,payment_status)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)""",
              (f["employee_id"], f["pay_period"], basic, allowance, deductions, basic + allowance - deductions,
               f.get("payment_status","Pending")), commit=True)
        flash("Payroll entry created.", "success")
    return redirect(url_for("payroll"))

@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="The page or record could not be found."), 404

if __name__ == "__main__":
    app.run(debug=True)
