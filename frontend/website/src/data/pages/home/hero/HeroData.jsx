import { ROUTES, WHATSAPP_HREF } from "../../../../utils/global/Constants";

export const heroData = {
  badge: "Accepting new patients",
  heading: {
    lead: "Care that knows",
    emphasis: "your name.",
  },
  description:
    "A 120-bed multi-specialty clinic where advanced medicine is delivered by people who sit down, listen, and stay until you understand.",
  /* The mobile layout carries a shorter version of the same line. */
  descriptionMobile:
    "A 120-bed multi-specialty clinic where advanced medicine comes with someone who sits down and listens.",
  primaryCta: {
    id: "hero-primary",
    label: "Book an appointment",
    path: ROUTES.contact,
  },
  secondaryCta: {
    id: "hero-secondary",
    label: "Why families choose us",
    path: ROUTES.about,
  },
  /* On mobile the second action becomes the WhatsApp escape hatch. */
  secondaryCtaMobile: {
    id: "hero-secondary-mobile",
    label: "WhatsApp us · 24/7",
    href: WHATSAPP_HREF,
  },
  image: {
    src: "/images/pages/home/home-hero.avif",
    alt: "A clinician sitting with a patient in natural window light",
  },
  reviews: {
    score: "4.9",
    outOf: "/5",
    label: "2,140 patient reviews",
  },
  trust: {
    /* Assets 4–6 in the handoff. Using clinicians from the Our Team roster,
       so the faces here are the same people a visitor meets on that page. */
    avatars: [
      {
        id: "trust-1",
        src: "/images/pages/our-team/doctors/w160/doc-4.avif",
        alt: "Dr. Lena Fischer, Pediatrics",
      },
      {
        id: "trust-2",
        src: "/images/pages/our-team/doctors/w160/doc-2-male.avif",
        alt: "Dr. Samuel Okafor, Orthopedics",
      },
      {
        id: "trust-3",
        src: "/images/pages/our-team/doctors/w160/doc-6.avif",
        alt: "Dr. Priya Menon, Gynecology",
      },
    ],
    lines: [
      "Same-week appointments with 20 resident specialists",
      "·  Open 24 hours for emergencies",
    ],
  },
};
