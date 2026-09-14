import styles from "./ResearchStats.module.css";

/** The three gold figures below the rule on innovation card 02. */
function ResearchStats({ items = [] }) {
  return (
    <div className={styles.stats}>
      {items.map((item) => (
        <div key={item.id}>
          <p className={styles.value}>{item.value}</p>
          <p className={styles.label}>{item.label}</p>
        </div>
      ))}
    </div>
  );
}

export default ResearchStats;
