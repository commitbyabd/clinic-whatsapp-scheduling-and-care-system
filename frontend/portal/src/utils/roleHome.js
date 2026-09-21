// Where each role lands after signing in. An unknown role falls through to
// the admin page, which shows it Forbidden.
const HOMES = {
  admin: "/dashboard",
  receptionist: "/reception",
  doctor: "/doctor",
};

export function homePathFor(role) {
  return HOMES[role] ?? "/dashboard";
}
