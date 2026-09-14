import { hiringOpenings } from "../../our-team/hiring/HiringData";

export const careersData = {
  eyebrow: "Careers",
  heading: "Apply to work here.",
  description:
    "The posts below are the ones open this quarter. If none of them fit but you think you belong here, say so — we read everything that arrives.",
  openingsLabel: "Open this quarter",
  /* Single source of truth: the same list the Our Team hiring card shows,
     so the two can never drift apart. */
  jobs: hiringOpenings.jobs,
  form: {
    heading: "Send an application",
    helper:
      "This goes to the practice manager, not to the patient enquiry desk.",
    fields: {
      name: { id: "careers-name", label: "Your name", placeholder: "Rosa Aguilar" },
      email: {
        id: "careers-email",
        label: "Email",
        placeholder: "you@example.com",
      },
      role: { id: "careers-role", label: "Role you're applying for" },
      message: {
        id: "careers-message",
        label: "A note about you",
        placeholder:
          "Where you trained, what you're doing now, and why here.",
        rows: 4,
      },
    },
    otherRole: "Something else — I'll explain below",
    submitLabel: "Send application",
    finePrint:
      "Please don't attach documents here. If we'd like to take it further we'll ask for your CV and references by email.",
    success: {
      heading: "Thank you — that's with the practice manager.",
      description:
        "We read every application and reply either way, usually within two weeks.",
    },
  },
};

export const careersRoleOptions = [
  ...careersData.jobs.map((job) => job.title),
  careersData.form.otherRole,
];
