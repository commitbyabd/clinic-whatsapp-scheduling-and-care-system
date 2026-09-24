import { Stethoscope, ConciergeBell, UserX, KeyRound } from "lucide-react";
import {
  listDoctors,
  listPasswordRequests,
  listReceptionists,
  listDeactivatedStaff,
  deactivateDoctor,
  deactivateReceptionist,
  reactivateDoctor,
  reactivateReceptionist,
} from "../api/admin.js";

/*
  The single description of each staff list: what the sidebar calls it, what
  the section header says, and which endpoints it talks to.

  Both the nav and the list read from here, so a wording change lands in one
  place. A third kind of staff is a new entry, not another branch.
*/
export const STAFF_VIEWS = [
  {
    slug: "doctors",
    title: "Doctors",
    subtitle: "Clinicians taking appointments",
    icon: Stethoscope,
    kind: "doctor",
    noun: "doctor",
    role: "Doctor",
    empty: "No doctors yet. Add one to get started.",
    fetchList: listDoctors,
    deactivate: deactivateDoctor,
  },
  {
    slug: "receptionists",
    title: "Receptionists",
    subtitle: "Front desk and scheduling",
    icon: ConciergeBell,
    kind: "receptionist",
    noun: "receptionist",
    role: "Receptionist",
    empty: "No receptionists yet. Add one to get started.",
    fetchList: listReceptionists,
    deactivate: deactivateReceptionist,
  },
  {
    slug: "requests",
    title: "Password requests",
    subtitle: "Staff who cannot sign in",
    icon: KeyRound,
    noun: "password request",
    // Not staff rows: each is someone asking for a reset, so the list
    // draws PasswordRequestCard and offers no Add button.
    rows: "password-request",
    empty:
      "No password requests. Staff who forget theirs ask from the sign-in page.",
    fetchList: listPasswordRequests,
  },
  {
    slug: "deactivated",
    title: "Deactivated users",
    subtitle: "Accounts without access",
    icon: UserX,
    noun: "deactivated user",
    empty: "No deactivated accounts. Everyone on staff currently has access.",
    fetchList: listDeactivatedStaff,
    // Restoring access is the only action here, and which endpoint to call
    // depends on the row rather than the view: this list holds both roles.
    // No 'kind', so the section knows not to offer an Add button.
    reactivate: (member) =>
      member.kind === "doctor"
        ? reactivateDoctor(member.id)
        : reactivateReceptionist(member.id),
  },
];

export const DEFAULT_VIEW_SLUG = "doctors";

export function findView(slug) {
  return STAFF_VIEWS.find((view) => view.slug === slug);
}
