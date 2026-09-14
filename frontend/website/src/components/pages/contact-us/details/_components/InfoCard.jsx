import { externalLinkProps } from "../../../../../utils/global/Links";
import styles from "./InfoCard.module.css";

function InfoCard({ label, value, href, lines, note, children }) {
  return (
    <article className={styles.card}>
      <h3 className={styles.label}>{label}</h3>

      {href ? (
        <a href={href} className={styles.value} {...externalLinkProps(href)}>
          {value}
        </a>
      ) : null}

      {!href && value ? <p className={styles.value}>{value}</p> : null}

      {lines ? (
        <p className={`${styles.value} ${styles.address}`}>
          {lines.map((line, index) => (
            <span key={line}>
              {line}
              {index < lines.length - 1 ? <br /> : null}
            </span>
          ))}
        </p>
      ) : null}

      {note ? <p className={styles.note}>{note}</p> : null}

      {children}
    </article>
  );
}

export default InfoCard;
