import styles from "./PriceCard.module.css";

function PriceCard({ title, price, note, emphasis = false }) {
  return (
    <article
      className={`${styles.card} ${emphasis ? styles.emphasis : ""}`.trim()}
    >
      <h3 className={styles.title}>{title}</h3>
      <p className={styles.price}>{price}</p>
      <p className={styles.note}>{note}</p>
    </article>
  );
}

export default PriceCard;
