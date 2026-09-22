import {
  ADDRESS_CITY,
  ADDRESS_STREET,
  COMPANY_FULL_NAME,
  EMAIL,
  EMAIL_HREF,
  PHONE_DISPLAY,
  PHONE_TEL_HREF,
  ROUTES,
  WHATSAPP_DISPLAY,
  WHATSAPP_HREF,
} from "../../../utils/global/Constants";

export const footerDescription =
  "A 120-bed multi-specialty clinic in Lahore, caring for this neighbourhood since 1994.";

export const footerColumns = [
  {
    id: "footer-visit",
    heading: "Visit",
    links: [
      { id: "footer-visit-home", label: "Home", path: ROUTES.home },
      { id: "footer-visit-about", label: "About Us", path: ROUTES.about },
      { id: "footer-visit-team", label: "Our Team", path: ROUTES.team },
      {
        id: "footer-visit-innovations",
        label: "Innovations",
        path: ROUTES.innovations,
      },
      { id: "footer-visit-contact", label: "Contact Us", path: ROUTES.contact },
    ],
  },
  {
    id: "footer-care",
    heading: "Care",
    links: [
      { id: "footer-care-departments", label: "Departments", path: ROUTES.team },
      {
        id: "footer-care-fund",
        label: "The Marigold Fund",
        path: ROUTES.about,
      },
      {
        id: "footer-care-portal",
        label: "Patient portal",
        path: ROUTES.innovations,
      },
      {
        id: "footer-care-telemedicine",
        label: "Telemedicine",
        path: ROUTES.innovations,
      },
      { id: "footer-care-emergency", label: "Emergency", href: PHONE_TEL_HREF },
    ],
  },
];

export const footerContact = {
  id: "footer-reach",
  heading: "Reach us",
  items: [
    { id: "footer-reach-phone", label: PHONE_DISPLAY, href: PHONE_TEL_HREF },
    {
      id: "footer-reach-whatsapp",
      label: `WhatsApp ${WHATSAPP_DISPLAY}`,
      href: WHATSAPP_HREF,
    },
    { id: "footer-reach-email", label: EMAIL, href: EMAIL_HREF },
    {
      id: "footer-reach-address",
      lines: [ADDRESS_STREET, ADDRESS_CITY],
    },
  ],
};

export const footerLegal = {
  copyright: `© 2026 ${COMPANY_FULL_NAME}`,
  /* No routes exist for these yet, so they render as plain text. */
  items: [
    { id: "legal-privacy", label: "Privacy" },
    { id: "legal-rights", label: "Patient rights" },
    { id: "legal-careers", label: "Careers" },
  ],
};
