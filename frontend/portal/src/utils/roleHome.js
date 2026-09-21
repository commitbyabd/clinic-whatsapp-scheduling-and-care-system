// Where each role lands after signing in. Doctors have no portal yet, so they
// fall through to the admin page, which shows them Forbidden.
const HOMES = {
  admin: "/dashboard",
  receptionist: "/reception",
};

export function homePathFor(role) {
  return HOMES[role] ?? "/dashboard";
}
