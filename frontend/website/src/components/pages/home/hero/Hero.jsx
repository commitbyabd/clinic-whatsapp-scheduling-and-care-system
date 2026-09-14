import { heroData } from "../../../../data/pages/home/hero/HeroData";
import Button from "../../../ui/button/Button";
import Chip from "../../../ui/chip/Chip";
import Container from "../../../ui/container/Container";
import LazyImage from "../../../ui/lazy-image/LazyImage";
import styles from "./hero.module.css";

function Hero() {
  return (
    <section className={styles.hero}>
      <span className={`blob ${styles.circle}`} aria-hidden="true" />

      <Container className={styles.grid}>
        <div className={styles.copy}>
          <Chip variant="sage" size="lg" dot>
            {heroData.badge}
          </Chip>

          <h1 className={styles.heading}>
            {heroData.heading.lead}{" "}
            <em className={styles.emphasis}>{heroData.heading.emphasis}</em>
          </h1>

          <p className={`${styles.lead} ${styles.leadDesktop}`}>
            {heroData.description}
          </p>
          <p className={`${styles.lead} ${styles.leadMobile}`}>
            {heroData.descriptionMobile}
          </p>

          <div className={styles.actions}>
            <Button to={heroData.primaryCta.path} variant="primary">
              {heroData.primaryCta.label}
            </Button>

            <Button
              to={heroData.secondaryCta.path}
              variant="outline"
              className={styles.secondaryDesktop}
            >
              {heroData.secondaryCta.label}
            </Button>

            <Button
              href={heroData.secondaryCtaMobile.href}
              variant="outline"
              target="_blank"
              rel="noopener"
              className={styles.secondaryMobile}
            >
              {heroData.secondaryCtaMobile.label}
            </Button>
          </div>

          <div className={styles.trust}>
            <div className={styles.avatars}>
              {heroData.trust.avatars.map((avatar) => (
                <LazyImage
                  key={avatar.id}
                  src={avatar.src}
                  alt={avatar.alt}
                  priority
                  className={styles.avatar}
                />
              ))}
            </div>

            <p className={styles.trustCopy}>
              {heroData.trust.lines.map((line, index) => (
                <span key={line}>
                  {line}
                  {index < heroData.trust.lines.length - 1 ? <br /> : null}
                </span>
              ))}
            </p>
          </div>
        </div>

        <div className={styles.media}>
          <LazyImage
            src={heroData.image.src}
            alt={heroData.image.alt}
            priority
            className={styles.image}
          />

          <div className={styles.reviews}>
            <p className={styles.score}>
              {heroData.reviews.score}
              <span className={styles.outOf}>{heroData.reviews.outOf}</span>
            </p>
            <p className={styles.reviewsLabel}>{heroData.reviews.label}</p>
          </div>
        </div>
      </Container>
    </section>
  );
}

export default Hero;
