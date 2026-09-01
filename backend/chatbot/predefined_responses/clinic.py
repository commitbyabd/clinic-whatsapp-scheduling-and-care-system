"""
Per-deployment clinic facts.

These are the values that differ between clinics, or change without any code
logic changing — an address, a phone number, opening hours. They live here so
that moving the clinic or onboarding a second one is a config edit, not a
rewrite of the response text in rules.py.

Every value is a plain string that gets interpolated into a response, so the
defaults below are written to read naturally in a sentence. If you later want
these to come from environment variables, a settings file, or a per-tenant
database row, this module is the single place to change.

NOTE: PHONE and EMAIL are still placeholders — fill them in before going live.
"""

# Used as "Welcome to {NAME}." — keep it lower-case unless it is a proper name,
# so the sentence reads correctly.
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
