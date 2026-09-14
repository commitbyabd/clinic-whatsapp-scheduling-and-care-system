import * as Yup from "yup";
import { contactFormData } from "../../../../data/pages/contact-us/contact-form/ContactFormData";

const slugify = (value) =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

/**
 * Resolves the `?dept=` slug the Home symptom router sends here back to one
 * of the form's own department options.
 *
 * An unknown slug falls back to the first option ("Not sure — please
 * advise") rather than erroring — a stale or hand-typed link should still
 * land on a usable form.
 */
export const departmentFromSlug = (slug) => {
  const fallback = contactFormData.departments[0];
  if (!slug) return fallback;

  return (
    contactFormData.departments.find((name) => slugify(name) === slug) ??
    fallback
  );
};

export const buildInitialValues = (department) => ({
  name: "",
  phone: "",
  department: department ?? contactFormData.departments[0],
  message: "",
});

export const initialValues = buildInitialValues();

export const validationSchema = Yup.object({
  name: Yup.string().trim().required("Please tell us your name."),
  phone: Yup.string()
    .trim()
    .required("We need a phone number to reply to.")
    .min(7, "That number looks too short."),
  department: Yup.string().required("Please choose a department."),
  message: Yup.string()
    .trim()
    .required("Please tell us how we can help.")
    .min(10, "A little more detail will help us route this."),
});
