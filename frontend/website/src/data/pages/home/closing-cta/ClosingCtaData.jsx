import {
  PHONE_DISPLAY,
  ROUTES,
  WHATSAPP_HREF,
} from "../../../../utils/global/Constants";

export const closingCtaData = {
  heading: "Let's get you seen this week.",
  description:
    "Message us on WhatsApp and our assistant will find a slot in under a minute — or ask for a human any time.",
  primaryCta: {
    id: "closing-primary",
    label: "Book an appointment",
    path: ROUTES.contact,
  },
  secondaryCta: {
    id: "closing-secondary",
    label: PHONE_DISPLAY,
    href: WHATSAPP_HREF,
  },
};
