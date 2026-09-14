import { BOOKING_ROUTE, ROUTES } from "../../../utils/global/Constants";

export const navItems = [
  { id: "nav-home", label: "Home", path: ROUTES.home },
  { id: "nav-about", label: "About Us", path: ROUTES.about },
  { id: "nav-team", label: "Our Team", path: ROUTES.team },
  { id: "nav-innovations", label: "Innovations", path: ROUTES.innovations },
  { id: "nav-contact", label: "Contact Us", path: ROUTES.contact },
];

export const navCta = {
  id: "nav-cta",
  label: "Book an Appointment",
  path: BOOKING_ROUTE,
};
