"""
The intent table: what patients type, and what we say back.

This is the file you edit when you learn something new about how patients
phrase things. It holds no matching logic — response.py owns that — so adding
an intent here never risks breaking the engine.

ORDER IS LOAD-BEARING. Rules are evaluated top to bottom and the first match
wins, so a more specific intent must sit above a more generic one: "cancel my
appointment" contains the word "appointment", so appointment_cancel has to be
checked before the generic appointment rule. Every deliberate ordering choice
below carries a comment explaining why. If you reorder this dict, run
tests/test_response.py — it exists specifically to catch ordering regressions.

Clinic-specific facts (address, phone, hours) come from clinic.py rather than
being written into the response strings, so a clinic can move without this
file changing.
"""

from typing import TypedDict

from chatbot.predefined_responses import clinic


class RawRule(TypedDict):
    keywords: list[str]
    response: str


# Defined as constants because these two are used twice by the engine: once as
# a whole-message check that runs early, and once as a loose check that runs
# last. Sharing the lists keeps the two passes from drifting apart.
GREETING_KEYWORDS = [
    "hi",
    "hii",
    "hiii",
    "hello",
    "helo",
    "hey",
    "heya",
    "greetings",
    "salam",
    "salaam",
    "assalam",
    "assalamualaikum",
    "assalam o alaikum",
    "salam alaikum",
    "salaam alaikum",
    "aoa",
    "good morning",
    "good afternoon",
    "good evening",
]

FAREWELL_KEYWORDS = [
    "bye",
    "byee",
    "goodbye",
    "good bye",
    "see you",
    "take care",
    "thanks",
    "thank you",
    "thankyou",
    "thnx",
    "tysm",
    "jazakallah",
    "jazak allah",
    "jazakallahu khairan",
    "shukran",
    "shukriya",
    "shukriyaa",
    "allah hafiz",
    "khuda hafiz",
]

GREETING_RESPONSE = (
    f"Hello! Welcome to {clinic.NAME}. This is an automated system. "
    "How can we help you today?"
)
FAREWELL_RESPONSE = (
    "You're welcome! Take care, and message us anytime you need help."
)


RAW_RULES: dict[str, RawRule] = {
    # --- Safety-critical: always checked first ---
    # Broad on purpose. "urgent appointment" lands here rather than on the
    # booking rule, and that is the tradeoff we want: a false emergency reply
    # is recoverable, a missed one is not.
    "emergency": {
        "keywords": [
            "emergency",
            "emergencies",
            "urgent",
            "urgently",
            "ambulance",
            "severe pain",
            "chest pain",
            "can't breathe",
            "cant breathe",
            "cannot breathe",
            "not breathing",
            "difficulty breathing",
            "trouble breathing",
            "bleeding heavily",
            "heavy bleeding",
            "severe bleeding",
            "heart attack",
            "stroke",
            "unconscious",
            "fainted",
            "seizure",
            "overdose",
            "poisoned",
            "suicidal",
            "accident",
            "help me now",
        ],
        "response": (
            f"If this is a medical emergency, please call {clinic.EMERGENCY_NUMBER} "
            "or go to the nearest emergency room immediately. This chatbot "
            "cannot provide emergency care."
        ),
    },
    # --- Fees, checked before appointments on purpose ---
    # Fee questions almost always carry an appointment word ("how much for an
    # appointment?", "consultation fee"). Checking fees first means we answer
    # the question actually asked instead of replying with a booking prompt.
    "fees": {
        "keywords": [
            "fee",
            "fees",
            "consultation fee",
            "cost",
            "costs",
            "price",
            "prices",
            "charge",
            "charges",
            "rate",
            "rates",
            "how much",
            "payment",
            "pay",
        ],
        "response": (
            "Consultation fees vary by specialty. Please let us know which "
            "doctor or service you're asking about and we'll confirm the "
            "exact fee."
        ),
    },
    # --- Appointments (specific intents BEFORE the generic catch-all) ---
    # Confirm sits above cancel so "I don't want to cancel, just confirm"
    # resolves to the status check rather than the cancellation flow.
    "appointment_confirm": {
        "keywords": [
            "confirm",
            "confirms",
            "confirmed",
            "confirmation",
            "appointment status",
            "is my appointment",
            "check my appointment",
            "my booking",
        ],
        "response": (
            "Let us check that for you — please share your appointment "
            "reference or the phone number used to book."
        ),
    },
    "appointment_cancel": {
        "keywords": [
            "cancel",
            "cancels",
            "canceled",
            "cancelled",
            "cancellation",
            "cancelation",
            "reschedule",
            "re-schedule",
            "rescheduled",
            "rescheduling",
            "postpone",
            "postponed",
            "change my appointment",
            "change the appointment",
            "move my appointment",
            "shift my appointment",
        ],
        "response": (
            "To cancel or reschedule your appointment, please share your "
            "appointment reference or the date/time it was booked for."
        ),
    },
    # Symptom messages are an implicit booking request, so they are checked
    # before the generic appointment rule.
    "feeling_unwell": {
        "keywords": [
            "not feeling well",
            "not feeling good",
            "feeling unwell",
            "feeling sick",
            "feel sick",
            "sick",
            "ill",
            "unwell",
            "fever",
            "cough",
            "coughing",
            "cold",
            "flu",
            "pain",
            "headache",
            "sore throat",
            "vomiting",
            "nausea",
            "diarrhea",
            "diarrhoea",
            "infection",
        ],
        "response": (
            "We understand you're not feeling well and are very sad to hear "
            "that. To book an appointment, please provide your preferred date "
            "and time."
        ),
    },
    "appointment": {
        "keywords": [
            "appointment",
            "appointments",
            "book",
            "booked",
            "booking",
            "bookings",
            "schedule",
            "scheduling",
            "slot",
            "slots",
            "availability",
            "visit",
            "consultation",
            "see a doctor",
            "see the doctor",
        ],
        "response": (
            "To book an appointment, please provide your preferred date and "
            "time."
        ),
    },
    # --- Clinic info ---
    "doctor_info": {
        "keywords": [
            "doctor",
            "doctors",
            "dr",
            "physician",
            "specialist",
            "specialists",
            "consultant",
            "consultants",
            "surgeon",
            "dentist",
            "which doctor",
        ],
        "response": (
            "We have a team of experienced doctors. Please specify the "
            "specialty you are looking for."
        ),
    },
    # Bare "open"/"close" matched far too much ("can you open my file"), so
    # these are phrase-based instead.
    "clinic_hours": {
        "keywords": [
            "hours",
            "working hours",
            "working days",
            "opening hours",
            "opening time",
            "opening times",
            "closing time",
            "timing",
            "timings",
            "what time do you open",
            "what time do you close",
            "when do you open",
            "when do you close",
            "are you open",
            "still open",
            "open now",
            "open today",
            "open tomorrow",
            "open on",
            "closed on",
            "off day",
        ],
        "response": (
            f"Our clinic is open from {clinic.OPENING_TIME} to "
            f"{clinic.CLOSING_TIME}, {clinic.OPEN_DAYS}."
        ),
    },
    # Bare "where" matched things like "where do I send my report", so the
    # location-specific phrasings are spelled out.
    "location": {
        "keywords": [
            "location",
            "address",
            "branch",
            "where are you",
            "where is the clinic",
            "where is your clinic",
            "where are you located",
            "how do i get there",
            "how to reach",
            "directions",
            "map",
            "google map",
            "google maps",
        ],
        "response": f"We are located at {clinic.ADDRESS}.",
    },
    "insurance": {
        "keywords": [
            "insurance",
            "insured",
            "coverage",
            "covered",
            "panel",
            "policy",
            "claim",
            "reimbursement",
        ],
        "response": (
            "We accept a number of insurance providers. Please share your "
            "provider's name and we'll confirm your coverage."
        ),
    },
    "contact": {
        "keywords": [
            "phone number",
            "contact number",
            "contact details",
            "contact you",
            "call you",
            "your number",
            "whatsapp number",
            "landline",
            "helpline",
            "reach you",
            "email",
            "e-mail",
        ],
        "response": (
            f"You can reach us directly at {clinic.PHONE} or {clinic.EMAIL}."
        ),
    },
    "human_agent": {
        "keywords": [
            "talk to someone",
            "talk to a person",
            "speak to someone",
            "speak to a person",
            "human",
            "real person",
            "representative",
            "agent",
            "receptionist",
            "operator",
            "customer service",
            "customer support",
        ],
        "response": (
            "Sure, connecting you to a member of our staff. Please hold on "
            "for a moment."
        ),
    },
    # Below human_agent, because "service" would otherwise swallow the
    # "customer service" request for a human. "care" on its own matched
    # "take care" and "I don't care", so it only appears in longer phrases.
    "services": {
        "keywords": [
            "service",
            "services",
            "treatment",
            "treatments",
            "checkup",
            "checkups",
            "check-up",
            "check-ups",
            "check up",
            "check ups",
            "medical care",
            "health care",
            "healthcare",
            "facilities",
            "what do you offer",
        ],
        "response": (
            f"We offer a variety of services including {clinic.SERVICES_SUMMARY}."
        ),
    },
    "help": {
        "keywords": [
            "help",
            "menu",
            "options",
            "commands",
            "what can you do",
            "what do you do",
            "how does this work",
        ],
        "response": (
            "I can help you book an appointment, check clinic hours and "
            "location, find a doctor, or answer questions about our services "
            "and fees. What do you need?"
        ),
    },
    # --- Loose small talk: last, so it only catches messages with no intent ---
    # Almost every real message opens with "hi" or closes with "thanks", so
    # checking these first would hijack the conversation: "Hi, I want to book
    # an appointment" is an appointment, not a greeting. A message that is
    # *only* a greeting is still caught early — see _STANDALONE_RULES in
    # response.py.
    "greeting": {
        "keywords": GREETING_KEYWORDS,
        "response": GREETING_RESPONSE,
    },
    "farewell": {
        "keywords": FAREWELL_KEYWORDS,
        "response": FAREWELL_RESPONSE,
    },
}
