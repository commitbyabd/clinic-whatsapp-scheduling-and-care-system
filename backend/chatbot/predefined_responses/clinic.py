"""Per-deployment clinic facts, kept out of the response text in rules.py.

Every value is interpolated into a sentence, so it should read naturally there.
These match the public website (frontend/website/src/utils/global/Constants.jsx
and the contact page), so change both together.
"""

# used as "Welcome to {NAME}", so lower-case unless it is a proper name
NAME = "Marigold Health"

ADDRESS = "14-B Main Boulevard, Gulberg III, Lahore"

# The clinic's line for calls. Patients already reach the bot on WhatsApp,
# which for the demo is Twilio's sandbox number.
PHONE = "+92 42 3578 8886"
EMAIL = "care@marigold.health"

# Interpolated as "please call {EMERGENCY_NUMBER}": Rescue 1122, the
# emergency service in Punjab, where the clinic is.
EMERGENCY_NUMBER = "1122"

# read as "open from {OPENING_TIME} to {CLOSING_TIME}, {OPEN_DAYS}." The
# doctors' default week (scripts/seed_schedules.py) fits inside these.
OPENING_TIME = "8 AM"
CLOSING_TIME = "8 PM"
OPEN_DAYS = "Monday to Saturday"

# Interpolated as "a variety of services including {SERVICES_SUMMARY}."
SERVICES_SUMMARY = (
    "general check-ups, specialist consultations, and emergency care"
)
