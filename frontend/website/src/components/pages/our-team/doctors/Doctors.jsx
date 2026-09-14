import { doctorsData } from "../../../../data/pages/our-team/doctors/DoctorsData";
import Container from "../../../ui/container/Container";
import Reveal from "../../../ui/reveal/Reveal";
import DoctorCard from "./_components/DoctorCard";
import styles from "./doctors.module.css";

function Doctors() {
  return (
    <section className={styles.section}>
      <Container>
        <h2 className="srOnly">Our doctors</h2>

        <Reveal className={styles.grid}>
          {doctorsData.map((doctor) => (
            <DoctorCard key={doctor.id} {...doctor} />
          ))}
        </Reveal>
      </Container>
    </section>
  );
}

export default Doctors;
