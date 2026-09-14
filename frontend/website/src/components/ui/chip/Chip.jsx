import styles from "./chip.module.css";

/**
 * The uppercase pill used for availability badges, status chips and the
 * nurses' long-service recognition. `dot` adds the small leading circle.
 */
function Chip({
  as: Tag = "span",
  variant = "sage",
  size = "md",
  dot = false,
  className = "",
  children,
  ...rest
}) {
  return (
    <Tag
      className={`${styles.chip} ${styles[variant]} ${styles[size]} ${className}`.trim()}
      {...rest}
    >
      {dot ? <span className={styles.dot} aria-hidden="true" /> : null}
      {children}
    </Tag>
  );
}

export default Chip;
