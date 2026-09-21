import json
from datetime import date, datetime
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs


DATA_FILE = Path(__file__).with_name("attendance_log.json")


def load_data(data_file=DATA_FILE):
    """Read the JSON register, or return an empty register."""
    if not data_file.exists():
        return {"students": [], "attendance": []}

    with data_file.open(encoding="utf-8") as register:
        return json.load(register)


def save_data(data, data_file=DATA_FILE):
    """Save the register to JSON."""
    with data_file.open("w", encoding="utf-8") as register:
        json.dump(data, register, indent=2)


def create_student(name, student_id, data_file=DATA_FILE):
    """Add a student profile."""
    name = name.strip()
    student_id = student_id.strip()
    if not name or not student_id:
        raise ValueError("Name and student ID are required")

    data = load_data(data_file)
    for student in data["students"]:
        if student["student_id"] == student_id:
            raise ValueError("That student ID already exists")

    student = {"student_id": student_id, "name": name}
    data["students"].append(student)
    save_data(data, data_file)
    return student


def check_in_student(
    student_id, status="Present", checked_in_at=None, data_file=DATA_FILE
):
    """Record or update one student's attendance for one day."""
    student_id = student_id.strip()
    status = status.strip().title()
    if status not in ("Present", "Late"):
        raise ValueError("Status must be Present or Late")

    data = load_data(data_file)
    if not any(s["student_id"] == student_id for s in data["students"]):
        raise ValueError("Student ID was not found")

    checked_in_at = checked_in_at or datetime.now().astimezone()
    record = {
        "student_id": student_id,
        "date": checked_in_at.date().isoformat(),
        "status": status,
        "timestamp": checked_in_at.isoformat(),
    }

    for attendance in data["attendance"]:
        if (
            attendance["student_id"] == student_id
            and attendance["date"] == record["date"]
        ):
            attendance.update(record)
            save_data(data, data_file)
            return record

    data["attendance"].append(record)
    save_data(data, data_file)
    return record


def students_checked_in_today(today=None, data_file=DATA_FILE):
    """Return the students checked in on the requested day."""
    today = (today or date.today()).isoformat()
    data = load_data(data_file)
    names = {student["student_id"]: student["name"] for student in data["students"]}

    result = []
    for attendance in data["attendance"]:
        if attendance["date"] == today:
            result.append(
                {
                    "student_id": attendance["student_id"],
                    "name": names[attendance["student_id"]],
                    "status": attendance["status"],
                    "timestamp": attendance["timestamp"],
                }
            )
    return sorted(result, key=lambda student: student["timestamp"])


def page(data_file=DATA_FILE, message=""):
    """Build the small attendance page."""
    data = load_data(data_file)
    rows = ""
    for student in students_checked_in_today(data_file=data_file):
        rows += (
            f"<tr><td>{escape(student['name'])}</td>"
            f"<td>{escape(student['student_id'])}</td>"
            f"<td>{escape(student['status'])}</td></tr>"
        )
    if not rows:
        rows = "<tr><td colspan='3'>No check-ins today.</td></tr>"

    options = "".join(
        f"<option value='{escape(student['student_id'])}'>"
        f"{escape(student['name'])} ({escape(student['student_id'])})</option>"
        for student in data["students"]
    )
    return f"""<!doctype html>
<html>
<head>
  <title>KAB Attendance Register</title>
  <style>
    body {{ font-family: Arial; max-width: 800px; margin: 40px auto; }}
    form {{ padding: 15px; margin: 15px 0; background: #f1f1f1; }}
    input, select, button {{ padding: 8px; margin: 4px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
  </style>
</head>
<body>
  <h1>KAB Student Attendance Register</h1>
  <p>{escape(message)}</p>
  <h2>Create student profile</h2>
  <form method="post" action="/student">
    <input name="name" placeholder="Student name" required>
    <input name="student_id" placeholder="Student ID" required>
    <button type="submit">Create student</button>
  </form>
  <h2>Record check-in</h2>
  <form method="post" action="/check-in">
    <select name="student_id" required>{options}</select>
    <select name="status">
      <option>Present</option>
      <option>Late</option>
    </select>
    <button type="submit">Record attendance</button>
  </form>
  <h2>Checked in today</h2>
  <table>
    <tr><th>Name</th><th>Student ID</th><th>Status</th></tr>
    {rows}
  </table>
</body>
</html>"""


def run_web_app(data_file=DATA_FILE, port=8000):
    """Start the local web application."""
    class AttendanceHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_page()

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            form = parse_qs(self.rfile.read(length).decode())
            try:
                if self.path == "/student":
                    create_student(
                        form.get("name", [""])[0],
                        form.get("student_id", [""])[0],
                        data_file,
                    )
                    message = "Student profile created."
                elif self.path == "/check-in":
                    check_in_student(
                        form.get("student_id", [""])[0],
                        form.get("status", ["Present"])[0],
                        data_file=data_file,
                    )
                    message = "Attendance recorded."
                else:
                    message = "Unknown form."
            except (OSError, ValueError) as error:
                message = f"Error: {error}"
            self.send_page(message)

        def send_page(self, message=""):
            content = page(data_file, message).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format, *args):
            return

    print(f"Attendance app running at http://localhost:{port}")
    HTTPServer(("localhost", port), AttendanceHandler).serve_forever()


if __name__ == "__main__":
    run_web_app()
