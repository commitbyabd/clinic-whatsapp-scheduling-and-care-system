import {
  ADDRESS_CITY,
  ADDRESS_STREET,
  EMAIL,
  EMAIL_HREF,
  PHONE_DISPLAY,
  PHONE_TEL_HREF,
} from "../../../../utils/global/Constants";

/* WhatsApp has its own section on this page, so the phone card is the
   line that dials. */
export const detailsData = [
  {
    id: "detail-phone",
    label: "Phone",
    value: PHONE_DISPLAY,
    href: PHONE_TEL_HREF,
    note: "Reception · 24-hour emergency line",
  },
  {
    id: "detail-email",
    label: "Email",
    value: EMAIL,
    href: EMAIL_HREF,
    note: "Replies within one working day",
  },
  {
    id: "detail-address",
    label: "Address",
    lines: [ADDRESS_STREET, ADDRESS_CITY],
  },
];

/* Matches the chatbot's hours (backend/chatbot/predefined_responses/
   clinic.py) and the doctors' default week, which ends at 8pm on Saturday. */
export const hoursData = {
  id: "detail-hours",
  label: "Hours",
  rows: [
    { id: "hours-weekday", label: "OPD, Mon–Sat", value: "8am – 8pm" },
    { id: "hours-sunday", label: "OPD, Sunday", value: "Closed" },
    {
      id: "hours-emergency",
      label: "Emergency",
      value: "Always open",
      emphasis: true,
    },
  ],
};

/* Asset #28 in the handoff: "a real embed, or a static export styled to
   the palette". This is the latter — an invented map drawn in the site's
   colours, not a real location. Swap `src` for a real embed or export when
   the clinic has one. */
export const mapData = {
  src: "/images/pages/contact-us/map.svg",
  caption: "[ map embed ]",
  captionDetail: "14-B Main Boulevard · parking behind Gate 2",
  label: "Map of 14-B Main Boulevard, Gulberg III, Lahore — parking behind Gate 2",
};
