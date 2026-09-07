"""Per-deployment clinic facts, kept out of the response text in rules.py.

Every value is interpolated into a sentence, so it should read naturally there.

TODO: PHONE and EMAIL are still placeholders, fill them in before going live.
"""

# used as "Welcome to {NAME}", so lower-case unless it is a proper name
NAME = "the clinic"

ADDRESS = "123 Health St., Wellness City"

PHONE = "[clinic phone number]"
EMAIL = "[clinic email]"

# Interpolated as "please call {EMERGENCY_NUMBER}". The default keeps the
# generic wording; set it to a real number (e.g. "1122") for a deployment.
EMERGENCY_NUMBER = "your local emergency number"

OPENING_TIME = "9 AM"
CLOSING_TIME = "5 PM"
OPEN_DAYS = "Monday to Friday"

# Interpolated as "a variety of services including {SERVICES_SUMMARY}."
SERVICES_SUMMARY = (
    "general check-ups, specialist consultations, and emergency care"
)
