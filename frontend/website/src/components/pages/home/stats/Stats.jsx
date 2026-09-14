import { statsData } from "../../../../data/pages/home/stats/StatsData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import styles from "./stats.module.css";

function Stats() {
  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.strip}>
          {statsData.map((stat) => (
            <article key={stat.id} className={styles.stat}>
              <p className={styles.value}>{stat.value}</p>
              <p className={styles.label}>{stat.label}</p>
            </article>
          ))}
        </Reveal>
      </Container>
    </section>
  );
}

export default Stats;
