import {
  ADDRESS_CITY,
  ADDRESS_STREET,
  EMAIL,
  EMAIL_HREF,
  PHONE_DISPLAY,
  WHATSAPP_HREF,
} from "../../../../utils/global/Constants";

export const detailsData = [
  {
    id: "detail-phone",
    label: "Phone",
    value: PHONE_DISPLAY,
    href: WHATSAPP_HREF,
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

export const hoursData = {
  id: "detail-hours",
  label: "Hours",
  rows: [
    { id: "hours-weekday", label: "OPD, Mon–Fri", value: "8am – 8pm" },
    { id: "hours-saturday", label: "OPD, Saturday", value: "8am – 4pm" },
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
  captionDetail: "14 Alder Grove Road · parking behind Gate 2",
  label: "Map of 14 Alder Grove Road, Fairmont — parking behind Gate 2",
};
