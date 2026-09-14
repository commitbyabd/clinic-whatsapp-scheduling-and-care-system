import Chip from "../../../../ui/chip/Chip";
import LazyImage from "../../../../ui/lazy-image/LazyImage";
import PhotoPlaceholder from "../../../../ui/photo-placeholder/PhotoPlaceholder";
import styles from "./NurseCard.module.css";

function NurseCard({
  name,
  role,
  yearsOfService,
  photo,
  width,
  mobileWidth,
  shape,
  offset,
}) {
  return (
    <article
      className={`${styles.card} ${offset ? styles.offset : ""}`.trim()}
      style={{
        "--nurse-width": `${width}px`,
        "--nurse-width-mobile": `${mobileWidth}px`,
      }}
    >
      {photo ? (
        <LazyImage
          src={photo}
          alt={`${name}, ${role}`}
          className={`${styles.photo} ${styles[shape]}`}
        />
      ) : (
        <PhotoPlaceholder
          tone="sage"
          band={10}
          label={`Portrait of ${name} pending`}
          className={`${styles.photo} ${styles[shape]}`}
        />
      )}

      <h3 className={styles.name}>{name}</h3>
      <p className={styles.role}>{role}</p>

      {yearsOfService ? (
        <Chip variant="gold" size="md" dot className={styles.badge}>
          <span className={styles.badgeLong}>
            {yearsOfService} years with us
          </span>
          <span className={styles.badgeShort}>{yearsOfService} yrs</span>
        </Chip>
      ) : null}
    </article>
  );
}

export default NurseCard;
