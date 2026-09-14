import { Link } from "react-router";
import styles from "./button.module.css";

/**
 * Every pill button on the site. Renders a <Link> for internal routes, an
 * <a> for external/tel/mailto targets, and a <button> otherwise.
 *
 * Variants follow the palette's rule — sage is the institution, terracotta
 * is the Fund, gold is the ask — so pick the variant by what the button
 * asks for, not by where it sits.
 */
function Button({
  as,
  to,
  href,
  variant = "primary",
  size = "lg",
  className = "",
  children,
  ...rest
}) {
  const classes = `${styles.button} ${styles[variant]} ${styles[size]} ${className}`.trim();

  if (to) {
    return (
      <Link to={to} className={classes} {...rest}>
        {children}
      </Link>
    );
  }

  if (href) {
    return (
      <a href={href} className={classes} {...rest}>
        {children}
      </a>
    );
  }

  const Tag = as || "button";

  return (
    <Tag className={classes} type={Tag === "button" ? "button" : undefined} {...rest}>
      {children}
    </Tag>
  );
}

export default Button;
