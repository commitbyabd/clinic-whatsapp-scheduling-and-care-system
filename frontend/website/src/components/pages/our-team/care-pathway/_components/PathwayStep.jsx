import styles from "./PathwayStep.module.css";

function PathwayStep({ index, title, description, descriptionMobile }) {
  return (
    <article className={styles.step}>
      <p className={styles.index} aria-hidden="true">
        {index}
      </p>

      <h3 className={styles.title}>{title}</h3>

      <p className={`${styles.body} ${styles.bodyDesktop}`}>{description}</p>
      <p className={`${styles.body} ${styles.bodyMobile}`}>
        {descriptionMobile}
      </p>
    </article>
  );
}

export default PathwayStep;
