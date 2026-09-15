"""Per-deployment clinic facts, kept out of the response text in rules.py.

Every value is interpolated into a sentence, so it should read naturally there.
These match the public website (frontend/website/src/utils/global/Constants.jsx
and the contact page), so change both together.
"""

# used as "Welcome to {NAME}", so lower-case unless it is a proper name
NAME = "Marigold Health"

ADDRESS = "14 Alder Grove Road, Fairmont, CA 94112"

PHONE = "+1 (415) 523-8886"
EMAIL = "care@marigold.health"

# Interpolated as "please call {EMERGENCY_NUMBER}". The default keeps the
# generic wording; set it to a real number (e.g. "1122") for a deployment.
EMERGENCY_NUMBER = "your local emergency number"

# read as "open from {OPENING_TIME} to {CLOSING_TIME}, {OPEN_DAYS}."
OPENING_TIME = "8 AM"
CLOSING_TIME = "8 PM"
OPEN_DAYS = "Monday to Friday, and until 4 PM on Saturday"

# Interpolated as "a variety of services including {SERVICES_SUMMARY}."
SERVICES_SUMMARY = (
    "general check-ups, specialist consultations, and emergency care"
)
