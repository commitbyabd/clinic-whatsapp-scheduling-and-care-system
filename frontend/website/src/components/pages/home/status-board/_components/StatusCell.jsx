import { statusStates } from "../../../../../data/pages/home/status-board/StatusBoardData";
import styles from "./StatusCell.module.css";

function StatusCell({ label, shortLabel, value, unit, caption, state }) {
  const stateLabel = (statusStates[state] ?? statusStates.normal).label;

  return (
    <article className={styles.cell}>
      <div className={styles.top}>
        <h3 className={styles.label}>
          <span className={styles.labelLong}>{label}</span>
          <span className={styles.labelShort}>{shortLabel ?? label}</span>
        </h3>

        {/* The dot carries meaning, so the state is spelled out for anyone
            who cannot see the color. */}
        <span className={`${styles.dot} ${styles[state] ?? styles.normal}`}>
          <span className="srOnly">{stateLabel}</span>
        </span>
      </div>

      <p className={styles.figure}>
        {value}
        {unit ? <span className={styles.unit}> {unit}</span> : null}
      </p>

      <p className={styles.caption}>{caption}</p>
    </article>
  );
}

export default StatusCell;
