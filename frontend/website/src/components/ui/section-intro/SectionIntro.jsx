import styles from "./section-intro.module.css";

/**
 * The eyebrow + heading (+ optional lead paragraph) that opens almost every
 * section. `tone` switches the eyebrow color for the block it sits on —
 * cream, the terracotta Fund block, pale sage, or charcoal.
 */
function SectionIntro({
  eyebrow,
  heading,
  description,
  as: Tag = "h2",
  tone = "default",
  align = "left",
  headingWidth,
  descriptionWidth,
  className = "",
  children,
  ...rest
}) {
  return (
    <div
      className={`${styles.intro} ${styles[tone]} ${styles[align]} ${className}`.trim()}
      {...rest}
    >
      {eyebrow ? <p className={styles.eyebrow}>{eyebrow}</p> : null}

      {heading ? (
        <Tag
          className={styles.heading}
          style={headingWidth ? { maxWidth: `${headingWidth}px` } : undefined}
        >
          {heading}
        </Tag>
      ) : null}

      {description ? (
        <p
          className={styles.description}
          style={
            descriptionWidth ? { maxWidth: `${descriptionWidth}px` } : undefined
          }
        >
          {description}
        </p>
      ) : null}

      {children}
    </div>
  );
}

export default SectionIntro;
