/*
  Reads a JWT payload without verifying it.

  Only the server can check the signature, so nothing here is a security
  decision. It exists so the app can notice an expired token before
  rendering a screen the API would immediately reject, and route by role
  instead of showing an admin dashboard to a doctor.
*/
export function decodeToken(token) {
  try {
    const segment = String(token).split(".")[1];
    if (!segment) return null;

    const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
    const binary = atob(base64);

    // atob yields one byte per character; percent-decoding restores any
    // multi-byte UTF-8 in the claims.
    const json = decodeURIComponent(
      Array.from(binary)
        .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, "0")}`)
        .join(""),
    );

    return JSON.parse(json);
  } catch {
    return null;
  }
}

// Treated as expired slightly early, so a token cannot lapse between the
// check and the request it was checked for.
export function isExpired(payload, skewSeconds = 30) {
  if (!payload?.exp) return false;
  return payload.exp * 1000 <= Date.now() + skewSeconds * 1000;
}
