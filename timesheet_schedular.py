from datetime import date, timedelta
from collections import defaultdict

from database import SessionLocal
from timesheet_models import DraftTimesheet, Timesheet


def move_drafts_to_timesheet():

    db = SessionLocal()

    try:

        today = date.today()

        # ✅ Monday = 0, Sunday = 6
        # Skip Saturday & Sunday
        if today.weekday() >= 5:
            print("Weekend detected - scheduler skipped")
            return

        # ✅ Get today's drafts
        drafts = db.query(DraftTimesheet).filter(
            DraftTimesheet.work_date == today
        ).all()

        if not drafts:
            print("No drafts found")
            return

        # ✅ Group drafts by user
        grouped_drafts = defaultdict(list)

        for draft in drafts:
            grouped_drafts[draft.user_id].append(draft)

        # ✅ Process each user's drafts
        for user_id, user_drafts in grouped_drafts.items():

            # ✅ Skip if already submitted
            existing = db.query(Timesheet).filter(
                Timesheet.user_id == user_id,
                Timesheet.submitted_date == today
            ).first()

            if existing:
                print(f"Already submitted for user {user_id}")
                continue

            # ✅ Calculate today's total hours
            total_hours = round(
                sum(d.hours for d in user_drafts), 2
            )

            # ✅ Daily limit check
            if total_hours > 12:
                print(
                    f"User {user_id} exceeded daily limit "
                    f"with {total_hours} hours"
                )
                continue

            # ✅ Week range (Monday-Friday)
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=4)

            # ✅ Fetch weekly submitted timesheets
            weekly_timesheets = db.query(Timesheet).filter(
                Timesheet.user_id == user_id,
                Timesheet.submitted_date >= start_of_week,
                Timesheet.submitted_date <= end_of_week
            ).all()

            # ✅ Weekly hours
            weekly_hours = sum(
                t.total_hours for t in weekly_timesheets
            )

            weekly_total = weekly_hours + total_hours

            # ✅ Weekly limit check
            if weekly_total > 40:
                print(
                    f"User {user_id} exceeded weekly limit "
                    f"with {weekly_total} hours"
                )
                continue

            # ✅ Working days check
            working_days = set()

            for t in weekly_timesheets:
                working_days.add(t.submitted_date)

            working_days.add(today)

            if len(working_days) > 5:
                print(
                    f"User {user_id} exceeded 5 working days"
                )
                continue

            # ✅ Activities
            activities = []

            for d in user_drafts:

                activities.append({
                    "project_name": d.project_name,
                    "task_name": d.task_name,
                    "start_time": str(d.start_time),
                    "end_time": str(d.end_time),
                    "break_minutes": d.break_time,
                    "hours": d.hours
                })

            # ✅ Create timesheet
            timesheet = Timesheet(
                user_id=user_id,
                employee_id=user_drafts[0].user.employee_id,
                submitted_date=today,
                total_hours=total_hours,
                activities=activities
            )

            db.add(timesheet)

            print(
                f"Timesheet auto-submitted for user {user_id}"
            )

        db.commit()

    except Exception as e:

        db.rollback()

        print("Scheduler Error:", str(e))

    finally:

        db.close()
