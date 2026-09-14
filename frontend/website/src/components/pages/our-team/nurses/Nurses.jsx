import {
  nursesClosing,
  nursesData,
  nursesIntro,
} from "../../../../data/pages/our-team/nurses/NursesData";
import Reveal from "../../../ui/reveal/Reveal";
import SectionIntro from "../../../ui/section-intro/SectionIntro";
import NurseCard from "./_components/NurseCard";
import styles from "./nurses.module.css";

/* Card width, portrait shape and vertical offset are all derived from
   position in the list rather than stored per person. The irregularity is
   the point: this should read as a wall of photographs, not a directory. */
const CARD_WIDTHS = [168, 132, 148, 176, 136, 152, 140];
const MOBILE_WIDTHS = [122, 108, 122, 108, 122, 108, 122];
const SHAPES = ["circle", "dropBl", "dropTl"];

function Nurses() {
  return (
    <section className={styles.section}>
      <Reveal className={styles.block}>
        <span className={`blob ${styles.circle}`} aria-hidden="true" />

        <div className={styles.inner}>
          <SectionIntro
            tone="sage"
            eyebrow={nursesIntro.eyebrow}
            heading={nursesIntro.heading}
            description={nursesIntro.description}
            className={styles.intro}
          />

          <div className={styles.roster}>
            {nursesData.map((nurse, index) => (
              <NurseCard
                key={nurse.id}
                {...nurse}
                width={CARD_WIDTHS[index % CARD_WIDTHS.length]}
                mobileWidth={MOBILE_WIDTHS[index % MOBILE_WIDTHS.length]}
                shape={SHAPES[index % SHAPES.length]}
                offset={index % 2 === 1}
              />
            ))}
          </div>

          <div className={styles.closing}>
            <p className={styles.quote}>{nursesClosing.quote}</p>
            <p className={styles.attribution}>
              {nursesClosing.attribution.map((line, index) => (
                <span key={line}>
                  {line}
                  {index < nursesClosing.attribution.length - 1 ? <br /> : null}
                </span>
              ))}
            </p>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

export default Nurses;
