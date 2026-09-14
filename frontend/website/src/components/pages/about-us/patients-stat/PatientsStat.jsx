import { patientsStatData } from "../../../../data/pages/about-us/patients-stat/PatientsStatData";
import useCountUp from "../../../../hooks/useCountUp";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import styles from "./patients-stat.module.css";

function PatientsStat() {
  const { count } = patientsStatData;
  const numberRef = useCountUp({ to: count.to, decimals: count.decimals });

  return (
    <section className={styles.section}>
      <Container>
        <Reveal className={styles.block}>
          <div>
            <p className={styles.value}>
              {/* Screen readers get the figure once, not every frame of the
                  count. The animated copy is hidden from them. */}
              <span className="srOnly">{patientsStatData.value}</span>
              <span aria-hidden="true">
                <span ref={numberRef} className={styles.number} />{" "}
                {count.unit}
              </span>
            </p>
            <p className={styles.label}>{patientsStatData.label}</p>
          </div>

          <div className={styles.aside}>
            <p className={styles.description}>
              {patientsStatData.description}
            </p>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

export default PatientsStat;
