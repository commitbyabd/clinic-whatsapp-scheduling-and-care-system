import api, { TOKEN_KEY, USER_KEY } from "./client.js";

// POST /auth/login -> { access_token, token_type, role, full_name }
export async function login({ email, password }) {
  const { data } = await api.post("/auth/login", { email, password });
  return data;
}

export function saveToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function readToken() {
  return localStorage.getItem(TOKEN_KEY);
}

// Display data only, cached because the JWT carries just the id and role.
// Never use it for a decision the server should be making.
export function saveUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function readUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    // Hand-edited or truncated storage should sign the user out, not crash
    // the component asking for a name.
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

const GENERIC = "Something went wrong. Please try again.";

/*
  Reduces an axios failure to one readable sentence.

  The API replies in three shapes: { message } for the api_response
  envelope used by /admin, { detail: "..." } for a raw HTTPException, and
  { detail: [{ msg }] } for Pydantic validation errors. The envelope wins
  because its message is written for the user.
*/
export function readApiError(error) {
  const status = error?.response?.status;
  const body = error?.response?.data;

  // A 5xx body describes a fault, not something the user can act on, and
  // may carry internal detail. Only 4xx text is meant to be read.
  if (status >= 500) return GENERIC;

  if (typeof body?.message === "string") return body.message;

  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;

  if (error?.code === "ERR_NETWORK") return "Cannot reach the server.";
  if (error?.code === "ECONNABORTED") {
    return "The server took too long to respond. Please try again.";
  }

  return GENERIC;
}
