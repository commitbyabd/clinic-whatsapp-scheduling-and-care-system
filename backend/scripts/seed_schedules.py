"""
Gives every active doctor without working hours a default week, so reception
can book them straight away. A doctor who already has hours is left alone,
so running this twice changes nothing.

Run it from backend/. It reads backend/.env, so it writes to the database
named there:

    .\\.venv\\Scripts\\python.exe scripts\\seed_schedules.py             add the week
    .\\.venv\\Scripts\\python.exe scripts\\seed_schedules.py --dry-run   only show what it would do
    .\\.venv\\Scripts\\python.exe scripts\\seed_schedules.py --replace   every doctor gets the week

--replace overwrites the hours doctors already have, but keeps their days
off. A doctor can change their hours afterwards on the portal's Working
hours tab.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import (  # noqa: E402
    close_mongo_connection,
    connect_to_mongo,
    get_database,
)
from app.features.doctor.v1.edit_doctor_schedule import (  # noqa: E402
    edit_doctor_schedule_query,
)
from app.schemas.doctor_schedule_update import DoctorScheduleUpdate  # noqa: E402

# Monday to Saturday, a morning and an evening clinic, Sunday off (0 is
# Monday, as the schedule API counts). Built through the API's own schema,
# so it passes the same checks as hours saved in the portal.
DEFAULT_WEEK = DoctorScheduleUpdate(
    working_hours=[
        {"day_of_week": day, "start_time": start, "end_time": end}
        for day in range(6)
        for start, end in (("09:00", "13:00"), ("17:00", "20:00"))
    ],
    slot_minutes=30,
)
DESCRIPTION = "Mon-Sat, 9 AM-1 PM and 5-8 PM, 30-minute visits"


async def seed(dry_run: bool, replace: bool) -> None:
    await connect_to_mongo()

    try:
        db = get_database()

        doctors = (
            await db.users.find(
                {"role": "doctor", "is_active": True},
                {"full_name": 1, "specialization": 1},
            )
            .sort("full_name", 1)
            .to_list(length=None)
        )

        # Any schedule at all counts, even an emptied one: that week was the
        # doctor's own choice.
        rows = await db.schedules.find({}, {"doctor_id": 1}).to_list(length=None)
        has_hours = {row["doctor_id"] for row in rows}

        changed = 0
        for doctor in doctors:
            name = f"{doctor.get('full_name')} ({doctor.get('specialization') or 'no specialization'})"
            existing = doctor["_id"] in has_hours

            if existing and not replace:
                print(f"left alone  {name}: already has working hours")
                continue

            fields = {
                "working_hours": DEFAULT_WEEK.model_dump()["working_hours"],
                "slot_minutes": DEFAULT_WEEK.slot_minutes,
                "is_active": True,
            }
            # a new schedule starts with no days off; a replaced one keeps
            # the days off already planned
            if not existing:
                fields["blackout_dates"] = []

            if not dry_run:
                # the same write the portal's Save makes
                await edit_doctor_schedule_query(str(doctor["_id"]), fields)

            changed += 1
            action = "replaced" if existing else "added"
            print(f"{'would be ' + action if dry_run else action:<11} {name}: {DESCRIPTION}")

        verb = "would get" if dry_run else "now have"
        print(f"\n{len(doctors)} active doctors, {changed} {verb} the default week")

    finally:
        await close_mongo_connection()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would change, write nothing"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="also replace the hours of doctors who have some, keeping days off",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.dry_run, args.replace))
