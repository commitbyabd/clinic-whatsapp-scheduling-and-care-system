import api from "./client.js";

/*
  Receptionist endpoints, mirroring app/features/receptionist/route.py.

  Every route sits behind require_role("receptionist") on the server, and
  each call resolves to the response envelope, as in admin.js.
*/

// status: new | scheduled | declined | cancelled. New is the inbox.
export const listBookingRequests = async (status = "new") => {
  const { data } = await api.get("/receptionist/booking-requests", {
    params: { status },
  });
  return data;
};
