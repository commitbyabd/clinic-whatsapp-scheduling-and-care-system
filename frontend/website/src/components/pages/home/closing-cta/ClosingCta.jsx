import { closingCtaData } from "../../../../data/pages/home/closing-cta/ClosingCtaData";
import Button from "../../../ui/button/Button";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import { externalLinkProps } from "../../../../utils/global/Links";
import styles from "./closing-cta.module.css";

function ClosingCta() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.block}>
          <span className={`blob ${styles.circleSage}`} aria-hidden="true" />
          <span className={`blob ${styles.circleGold}`} aria-hidden="true" />

          <div className={styles.inner}>
            <h2 className={styles.heading}>{closingCtaData.heading}</h2>
            <p className={styles.description}>{closingCtaData.description}</p>

            <div className={styles.actions}>
              <Button
                to={closingCtaData.primaryCta.path}
                variant="goldOnDark"
                className={styles.primary}
              >
                {closingCtaData.primaryCta.label}
              </Button>

              <Button
                href={closingCtaData.secondaryCta.href}
                variant="outlineOnDark"
                {...externalLinkProps(closingCtaData.secondaryCta.href)}
              >
                {closingCtaData.secondaryCta.label}
              </Button>
            </div>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

export default ClosingCta;
