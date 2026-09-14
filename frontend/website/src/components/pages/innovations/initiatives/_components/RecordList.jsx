import styles from "./RecordList.module.css";

/** The patient-portal list panel inside innovation card 03. */
function RecordList({ rows = [] }) {
  return (
    <div className={styles.panel}>
      {rows.map((row) => (
        <div
          key={row.id}
          className={`${styles.row} ${row.highlighted ? styles.highlighted : ""}`.trim()}
        >
          <span
            className={`${styles.dot} ${styles[row.dot]}`}
            aria-hidden="true"
          />
          <span className={styles.label}>{row.label}</span>
          <span className={styles.state}>{row.state}</span>
        </div>
      ))}
    </div>
  );
}

export default RecordList;
