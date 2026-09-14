import { teamHeaderData } from "../../../../data/pages/our-team/header/HeaderData";
import Container from "../../../ui/container/Container";
import styles from "./header.module.css";

function TeamHeader() {
  return (
    <section className={styles.section}>
      <Container className={styles.inner}>
        <div>
          <p className={styles.eyebrow}>{teamHeaderData.eyebrow}</p>
          <h1 className={styles.heading}>{teamHeaderData.heading}</h1>
        </div>

        <p className={styles.support}>{teamHeaderData.description}</p>
      </Container>
    </section>
  );
}

export default TeamHeader;
