/* App-wide constants. Anything that appears in more than one place —
   the clinic's name, its contact details, its route table — lives here
   so there is one place to change it. */

export const COMPANY_NAME = "Marigold Health";
export const COMPANY_FULL_NAME = "Marigold Health Clinic & Medical Centre";
export const COMPANY_TAGLINE = "Clinic & Medical Centre";

/* The full brand lockup — mark, name and tagline in one image. Both are
   right-sized copies of /images/logo.avif made by npm run images:thumbs;
   the on-dark one has its lettering turned light for the charcoal footer. */
export const LOGO_SRC = "/images/logo/logo.avif";
export const LOGO_ON_DARK_SRC = "/images/logo/logo-on-dark.avif";
export const LOGO_WIDTH = 400;
export const LOGO_HEIGHT = 133;

/* One number, written three ways.

   E.164 is the international form with no punctuation at all — it is what
   both tel: and WhatsApp want, and the only form wa.me accepts. */
export const PHONE_DISPLAY = "+1 (415) 523-8886";
export const PHONE_E164 = "+14155238886";
export const PHONE_DIGITS = "14155238886";

/* A real phone call. Kept for the emergency line, where a chat app is the
   wrong thing to hand someone. */
export const PHONE_TEL_HREF = `tel:${PHONE_E164}`;

export const EMAIL = "care@marigold.health";
export const EMAIL_HREF = "mailto:care@marigold.health";

export const ADDRESS_STREET = "14 Alder Grove Road";
export const ADDRESS_CITY = "Fairmont, CA 94112";

/* WhatsApp deep link.

   wa.me/<digits> opens a chat with that account — the WhatsApp app on a
   phone, web.whatsapp.com on desktop. The number must be digits only, in
   international form: no +, spaces, dashes or brackets.

   ?text= prefills the message box. It is only ever a draft — the visitor
   still has to press send, and can edit or clear it first. It must be
   percent-encoded, which is what encodeURIComponent does. */
export const WHATSAPP_NUMBER = PHONE_DIGITS;
export const WHATSAPP_MESSAGE =
  "Hi Marigold Health — I'd like to book an appointment.";
export const WHATSAPP_HREF = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(
  WHATSAPP_MESSAGE,
)}`;

/* There is deliberately no generic PHONE_HREF: every place the number is
   linked has to say whether it dials (PHONE_TEL_HREF) or opens a chat
   (WHATSAPP_HREF). Publishing the number as a WhatsApp link is the default
   on this site, but the emergency line still dials. */

export const ROUTES = {
  home: "/",
  about: "/about-us",
  team: "/our-team",
  innovations: "/innovations",
  contact: "/contact-us",
};

/* Every "Book an appointment" CTA on the site points here. */
export const BOOKING_ROUTE = ROUTES.contact;

/* Recruitment lives in its own block on the contact page rather than the
   general enquiry form — "See all openings" on Our Team points here. */
export const CAREERS_ANCHOR_ID = "careers";
export const CAREERS_ANCHOR = `${ROUTES.contact}#${CAREERS_ANCHOR_ID}`;
