import { initiativesData } from "../../../../data/pages/innovations/initiatives/InitiativesData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import InitiativeCard from "./_components/InitiativeCard";
import styles from "./initiatives.module.css";

function Initiatives() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.grid}>
          {initiativesData.map((initiative) => (
            <InitiativeCard key={initiative.id} {...initiative} />
          ))}
        </Reveal>
      </Container>
    </section>
  );
}

export default Initiatives;
