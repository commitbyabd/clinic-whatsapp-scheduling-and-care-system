// Rounded surface. Background, padding and shadow come from the caller so
// one Card serves panels, list rows and dialogs. 'ref' is named explicitly
// rather than left to the spread, so it is clear the element forwards one.
function Card({ as: Tag = "div", ref, className = "", children, ...rest }) {
  return (
    <Tag
      ref={ref}
      className={`rounded-xl border border-border backdrop-blur-glass ${className}`}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export default Card;
