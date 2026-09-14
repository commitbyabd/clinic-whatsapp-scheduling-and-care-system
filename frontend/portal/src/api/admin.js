import api from "./client.js";

/*
  Admin endpoints, mirroring app/features/admin/route.py.

  Every route sits behind require_role("admin") on the server. Each call
  resolves to the response envelope:

      { status_code, message, success, data, error_code }

  so callers read the payload off .data and the user-facing text off
  .message. Non-2xx rejects, with the envelope on error.response.data.
*/
const unwrap = async (request) => {
  const { data } = await request;
  return data;
};

/* ---------------------------------------------------------------- doctors */

export const listDoctors = () => unwrap(api.get("/admin/doctors"));

// Unused by the current screens: the list carries every field the cards
// render. Kept for a detail view, where a record shows more than the list
// projection sends.
export const getDoctor = (doctorId) =>
  unwrap(api.get(`/admin/doctors/${doctorId}`));

// payload: { full_name, email, password, specialization }
export const createDoctor = (payload) =>
  unwrap(api.post("/admin/doctors", payload));

// payload: { full_name, email, specialization }, all optional
export const updateDoctor = (doctorId, payload) =>
  unwrap(api.patch(`/admin/doctors/${doctorId}`, payload));

// Both flip is_active rather than deleting, so appointment history keeps
// pointing at a doctor that still exists.
export const deactivateDoctor = (doctorId) =>
  unwrap(api.patch(`/admin/doctors/${doctorId}/deactivate`));

export const reactivateDoctor = (doctorId) =>
  unwrap(api.patch(`/admin/doctors/${doctorId}/reactivate`));

/* ---------------------------------------------------------- receptionists */

export const listReceptionists = () => unwrap(api.get("/admin/receptionists"));

// Reserved for a detail view, as with getDoctor.
export const getReceptionist = (receptionistId) =>
  unwrap(api.get(`/admin/receptionists/${receptionistId}`));

// payload: { full_name, email, password }
export const createReceptionist = (payload) =>
  unwrap(api.post("/admin/receptionists", payload));

// payload: { full_name, email }, all optional
export const updateReceptionist = (receptionistId, payload) =>
  unwrap(api.patch(`/admin/receptionists/${receptionistId}`, payload));

export const deactivateReceptionist = (receptionistId) =>
  unwrap(api.patch(`/admin/receptionists/${receptionistId}/deactivate`));

export const reactivateReceptionist = (receptionistId) =>
  unwrap(api.patch(`/admin/receptionists/${receptionistId}/reactivate`));

/* ------------------------------------------------------------- deactivated */

/*
  One endpoint covers both roles, so the rows arrive mixed and each carries
  its own 'role' straight from the users collection.

  That raw value is kept as 'kind', since reactivating has to pick between
  the doctor and receptionist endpoints, and 'role' is rewritten for display:
  the card prints it as-is.
*/
export const listDeactivatedStaff = async () => {
  const envelope = await unwrap(api.get("/admin/deactivated-users"));

  return {
    ...envelope,
    data: (envelope.data ?? []).map((row) => ({
      ...row,
      kind: row.role,
      role: row.role === "doctor" ? "Doctor" : "Receptionist",
    })),
  };
};
