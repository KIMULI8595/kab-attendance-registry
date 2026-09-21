import json
from datetime import date
from pathlib import Path


DEFAULT_LOG_FILE = Path(__file__).with_name("attendance_log.json")


def load_records(log_file=DEFAULT_LOG_FILE):
    """Read attendance records from the local JSON file."""
    path = Path(log_file)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Attendance log must contain a JSON list.")
    return records


def save_records(records, log_file=DEFAULT_LOG_FILE):
    """Write attendance records to the local JSON file."""
    path = Path(log_file)
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)


def mark_absent(student_ids, school_day=None, log_file=DEFAULT_LOG_FILE):
    """Add or update an Absent record for each student for one school day."""
    attendance_date = school_day or date.today().isoformat()
    records = load_records(log_file)

    for student_id in student_ids:
        matching_record = next(
            (
                record
                for record in records
                if record.get("student_id") == student_id
                and record.get("date") == attendance_date
            ),
            None,
        )
        if matching_record:
            matching_record["status"] = "Absent"
            matching_record.pop("timestamp", None)
        else:
            records.append(
                {
                    "student_id": student_id,
                    "date": attendance_date,
                    "status": "Absent",
                }
            )

    save_records(records, log_file)
    return recordschro


def attendance_rate(student_id, total_school_days, log_file=DEFAULT_LOG_FILE):
    """Return a student's attendance percentage across recorded school days."""
    if total_school_days <= 0:
        raise ValueError("Total school days must be greater than zero.")

    records = load_records(log_file)
    present_days = {
        record.get("date")
        for record in records
        if record.get("student_id") == student_id
        and record.get("status") in {"Present", "Late"}
    }
    return (len(present_days) / total_school_days) * 100


def missing_streak(student_id, log_file=DEFAULT_LOG_FILE):
    """Return the longest consecutive Absent streak in the attendance log."""
    records = load_records(log_file)
    absent_dates = sorted(
        {
            date.fromisoformat(record["date"])
            for record in records
            if record.get("student_id") == student_id
            and record.get("status") == "Absent"
            and record.get("date")
        }
    )

    longest = current = 0
    previous_day = None
    for absent_day in absent_dates:
        if previous_day and absent_day == previous_day.fromordinal(previous_day.toordinal() + 1):
            current += 1
        else:
            current = 1
        longest = max(longest, current)
        previous_day = absent_day
    return longest


def chronic_absentees(student_ids, total_school_days, threshold=85, log_file=DEFAULT_LOG_FILE):
    """Return students whose attendance rate is below the given threshold."""
    students = []
    for student_id in student_ids:
        rate = attendance_rate(student_id, total_school_days, log_file)
        if rate < threshold:
            students.append(
                {
                    "student_id": student_id,
                    "attendance_rate": round(rate, 2),
                    "missing_streak": missing_streak(student_id, log_file),
                }
            )
    return students


def today_absentees(log_file=DEFAULT_LOG_FILE):
    """Return student IDs marked Absent today."""
    today = date.today().isoformat()
    return [
        record["student_id"]
        for record in load_records(log_file)
        if record.get("date") == today and record.get("status") == "Absent"
    ]