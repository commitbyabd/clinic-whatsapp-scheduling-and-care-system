export const symptomRouterData = {
  eyebrow: "Not sure who to see?",
  heading: "Tell us what's wrong, in your own words.",
  description:
    "Most people don't know whether a bad headache belongs to a neurologist, an ENT or a GP. You shouldn't have to. Pick what fits closest and we'll point you at the right department — or just book with General Medicine and let the doctor decide.",
  chipsLabel: "Common reasons people come in",
  resultLabel: "We'd start you with",
  cta: "Book this",
  /* This block is navigation, not triage, and must never be described as
     advice. The emergency line is deliberate — keep it. */
  emergencyNote: "If this is an emergency, call us or come straight in.",
};

/* Index 8 is the default selection on load — the result region must never
   be empty. `slug` is what travels to the contact form as ?dept=. */
export const DEFAULT_SYMPTOM_INDEX = 8;

export const symptomRoutes = [
  {
    id: "symptom-chest",
    label: "Chest pain or breathlessness",
    department: "Cardiology",
    slug: "cardiology",
    note: "Same-day ECG included. If it's sudden, call us instead of booking.",
  },
  {
    id: "symptom-child-fever",
    label: "A child with a fever",
    department: "Pediatrics",
    slug: "pediatrics",
    note: "Open daily 8am–6pm; under-2s are never made to wait.",
  },
  {
    id: "symptom-joint",
    label: "Joint or back pain",
    department: "Orthopedics",
    slug: "orthopedics",
    note: "X-ray on site, usually in the same visit.",
  },
  {
    id: "symptom-lump",
    label: "A lump or swelling",
    department: "General Surgery",
    slug: "general-surgery",
    note: "Ultrasound first, surgical opinion the same morning.",
  },
  {
    id: "symptom-pregnancy",
    label: "Pregnancy or period problems",
    department: "Gynecology",
    slug: "gynecology",
    note: "Mon, Wed and Sat. Female clinician on request.",
  },
  {
    id: "symptom-rash",
    label: "A rash or skin change",
    department: "Dermatology",
    slug: "dermatology",
    note: "Tue and Fri. Photos can be reviewed before you come in.",
  },
  {
    id: "symptom-tiredness",
    label: "Tiredness, thirst or weight change",
    department: "Internal Medicine",
    slug: "internal-medicine",
    note: "Bloods taken at the visit; results the same evening.",
  },
  {
    id: "symptom-ent",
    label: "Ear, throat or hearing trouble",
    department: "ENT",
    slug: "ent",
    note: "Wed and Sat, with audiology in the same corridor.",
  },
  {
    id: "symptom-unsure",
    label: "Honestly, I'm not sure",
    department: "General Medicine",
    slug: "general-medicine",
    note: "The safest starting point — we'll refer you on, free.",
  },
];
