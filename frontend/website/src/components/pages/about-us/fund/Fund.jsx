import {
  fundActions,
  fundImage,
  fundIntro,
  fundStats,
  fundTestimonial,
} from "../../../../data/pages/about-us/fund/FundData";
import Button from "../../../ui/button/Button";
import LazyImage from "../../../ui/lazy-image/LazyImage";
import Reveal from "../../../ui/reveal/Reveal";
import SectionIntro from "../../../ui/section-intro/SectionIntro";
import FundStatCard from "./_components/FundStatCard";
import styles from "./fund.module.css";

/**
 * The emotional climax of the About page, and the only place terracotta is
 * allowed to own a whole block. Kept deliberately distinct from the sage
 * institutional sections above it.
 */
function Fund() {
  return (
    <section className={styles.section}>
      <Reveal className={styles.block}>
        <span className={`blob ${styles.circleLight}`} aria-hidden="true" />
        <span className={`blob ${styles.circleInk}`} aria-hidden="true" />

        <div className={styles.inner}>
          <SectionIntro
            tone="fund"
            eyebrow={fundIntro.eyebrow}
            heading={fundIntro.heading}
            description={fundIntro.description}
            className={styles.intro}
          />

          <div className={styles.grid}>
            <div className={styles.stats}>
              {fundStats.map((stat) => (
                <FundStatCard key={stat.id} {...stat} />
              ))}

              <blockquote className={styles.testimonial}>
                <p className={styles.quote}>{fundTestimonial.quote}</p>
                <footer className={styles.cite}>
                  {fundTestimonial.name}
                  <br />
                  {fundTestimonial.role}
                </footer>
              </blockquote>
            </div>

            <LazyImage
              src={fundImage.src}
              alt={fundImage.alt}
              className={styles.media}
            />
          </div>

          <div className={styles.actions}>
            <Button variant="white">{fundActions.primary.label}</Button>
            <Button variant="outlineOnFund">
              {fundActions.secondary.label}
            </Button>
            <span className={styles.note}>{fundActions.note}</span>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

export default Fund;
