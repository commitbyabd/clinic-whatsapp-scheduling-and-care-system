export const carePathwayIntro = {
  heading: "How a case moves through this building.",
  description:
    "Most of what goes wrong in a hospital goes wrong in the handover. These four steps exist so yours doesn't.",
};

/* The numerals are decorative — the reading order is carried by the titles.
   Each step keeps a shortened line for the phone layout. */
export const carePathwayData = [
  {
    id: "pathway-clinician",
    index: "01",
    title: "One named clinician",
    description:
      "From your first visit, one doctor owns your case. You get their name, and it doesn't change when the shift does.",
    descriptionMobile:
      "One doctor owns your case, and it doesn't change when the shift does.",
  },
  {
    id: "pathway-board-round",
    index: "02",
    title: "Morning board round",
    description:
      "Every inpatient is discussed at 7:45am by the doctor, the charge nurse and the pharmacist together — not in three separate notes.",
    descriptionMobile:
      "Doctor, charge nurse and pharmacist discuss every inpatient together at 7:45am.",
  },
  {
    id: "pathway-cross-referral",
    index: "03",
    title: "Cross-referral in person",
    description:
      "If you need a second specialty, the two doctors speak before you're sent along. You should never have to repeat your own history.",
    descriptionMobile:
      "The two doctors speak before you're sent along — never repeat your own history.",
  },
  {
    id: "pathway-discharge",
    index: "04",
    title: "Discharge, explained twice",
    description:
      "Once by the doctor and once by your nurse, in plain language, with the follow-up already booked before you leave.",
    descriptionMobile:
      "Once by the doctor, once by your nurse, with the follow-up already booked.",
  },
];
