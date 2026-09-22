import { PHONE_DISPLAY } from "../../../../utils/global/Constants";

export const contactFormData = {
  heading: "Or send us a note",
  helper: "For non-urgent questions. If it's urgent, please call.",
  fields: {
    name: { id: "name", label: "Your name", placeholder: "Ayesha Khan" },
    phone: { id: "phone", label: "Phone", placeholder: "+92 300 1234567" },
    department: { id: "department", label: "Department" },
    message: {
      id: "message",
      label: "How can we help?",
      placeholder: "A short description of what you need.",
      rows: 4,
    },
  },
  /* Deliberately no medical-detail field — the fine print promises that
     records are only discussed by phone or in person. */
  departments: [
    "Not sure — please advise",
    "Cardiology",
    "Pediatrics",
    "Orthopedics",
    "General Surgery",
    "Gynecology",
    "Dermatology",
    "Internal Medicine",
    "ENT",
  ],
  submitLabel: "Send message",
  finePrint:
    "We never share your details. Medical records are only discussed over the phone or in person.",
  success: {
    heading: "Thank you — that's with us.",
    description: `Someone from the front desk will reply within one working day. If it can't wait, please call ${PHONE_DISPLAY}.`,
  },
};
