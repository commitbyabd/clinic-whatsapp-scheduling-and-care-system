import {
  hiringOpenings,
  hiringPolicy,
} from "../../../../data/pages/our-team/hiring/HiringData";
import Button from "../../../ui/button/Button";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import styles from "./hiring.module.css";

function Hiring() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.pair}>
          <article className={styles.policy}>
            <p className={styles.eyebrow}>{hiringPolicy.eyebrow}</p>
            <h2 className={styles.heading}>{hiringPolicy.heading}</h2>
            <p className={styles.description}>{hiringPolicy.description}</p>

            <div className={styles.stats}>
              {hiringPolicy.stats.map((stat) => (
                <div key={stat.id}>
                  <p className={styles.statValue}>{stat.value}</p>
                  <p className={styles.statLabel}>{stat.label}</p>
                </div>
              ))}
            </div>
          </article>

          <article className={styles.openings}>
            <span className={`blob ${styles.circle}`} aria-hidden="true" />

            <div className={styles.openingsInner}>
              <p className={`${styles.eyebrow} ${styles.eyebrowOnDark}`}>
                {hiringOpenings.eyebrow}
              </p>
              <h2 className={`${styles.heading} ${styles.headingOnDark}`}>
                {hiringOpenings.heading}
              </h2>
              <p className={`${styles.description} ${styles.descriptionOnDark}`}>
                {hiringOpenings.description}
              </p>

              <ul className={styles.jobs}>
                {hiringOpenings.jobs.map((job) => (
                  <li key={job.id} className={styles.job}>
                    <span className={styles.jobTitle}>{job.title}</span>
                    <span className={styles.jobMeta}>{job.meta}</span>
                  </li>
                ))}
              </ul>

              <Button
                to={hiringOpenings.cta.path}
                variant="goldOnDark"
                className={styles.cta}
              >
                {hiringOpenings.cta.label}
              </Button>
            </div>
          </article>
        </Reveal>
      </Container>
    </section>
  );
}

export default Hiring;
