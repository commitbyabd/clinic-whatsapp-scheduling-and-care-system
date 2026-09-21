import api from "./client.js";

/*
  Receptionist endpoints, mirroring app/features/receptionist/route.py.

  Every route sits behind require_role("receptionist") on the server, and
  each call resolves to the response envelope, as in admin.js.
*/
const unwrap = async (request) => {
  const { data } = await request;
  return data;
};

/* ------------------------------------------------------- booking requests */

// status: new | scheduled | declined | cancelled. New is the inbox.
export const listBookingRequests = (status = "new") =>
  unwrap(api.get("/receptionist/booking-requests", { params: { status } }));

// Patients registered under the request's WhatsApp number. The server
// reads the number off the request, so it never goes in a URL.
export const listMatchingPatients = (requestId) =>
  unwrap(api.get(`/receptionist/booking-requests/${requestId}/patients`));

// payload: { doctor_id, starts_at, patient_id }
//      or: { doctor_id, starts_at, new_patient: { full_name, date_of_birth, gender } }
// starts_at is one of the times listFreeSlots returned, sent back unchanged.
export const scheduleBookingRequest = (requestId, payload) =>
  unwrap(
    api.post(`/receptionist/booking-requests/${requestId}/schedule`, payload),
  );

export const declineBookingRequest = (requestId) =>
  unwrap(api.patch(`/receptionist/booking-requests/${requestId}/decline`));

/* ---------------------------------------------------------------- doctors */

export const listDoctors = () => unwrap(api.get("/receptionist/doctors"));

// date is "YYYY-MM-DD", a day in clinic time. Slots come back as UTC ISO
// strings, and the message says why when there are none.
export const listFreeSlots = (doctorId, date) =>
  unwrap(
    api.get(`/receptionist/doctors/${doctorId}/slots`, { params: { date } }),
  );
