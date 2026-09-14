import { CAREERS_ANCHOR } from "../../../../utils/global/Constants";

/* This card is the payoff for the claim made in the Home page's "Who We Are"
   block ("salaried, not commissioned") — keep the wording consistent if
   either is edited. */
export const hiringPolicy = {
  eyebrow: "How we hire",
  heading: "Salaried, not commissioned.",
  description:
    "Nobody at Marigold earns more by ordering a scan, admitting a patient overnight or recommending a procedure. Every clinician is on a flat salary with a fixed annual review. It is the single policy we're asked about most, and the one we'd defend hardest.",
  stats: [
    { id: "hiring-tenure", value: "9.2", label: "average years on staff" },
    { id: "hiring-turnover", value: "4%", label: "annual turnover" },
    {
      id: "hiring-ratio",
      value: "1:6",
      label: "nurse-to-patient ratio, day shift",
    },
  ],
};

export const hiringOpenings = {
  eyebrow: "Join us",
  heading: "Three posts open this quarter.",
  description:
    "We hire slowly and we keep people. If you'd rather practise medicine than meet targets, we'd like to hear from you.",
  jobs: [
    {
      id: "job-registrar",
      title: "Registrar, Internal Medicine",
      meta: "Full-time",
    },
    { id: "job-staff-nurse", title: "Staff nurse, Emergency", meta: "Two posts" },
    { id: "job-radiographer", title: "Radiographer", meta: "Part-time" },
  ],
  /* Points at the dedicated careers block on the contact page, not at the
     general enquiry form. */
  cta: { id: "hiring-cta", label: "See all openings", path: CAREERS_ANCHOR },
};
