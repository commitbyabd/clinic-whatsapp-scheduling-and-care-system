import * as Yup from "yup";
import { careersRoleOptions } from "../../../../data/pages/contact-us/careers/CareersData";

export const initialValues = {
  name: "",
  email: "",
  role: careersRoleOptions[0],
  message: "",
};

export const validationSchema = Yup.object({
  name: Yup.string().trim().required("Please tell us your name."),
  email: Yup.string()
    .trim()
    .email("That doesn't look like an email address.")
    .required("We reply by email, so we need one."),
  role: Yup.string().required("Please choose a role."),
  message: Yup.string()
    .trim()
    .required("Please tell us a little about yourself.")
    .min(10, "A sentence or two is enough to start."),
});
