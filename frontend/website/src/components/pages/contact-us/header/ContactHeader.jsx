import { contactHeaderData } from "../../../../data/pages/contact-us/header/HeaderData";
import Container from "../../../ui/container/Container";
import styles from "./header.module.css";

function ContactHeader() {
  return (
    <section className={styles.section}>
      <Container className={styles.grid}>
        <div>
          <p className={styles.eyebrow}>{contactHeaderData.eyebrow}</p>
          <h1 className={styles.heading}>{contactHeaderData.heading}</h1>
        </div>

        <p className={styles.support}>{contactHeaderData.description}</p>
      </Container>
    </section>
  );
}

export default ContactHeader;
