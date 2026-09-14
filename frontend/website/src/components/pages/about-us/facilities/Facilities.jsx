import {
  facilitiesData,
  facilitiesIntro,
} from "../../../../data/pages/about-us/facilities/FacilitiesData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import FacilityCard from "./_components/FacilityCard";
import styles from "./facilities.module.css";

function Facilities() {
  return (
    <section className={styles.section}>
      <Container>
        <div className={styles.head}>
          <h2 className={styles.heading}>{facilitiesIntro.heading}</h2>
          <p className={styles.support}>{facilitiesIntro.description}</p>
        </div>

        <Reveal className={styles.grid}>
          {facilitiesData.map((facility) => (
            <FacilityCard key={facility.id} {...facility} />
          ))}
        </Reveal>
      </Container>
    </section>
  );
}

export default Facilities;
