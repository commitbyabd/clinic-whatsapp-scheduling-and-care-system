// The departments the chatbot sends patients to, mirroring SPECIALIZATIONS
// in backend/chatbot/classifier.py. A doctor filed under one of these names
// is the one reception sees suggested, so the admin picks from this list.
// The server checks against its own copy and wins.
export const SPECIALIZATIONS = [
  "General Physician",
  "Dermatologist",
  "Pulmonologist",
  "Neurologist",
  "Orthopedist",
  "ENT Specialist",
  "Gynecologist",
  "Pediatrician",
  "General Surgeon",
  "Urologist",
  "Cardiologist",
  "Endocrinologist",
];
