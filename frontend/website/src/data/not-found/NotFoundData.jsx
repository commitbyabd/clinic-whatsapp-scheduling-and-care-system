import { ROUTES } from "../../utils/global/Constants";

export const notFoundData = {
  eyebrow: "404",
  heading: "That page isn't here.",
  description:
    "The link may have moved or been retired. If you were trying to book, the fastest route is still a message — someone answers.",
  primary: { id: "not-found-primary", label: "Book an appointment", path: ROUTES.contact },
  secondary: { id: "not-found-secondary", label: "Back to home", path: ROUTES.home },
};
