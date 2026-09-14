// Initials avatar. Surface colour comes from the caller.
function Avatar({
  initials,
  size = "size-14",
  radius = "rounded-lg",
  className = "",
}) {
  return (
    <span
      aria-hidden="true"
      className={`grid shrink-0 place-items-center font-primary text-md-lg font-bold text-plum ${size} ${radius} ${className}`}
    >
      {initials}
    </span>
  );
}

export default Avatar;
