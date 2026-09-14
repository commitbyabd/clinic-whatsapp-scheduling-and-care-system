// Square icon container. Surface colour comes from the caller.
function IconBox({
  size = "size-8",
  radius = "rounded-sm",
  className = "",
  children,
}) {
  return (
    <span
      className={`grid shrink-0 place-items-center ${size} ${radius} ${className}`}
    >
      {children}
    </span>
  );
}

export default IconBox;
