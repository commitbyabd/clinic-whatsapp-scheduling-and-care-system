import { Field, Form, Formik } from "formik";
import { useState } from "react";
import {
  careersData,
  careersRoleOptions,
} from "../../../../data/pages/contact-us/careers/CareersData";
import { CAREERS_ANCHOR_ID } from "../../../../utils/global/Constants";
import Button from "../../../ui/button/Button";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import styles from "./careers.module.css";
import { initialValues, validationSchema } from "./validation";

const { form } = careersData;
const { fields } = form;

function FieldError({ touched, error }) {
  if (!touched || !error) return null;

  return (
    <p className={styles.error} role="alert">
      {error}
    </p>
  );
}

/**
 * Recruitment gets its own block and its own form — "See all openings" on
 * Our Team lands here rather than on the general patient enquiry form.
 */
function Careers() {
  const [isSent, setIsSent] = useState(false);

  const handleSubmit = (_values, { setSubmitting }) => {
    setSubmitting(false);
    setIsSent(true);
  };

  return (
    <section className={styles.section} id={CAREERS_ANCHOR_ID}>
      <Container>
        <div className={styles.head}>
          <div>
            <p className={styles.eyebrow}>{careersData.eyebrow}</p>
            <h2 className={styles.heading}>{careersData.heading}</h2>
          </div>

          <p className={styles.support}>{careersData.description}</p>
        </div>

        <Reveal className={styles.layout}>
          <div className={styles.openings}>
            <h3 className={styles.openingsLabel}>
              {careersData.openingsLabel}
            </h3>

            <ul className={styles.jobs}>
              {careersData.jobs.map((job) => (
                <li key={job.id} className={styles.job}>
                  <span className={styles.jobTitle}>{job.title}</span>
                  <span className={styles.jobMeta}>{job.meta}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className={styles.panel}>
            {isSent ? (
              <div className={styles.success} role="status">
                <h3 className={styles.formHeading}>{form.success.heading}</h3>
                <p className={styles.helper}>{form.success.description}</p>
              </div>
            ) : (
              <>
                <h3 className={styles.formHeading}>{form.heading}</h3>
                <p className={styles.helper}>{form.helper}</p>

                <Formik
                  initialValues={initialValues}
                  validationSchema={validationSchema}
                  onSubmit={handleSubmit}
                >
                  {({ errors, touched, isSubmitting }) => (
                    <Form noValidate>
                      <div className={styles.grid}>
                        <div className={styles.field}>
                          <label
                            className={styles.label}
                            htmlFor={fields.name.id}
                          >
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
                          <FieldError
                            touched={touched.name}
                            error={errors.name}
                          />
                        </div>

                        <div className={styles.field}>
                          <label
                            className={styles.label}
                            htmlFor={fields.email.id}
                          >
                            {fields.email.label}
                          </label>
                          <Field
                            id={fields.email.id}
                            name="email"
                            type="email"
                            placeholder={fields.email.placeholder}
                            className={styles.input}
                            autoComplete="email"
                          />
                          <FieldError
                            touched={touched.email}
                            error={errors.email}
                          />
                        </div>

                        <div className={`${styles.field} ${styles.wide}`}>
                          <label
                            className={styles.label}
                            htmlFor={fields.role.id}
                          >
                            {fields.role.label}
                          </label>
                          <Field
                            as="select"
                            id={fields.role.id}
                            name="role"
                            className={styles.input}
                          >
                            {careersRoleOptions.map((role) => (
                              <option key={role} value={role}>
                                {role}
                              </option>
                            ))}
                          </Field>
                          <FieldError
                            touched={touched.role}
                            error={errors.role}
                          />
                        </div>

                        <div className={`${styles.field} ${styles.wide}`}>
                          <label
                            className={styles.label}
                            htmlFor={fields.message.id}
                          >
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
                          <FieldError
                            touched={touched.message}
                            error={errors.message}
                          />
                        </div>
                      </div>

                      <Button
                        as="button"
                        type="submit"
                        variant="gold"
                        className={styles.submit}
                        disabled={isSubmitting}
                      >
                        {form.submitLabel}
                      </Button>
                    </Form>
                  )}
                </Formik>

                <p className={styles.finePrint}>{form.finePrint}</p>
              </>
            )}
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

export default Careers;
