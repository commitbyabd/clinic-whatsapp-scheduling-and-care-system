import { fundTeaserData } from "../../../../data/pages/home/fund-teaser/FundTeaserData";
import Button from "../../../ui/button/Button";
import Container from "../../../ui/container/Container";
import LazyImage from "../../../ui/lazy-image/LazyImage";
import Reveal from "../../../ui/reveal/Reveal";
import SectionIntro from "../../../ui/section-intro/SectionIntro";
import styles from "./fund-teaser.module.css";

function FundTeaser() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal as="article" className={styles.card}>
          <LazyImage
            src={fundTeaserData.image.src}
            alt={fundTeaserData.image.alt}
            className={styles.media}
          />

          <div className={styles.copy}>
            <SectionIntro
              tone="terracotta"
              eyebrow={fundTeaserData.eyebrow}
              heading={fundTeaserData.heading}
              headingWidth={440}
              className={styles.intro}
            />

            <p className={styles.description}>{fundTeaserData.description}</p>

            <Button
              to={fundTeaserData.cta.path}
              variant="terracotta"
              className={styles.cta}
            >
              {fundTeaserData.cta.label}
            </Button>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

export default FundTeaser;
