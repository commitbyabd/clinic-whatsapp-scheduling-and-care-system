/* Helpers for the mix of link targets the site carries: internal routes,
   tel:/mailto: handoffs to the device, and outbound https links such as the
   WhatsApp deep link. */

/**
 * True for links that leave the site and so should open in a new tab.
 * tel: and mailto: are deliberately excluded — those hand off to the
 * device's own dialler or mail client and must stay in the same tab.
 */
export const isExternalHref = (href) =>
  typeof href === "string" && /^https?:\/\//i.test(href);

/**
 * Spread onto an anchor to open outbound links safely. rel="noopener" stops
 * the opened page getting a handle on this one via window.opener.
 */
export const externalLinkProps = (href) =>
  isExternalHref(href)
    ? { target: "_blank", rel: "noopener noreferrer" }
    : null;
