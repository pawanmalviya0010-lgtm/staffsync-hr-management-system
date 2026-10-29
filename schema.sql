CREATE DATABASE IF NOT EXISTS staffsync CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE staffsync;

CREATE TABLE IF NOT EXISTS departments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE,
  description VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS employees (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_code VARCHAR(30) NOT NULL UNIQUE,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  phone VARCHAR(30),
  department_id INT NULL,
  job_title VARCHAR(100),
  hire_date DATE NULL,
  salary DECIMAL(12,2) NOT NULL DEFAULT 0,
  status ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_employee_department FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('admin','employee') NOT NULL DEFAULT 'employee',
  employee_id INT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS attendance (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  attendance_date DATE NOT NULL,
  status ENUM('Present','Absent','Late','Half Day','Work From Home') NOT NULL DEFAULT 'Present',
  check_in TIME NULL,
  check_out TIME NULL,
  UNIQUE KEY uq_attendance_employee_date (employee_id, attendance_date),
  CONSTRAINT fk_attendance_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS leave_requests (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  leave_type ENUM('Casual','Sick','Annual','Unpaid','Other') NOT NULL DEFAULT 'Casual',
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  reason TEXT NOT NULL,
  status ENUM('Pending','Approved','Rejected') NOT NULL DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_leave_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS payroll (
  id INT AUTO_INCREMENT PRIMARY KEY,
  employee_id INT NOT NULL,
  pay_period CHAR(7) NOT NULL,
  basic_salary DECIMAL(12,2) NOT NULL DEFAULT 0,
  allowances DECIMAL(12,2) NOT NULL DEFAULT 0,
  deductions DECIMAL(12,2) NOT NULL DEFAULT 0,
  net_salary DECIMAL(12,2) NOT NULL DEFAULT 0,
  payment_status ENUM('Pending','Paid') NOT NULL DEFAULT 'Pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_payroll_employee FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

INSERT IGNORE INTO departments(name, description) VALUES
('Engineering','Software and technology'),
('Human Resources','People operations'),
('Finance','Finance and accounting'),
('Marketing','Brand and communications'),
('Operations','Daily operations');
