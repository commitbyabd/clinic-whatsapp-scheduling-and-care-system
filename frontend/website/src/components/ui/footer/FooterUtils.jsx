/* Rendering helpers for the footer's mixed link types — internal routes,
   tel:/mailto: targets, and plain text for items that have no destination
   yet. Kept here so Footer.jsx stays declarative. */

export const getLinkKind = (item) => {
  if (item.path) return "route";
  if (item.href) return "external";
  return "text";
};
