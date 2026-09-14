/*
  The one button in the system. Add a variant here rather than restyling a
  button per page.

  fullWidth pushes the label left and any trailingIcon right.
*/
const VARIANTS = {
  primary:
    "bg-(image:--gradient-primary-button) text-white shadow-button hover:-translate-y-px hover:filter-(--filter-button-hover) focus-visible:ring-violet/22",
  plum: "bg-plum text-white shadow-button hover:-translate-y-px hover:bg-plum-deep focus-visible:ring-violet/22",
  outline:
    "border border-border bg-white text-plum shadow-sm hover:-translate-y-px hover:bg-pale-lavender focus-visible:ring-violet/22",
  danger: "text-error hover:bg-error-bg focus-visible:ring-error/30",
};

const SIZES = {
  sm: "h-9 gap-2 px-3 text-sm",
  md: "h-11 gap-2 px-4 text-md",
  lg: "h-(--button-height) gap-3 px-5 text-md-lg",
};

function Button({
  children,
  variant = "primary",
  size = "md",
  fullWidth = false,
  leadingIcon,
  trailingIcon,
  type = "button",
  className = "",
  ...rest
}) {
  return (
    <button
      type={type}
      className={`inline-flex shrink-0 items-center rounded-md font-primary font-semibold transition duration-200 focus-visible:ring-4 focus-visible:outline-none ${
        fullWidth ? "w-full justify-between" : "justify-center"
      } ${SIZES[size]} ${VARIANTS[variant]} ${className}`}
      {...rest}
    >
      {leadingIcon}
      <span>{children}</span>
      {trailingIcon}
    </button>
  );
}

export default Button;
