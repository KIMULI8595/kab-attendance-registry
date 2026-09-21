"""Command-line student attendance register."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("attendance_log.json")
VALID_STATUSES = {"Present", "Late"}


def _empty_data() -> dict[str, list[dict[str, Any]]]:
    return {"students": [], "attendance": []}


def load_data(data_file: Path = DATA_FILE) -> dict[str, list[dict[str, Any]]]:
    """Load the register, creating an empty structure when no file exists."""
    if not data_file.exists():
        return _empty_data()

    try:
        with data_file.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"{data_file} contains invalid JSON") from error

    if not isinstance(data, dict):
        raise ValueError("Attendance data must be a JSON object")

    students = data.get("students", [])
    attendance = data.get("attendance", [])
    if not isinstance(students, list) or not isinstance(attendance, list):
        raise ValueError("Attendance data must contain student and attendance lists")
    return {"students": students, "attendance": attendance}


def save_data(data: dict[str, list[dict[str, Any]]], data_file: Path = DATA_FILE) -> None:
    """Persist register data as readable JSON."""
    with data_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def create_student(
    name: str, student_id: str, data_file: Path = DATA_FILE
) -> dict[str, str]:
    """Create a student profile and reject duplicate or incomplete identities."""
    name = name.strip()
    student_id = student_id.strip()
    if not name or not student_id:
        raise ValueError("Name and student ID are required")

    data = load_data(data_file)
    if any(student["student_id"] == student_id for student in data["students"]):
        raise ValueError(f"Student ID {student_id} already exists")

    student = {"student_id": student_id, "name": name}
    data["students"].append(student)
    save_data(data, data_file)
    return student


def check_in_student(
    student_id: str,
    status: str = "Present",
    checked_in_at: datetime | None = None,
    data_file: Path = DATA_FILE,
) -> dict[str, str]:
    """Record or update one student's status for the current school day."""
    student_id = student_id.strip()
    status = status.strip().title()
    if status not in VALID_STATUSES:
        raise ValueError("Status must be Present or Late")

    data = load_data(data_file)
    student = next(
        (student for student in data["students"] if student["student_id"] == student_id),
        None,
    )
    if student is None:
        raise ValueError(f"No student found with ID {student_id}")

    timestamp = checked_in_at or datetime.now().astimezone()
    today = timestamp.date().isoformat()
    record = {
        "student_id": student_id,
        "date": today,
        "status": status,
        "timestamp": timestamp.isoformat(),
    }
    existing = next(
        (
            attendance
            for attendance in data["attendance"]
            if attendance["student_id"] == student_id
            and attendance["date"] == today
        ),
        None,
    )
    if existing is None:
        data["attendance"].append(record)
    else:
        existing.update(record)
    save_data(data, data_file)
    return record


def students_checked_in_today(
    today: date | None = None, data_file: Path = DATA_FILE
) -> list[dict[str, str]]:
    """Return today's checked-in students, ordered by check-in timestamp."""
    target_date = (today or date.today()).isoformat()
    data = load_data(data_file)
    students_by_id = {
        student["student_id"]: student["name"] for student in data["students"]
    }
    checked_in = [
        {
            "student_id": attendance["student_id"],
            "name": students_by_id.get(attendance["student_id"], "Unknown"),
            "status": attendance["status"],
            "timestamp": attendance["timestamp"],
        }
        for attendance in data["attendance"]
        if attendance["date"] == target_date
    ]
    return sorted(checked_in, key=lambda record: record["timestamp"])


def _print_today(data_file: Path = DATA_FILE) -> None:
    records = students_checked_in_today(data_file=data_file)
    if not records:
        print("No students have been checked in today.")
        return
    print("Students checked in today:")
    for record in records:
        print(f"- {record['name']} ({record['student_id']}): {record['status']}")


def run_cli(data_file: Path = DATA_FILE) -> None:
    """Run the roster menu used by the application entry point."""
    while True:
        print("\nKAB Student Attendance Register")
        print("1. Create student profile")
        print("2. Check in student")
        print("3. Show students checked in today")
        print("0. Exit")
        choice = input("Choose an option: ").strip()

        try:
            if choice == "1":
                student = create_student(
                    input("Student name: "), input("Student ID: "), data_file
                )
                print(f"Created profile for {student['name']} ({student['student_id']}).")
            elif choice == "2":
                record = check_in_student(
                    input("Student ID: "),
                    input("Status (Present/Late): ") or "Present",
                    data_file=data_file,
                )
                print(f"Recorded {record['status']} for {record['student_id']}.")
            elif choice == "3":
                _print_today(data_file)
            elif choice == "0":
                print("Goodbye.")
                return
            else:
                print("Please choose a valid option.")
        except (OSError, ValueError) as error:
            print(f"Error: {error}")


if __name__ == "__main__":
    run_cli()
