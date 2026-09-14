import {
  carePathwayData,
  carePathwayIntro,
} from "../../../../data/pages/our-team/care-pathway/CarePathwayData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import PathwayStep from "./_components/PathwayStep";
import styles from "./care-pathway.module.css";

/**
 * Sits between the doctors grid and the nurses tribute — partly for the
 * content, partly for rhythm: it keeps the two photographic sections from
 * sitting back to back.
 */
function CarePathway() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.block}>
          <div className={styles.head}>
            <h2 className={styles.heading}>{carePathwayIntro.heading}</h2>
            <p className={styles.support}>{carePathwayIntro.description}</p>
          </div>

          <div className={styles.steps}>
            {carePathwayData.map((step) => (
              <PathwayStep key={step.id} {...step} />
            ))}
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

export default CarePathway;
