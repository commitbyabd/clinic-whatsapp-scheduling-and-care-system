/* Right-sized copies (npm run images:thumbs), not the 1254px masters —
   decoding the masters is what stopped the last portraits painting. */
const portrait = (file) => `/images/pages/our-team/nurses/w400/${file}`;

export const nursesIntro = {
  eyebrow: "A thank-you",
  heading: "Our nurses hold this place together.",
  description:
    "Doctors get the credit and the nameplates. The people who notice a fever at 3am, who explain the discharge notes twice, who sit with someone's mother so she isn't alone — they are these thirty. A few of them have been doing it here for longer than some of our doctors have been qualified.",
};

/**
 * Order matters: card width, portrait shape and vertical offset are all
 * derived from the index, so re-ordering this list changes the visual
 * rhythm of the wall. Six people, sized to sit on a single row at desktop
 * width, using all six portraits in public/images/pages/our-team/nurses.
 */
export const nursesData = [
  {
    id: "nurse-aguilar",
    name: "Rosa Aguilar",
    role: "Charge nurse, Ward B",
    yearsOfService: 14,
    photo: portrait("nurse-2.avif"),
  },
  {
    id: "nurse-kim",
    name: "Daniel Kim",
    role: "Emergency & triage",
    yearsOfService: null,
    photo: portrait("nurse-1-male.avif"),
  },
  {
    id: "nurse-noor",
    name: "Fatima Noor",
    role: "NICU",
    yearsOfService: null,
    photo: portrait("nurse-3.avif"),
  },
  {
    id: "nurse-bautista",
    name: "Michael Bautista",
    role: "Theatre scrub nurse",
    yearsOfService: 9,
    photo: portrait("nurse-6.avif"),
  },
  {
    id: "nurse-achieng",
    name: "Helen Achieng",
    role: "Outpatient clinics",
    yearsOfService: null,
    photo: portrait("nurse-4.avif"),
  },
  {
    id: "nurse-pillai",
    name: "Arjun Pillai",
    role: "Post-op recovery",
    yearsOfService: null,
    photo: portrait("nurse-5.avif"),
  },
];

export const nursesClosing = {
  quote:
    "“Thank you — for the shifts nobody sees, and the patience nobody bills for.”",
  attribution: ["On behalf of the doctors and directors", "of Marigold Health"],
};
