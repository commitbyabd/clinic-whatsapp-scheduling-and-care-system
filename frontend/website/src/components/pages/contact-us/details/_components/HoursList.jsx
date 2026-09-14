import styles from "./HoursList.module.css";

/** The three-row justified list inside the Hours card. */
function HoursList({ rows = [] }) {
  return (
    <dl className={styles.list}>
      {rows.map((row) => (
        <div key={row.id} className={styles.row}>
          <dt>{row.label}</dt>
          <dd
            className={`${styles.value} ${row.emphasis ? styles.emphasis : ""}`.trim()}
          >
            {row.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export default HoursList;
