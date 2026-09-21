from reporting import chronic_absentees, mark_absent, today_absentees


def main():
    while True:
        print("\nKAB Attendance Register")
        print("1. Mark students absent")
        print("2. Show today's absentees")
        print("3. Show chronic absence report")
        print("4. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            student_ids = input("Student IDs, separated by commas: ").split(",")
            student_ids = [student_id.strip() for student_id in student_ids if student_id.strip()]
            mark_absent(student_ids)
            print(f"Marked {len(student_ids)} student(s) absent.")
        elif choice == "2":
            print("Today's absentees:", ", ".join(today_absentees()) or "None")
        elif choice == "3":
            student_ids = input("All student IDs, separated by commas: ").split(",")
            student_ids = [student_id.strip() for student_id in student_ids if student_id.strip()]
            total_days = int(input("Total school days: "))
            report = chronic_absentees(student_ids, total_days)
            if report:
                for student in report:
                    print(
                        f"{student['student_id']}: {student['attendance_rate']}% "
                        f"attendance, {student['missing_streak']}-day absence streak"
                    )
            else:
                print("No chronic absences found.")
        elif choice == "4":
            print("Goodbye.")
            return
        else:
            print("Please choose an option from 1 to 4.")


if __name__ == "__main__":
    main()