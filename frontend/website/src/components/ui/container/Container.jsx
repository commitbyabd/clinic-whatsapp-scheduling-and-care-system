import styles from "./container.module.css";

/**
 * The standard width wrapper. Every section's inner content goes through it
 * instead of hardcoding max-widths. Full-bleed colored blocks pass a wider
 * maxWidth and constrain their own inner content with a second Container.
 */
function Container({
  as: Tag = "div",
  maxWidth = 1200,
  className = "",
  children,
  style,
  ...rest
}) {
  return (
    <Tag
      className={`${styles.container} ${className}`.trim()}
      style={{ "--container-max": `${maxWidth}px`, ...style }}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export default Container;
