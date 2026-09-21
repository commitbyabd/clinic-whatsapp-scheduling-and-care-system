import api from "./client.js";

/*
  Doctor endpoints, mirroring app/features/doctor/route.py.

  Every route sits behind require_role("doctor") and works on the signed-in
  doctor's own data: the server takes the doctor from the token. Each call
  resolves to the response envelope, as in admin.js.
*/
const unwrap = async (request) => {
  const { data } = await request;
  return data;
};

/* ---------------------------------------------------------- working hours */

// data is the schedule, or [] when none has been saved yet
export const getSchedule = () => unwrap(api.get("/doctor/schedule"));

// payload: { working_hours: [{ day_of_week, start_time, end_time }],
//            slot_minutes, blackout_dates: ["YYYY-MM-DD"] }
export const saveSchedule = (payload) =>
  unwrap(api.put("/doctor/schedule", payload));

/* ----------------------------------------------------------- appointments */

// Today onwards, or every visit when includePast is true
export const listAppointments = (includePast = false) =>
  unwrap(
    api.get("/doctor/appointments", { params: { include_past: includePast } }),
  );

// payload: { diagnosis, vitals: { bp, pulse, temperature, weight },
//            prescriptions: [...], follow_up_on, doctor_notes }
export const saveConsultation = (appointmentId, payload) =>
  unwrap(api.put(`/doctor/appointments/${appointmentId}/consultation`, payload));

// status: completed | no_show, or booked to undo either
export const setAppointmentStatus = (appointmentId, status) =>
  unwrap(api.patch(`/doctor/appointments/${appointmentId}/status`, { status }));

/* --------------------------------------------------------------- patients */

// payload: { allergies: [...], chronic_conditions: [...], blood_group }
export const saveMedicalDetails = (patientId, payload) =>
  unwrap(api.put(`/doctor/patients/${patientId}/medical`, payload));
