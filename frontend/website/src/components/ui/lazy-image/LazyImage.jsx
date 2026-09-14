import styles from "./lazy-image.module.css";

/**
 * Content images. Keeps loading/decoding hints consistent and gives every
 * image a wrapper that can carry the design's organic radii — the hero arch,
 * the logo leaf, the nurses' teardrops.
 *
 * Pass `priority` for above-the-fold imagery (the Home hero) so it is not
 * lazily loaded.
 */
function LazyImage({
  src,
  alt = "",
  priority = false,
  radius,
  objectPosition,
  className = "",
  imageClassName = "",
  children,
  style,
  ...rest
}) {
  return (
    <div
      className={`${styles.wrapper} ${className}`.trim()}
      style={{ ...(radius ? { borderRadius: radius } : null), ...style }}
      {...rest}
    >
      <img
        src={src}
        alt={alt}
        className={`${styles.image} ${imageClassName}`.trim()}
        loading={priority ? "eager" : "lazy"}
        decoding={priority ? "sync" : "async"}
        fetchPriority={priority ? "high" : "auto"}
        style={objectPosition ? { objectPosition } : undefined}
      />
      {children}
    </div>
  );
}

export default LazyImage;
