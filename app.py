"""Simple command-line student attendance register."""

import json
from datetime import date, datetime
from pathlib import Path


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


def show_today(data_file=DATA_FILE):
    students = students_checked_in_today(data_file=data_file)
    if not students:
        print("No students have been checked in today.")
        return

    print("Students checked in today:")
    for student in students:
        print(f"- {student['name']} ({student['student_id']}): {student['status']}")


def run_cli(data_file=DATA_FILE):
    """Run the roster menu."""
    while True:
        print("\n1. Create student profile")
        print("2. Check in student")
        print("3. Show today's check-ins")
        print("0. Exit")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                student = create_student(
                    input("Name: "), input("Student ID: "), data_file
                )
                print(f"Created {student['name']}.")
            elif choice == "2":
                record = check_in_student(
                    input("Student ID: "),
                    input("Status (Present/Late): ") or "Present",
                    data_file=data_file,
                )
                print(f"Recorded {record['status']}.")
            elif choice == "3":
                show_today(data_file)
            elif choice == "0":
                break
            else:
                print("Invalid option.")
        except (OSError, ValueError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    run_cli()
