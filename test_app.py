import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app import check_in_student, create_student, students_checked_in_today


class RosterTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.temp_dir.name) / "attendance_log.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_student_and_check_in(self):
        create_student(" Ada Lovelace ", " A001 ", self.data_file)
        timestamp = datetime(2026, 9, 21, 8, 15, tzinfo=timezone.utc)

        record = check_in_student("A001", "late", timestamp, self.data_file)

        self.assertEqual(record["status"], "Late")
        self.assertEqual(
            students_checked_in_today(timestamp.date(), self.data_file),
            [
                {
                    "student_id": "A001",
                    "name": "Ada Lovelace",
                    "status": "Late",
                    "timestamp": timestamp.isoformat(),
                }
            ],
        )

    def test_check_in_updates_same_student_for_same_day(self):
        create_student("Grace Hopper", "G001", self.data_file)
        timestamp = datetime(2026, 9, 21, 8, 15, tzinfo=timezone.utc)
        check_in_student("G001", "Late", timestamp, self.data_file)
        check_in_student(
            "G001",
            "Present",
            datetime(2026, 9, 21, 8, 30, tzinfo=timezone.utc),
            self.data_file,
        )

        with self.data_file.open(encoding="utf-8") as file:
            data = json.load(file)
        self.assertEqual(len(data["attendance"]), 1)
        self.assertEqual(data["attendance"][0]["status"], "Present")

    def test_duplicate_and_unknown_students_are_rejected(self):
        create_student("Alan Turing", "T001", self.data_file)
        with self.assertRaises(ValueError):
            create_student("Another Name", "T001", self.data_file)
        with self.assertRaises(ValueError):
            check_in_student("missing", data_file=self.data_file)


if __name__ == "__main__":
    unittest.main()
