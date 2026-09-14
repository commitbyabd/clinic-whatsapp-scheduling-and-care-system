import { missionData } from "../../../../data/pages/about-us/mission/MissionData";
import Container from "../../../ui/container/Container";
import styles from "./mission.module.css";

function Mission() {
  return (
    <section className={styles.section}>
      <Container maxWidth={980} className={styles.inner}>
        {/* The design sets the mission as a statement, not a heading — so the
            page's h1 is carried visually-hidden rather than dropped. */}
        <h1 className="srOnly">{missionData.pageTitle}</h1>

        <p className={styles.eyebrow}>{missionData.eyebrow}</p>
        <p className={styles.quote}>{missionData.quote}</p>
        <span className={styles.rule} aria-hidden="true" />
        <p className={styles.attribution}>{missionData.attribution}</p>
      </Container>
    </section>
  );
}

export default Mission;
