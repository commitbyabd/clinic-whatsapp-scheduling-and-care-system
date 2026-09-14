import styles from "./FundStatCard.module.css";

function FundStatCard({ value, label }) {
  return (
    <article className={styles.card}>
      <p className={styles.value}>{value}</p>
      <p className={styles.label}>{label}</p>
    </article>
  );
}

export default FundStatCard;
