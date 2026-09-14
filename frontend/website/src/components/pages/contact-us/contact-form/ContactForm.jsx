import { Field, Form, Formik } from "formik";
import { useState } from "react";
import { useSearchParams } from "react-router";
import { contactFormData } from "../../../../data/pages/contact-us/contact-form/ContactFormData";
import Button from "../../../ui/button/Button";
import styles from "./contact-form.module.css";
import {
  buildInitialValues,
  departmentFromSlug,
  validationSchema,
} from "./validation";

const { fields } = contactFormData;

function FieldError({ touched, error }) {
  if (!touched || !error) return null;

  return (
    <p className={styles.error} role="alert">
      {error}
    </p>
  );
}

function ContactForm() {
  const [isSent, setIsSent] = useState(false);
  const [searchParams] = useSearchParams();

  /* The Home symptom router hands off the department it routed to as
     /contact-us?dept=<slug>; preselect it so the visitor does not have to
     pick again what they were just told. */
  const department = departmentFromSlug(searchParams.get("dept"));

  /* No backend is wired up yet — on submit the panel body is replaced with
     a confirmation in the same cream card rather than navigating away. */
  const handleSubmit = (_values, { setSubmitting }) => {
    setSubmitting(false);
    setIsSent(true);
  };

  if (isSent) {
    return (
      <div className={styles.panel}>
        <div className={styles.success} role="status">
          <h2 className={styles.heading}>
            {contactFormData.success.heading}
          </h2>
          <p className={styles.helper}>
            {contactFormData.success.description}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.panel}>
      <h2 className={styles.heading}>{contactFormData.heading}</h2>
      <p className={styles.helper}>{contactFormData.helper}</p>

      <Formik
        initialValues={buildInitialValues(department)}
        enableReinitialize
        validationSchema={validationSchema}
        onSubmit={handleSubmit}
      >
        {({ errors, touched, isSubmitting }) => (
          <Form noValidate>
            <div className={styles.grid}>
              <div className={styles.field}>
                <label className={styles.label} htmlFor={fields.name.id}>
                  {fields.name.label}
                </label>
                <Field
                  id={fields.name.id}
                  name="name"
                  type="text"
                  placeholder={fields.name.placeholder}
                  className={styles.input}
                  autoComplete="name"
                />
                <FieldError touched={touched.name} error={errors.name} />
              </div>

              <div className={styles.field}>
                <label className={styles.label} htmlFor={fields.phone.id}>
                  {fields.phone.label}
                </label>
                <Field
                  id={fields.phone.id}
                  name="phone"
                  type="tel"
                  placeholder={fields.phone.placeholder}
                  className={styles.input}
                  autoComplete="tel"
                />
                <FieldError touched={touched.phone} error={errors.phone} />
              </div>

              <div className={`${styles.field} ${styles.wide}`}>
                <label className={styles.label} htmlFor={fields.department.id}>
                  {fields.department.label}
                </label>
                <Field
                  as="select"
                  id={fields.department.id}
                  name="department"
                  className={styles.input}
                >
                  {contactFormData.departments.map((department) => (
                    <option key={department} value={department}>
                      {department}
                    </option>
                  ))}
                </Field>
                <FieldError
                  touched={touched.department}
                  error={errors.department}
                />
              </div>

              <div className={`${styles.field} ${styles.wide}`}>
                <label className={styles.label} htmlFor={fields.message.id}>
                  {fields.message.label}
                </label>
                <Field
                  as="textarea"
                  id={fields.message.id}
                  name="message"
                  rows={fields.message.rows}
                  placeholder={fields.message.placeholder}
                  className={`${styles.input} ${styles.textarea}`}
                />
                <FieldError touched={touched.message} error={errors.message} />
              </div>
            </div>

            <Button
              as="button"
              type="submit"
              variant="gold"
              className={styles.submit}
              disabled={isSubmitting}
            >
              {contactFormData.submitLabel}
            </Button>
          </Form>
        )}
      </Formik>

      <p className={styles.finePrint}>{contactFormData.finePrint}</p>
    </div>
  );
}

export default ContactForm;
