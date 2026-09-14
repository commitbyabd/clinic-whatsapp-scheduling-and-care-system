import styles from "./photo-placeholder.module.css";

/**
 * A reserved image slot for the shots still outstanding in the handoff's
 * asset list. Reproduces the prototype's diagonal stripe fill so a missing
 * photograph reads as deliberately pending rather than broken.
 *
 * Delete the usage — not this component — as each photograph lands.
 */
function PhotoPlaceholder({
  tone = "neutral",
  band = 14,
  caption,
  label,
  className = "",
  style,
  ...rest
}) {
  return (
    <div
      className={`${styles.placeholder} ${styles[tone]} ${className}`.trim()}
      style={{ "--stripe-band": `${band}px`, ...style }}
      role="img"
      aria-label={label || caption || "Photography pending"}
      {...rest}
    >
      {caption ? (
        <span className={styles.caption} aria-hidden="true">
          {caption}
        </span>
      ) : null}
    </div>
  );
}

export default PhotoPlaceholder;
