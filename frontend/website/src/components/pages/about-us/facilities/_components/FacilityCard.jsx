import LazyImage from "../../../../ui/lazy-image/LazyImage";
import styles from "./FacilityCard.module.css";

function FacilityCard({ title, description, image }) {
  return (
    <article className={styles.card}>
      <LazyImage
        src={image.src}
        alt={image.alt}
        className={styles.media}
      />

      <div className={styles.body}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.description}>{description}</p>
      </div>
    </article>
  );
}

export default FacilityCard;
