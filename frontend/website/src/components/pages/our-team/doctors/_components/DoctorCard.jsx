import LazyImage from "../../../../ui/lazy-image/LazyImage";
import styles from "./DoctorCard.module.css";

function DoctorCard({ id, name, specialization, note, photo }) {
  return (
    /* The clinic days table links here by id. */
    <article id={id} className={styles.card}>
      <LazyImage
        src={photo}
        alt={`${name}, ${specialization}`}
        className={styles.media}
      />

      <div className={styles.body}>
        <h3 className={styles.name}>{name}</h3>
        <p className={styles.specialization}>{specialization}</p>
        <p className={styles.note}>{note}</p>
      </div>
    </article>
  );
}

export default DoctorCard;
