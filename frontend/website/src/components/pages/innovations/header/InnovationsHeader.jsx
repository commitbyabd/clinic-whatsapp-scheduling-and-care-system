import { innovationsHeaderData } from "../../../../data/pages/innovations/header/HeaderData";
import Container from "../../../ui/container/Container";
import styles from "./header.module.css";

function InnovationsHeader() {
  return (
    <section className={styles.section}>
      <Container>
        <p className={styles.eyebrow}>{innovationsHeaderData.eyebrow}</p>

        <div className={styles.grid}>
          <h1 className={styles.heading}>{innovationsHeaderData.heading}</h1>
          <p className={styles.support}>{innovationsHeaderData.description}</p>
        </div>
      </Container>
    </section>
  );
}

export default InnovationsHeader;
