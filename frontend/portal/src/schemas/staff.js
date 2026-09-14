import { z } from "zod";

/*
  Client-side mirror of the staff models in app/schemas/. Every rule here
  matches a Field(...) constraint on the server, so a changed limit needs
  one edit in this file. The server still validates and still wins.

    doctorCreate       -> DoctorCreate
    doctorUpdate       -> DoctorUpdate
    receptionistCreate -> ReceptionistCreate
    receptionistUpdate -> ReceptionistUpdate
*/

const fullName = z
  .string()
  .trim()
  .min(2, "Full name must be at least 2 characters.")
  .max(100, "Full name cannot be longer than 100 characters.");

// Trim in a separate step piped into the format check. Zod runs checks in
// order, so z.email().trim() would reject a pasted " name@clinic.com "
// before the spaces were removed.
const email = z
  .string()
  .trim()
  .pipe(
    z
      .email("Enter a valid email address.")
      .max(254, "Email address cannot be longer than 254 characters."),
  );

const specialization = z
  .string()
  .trim()
  .min(2, "Specialization must be at least 2 characters.")
  .max(100, "Specialization cannot be longer than 100 characters.");

// Never trimmed: spaces are legitimate password characters and the hash
// has to match what was typed. The 64 ceiling is the server's, because
// bcrypt ignores anything past 72 bytes.
const password = z
  .string()
  .min(8, "Password must be at least 8 characters.")
  .max(64, "Password cannot be longer than 64 characters.");

export const doctorCreateSchema = z.object({
  full_name: fullName,
  email,
  password,
  specialization,
});

export const receptionistCreateSchema = z.object({
  full_name: fullName,
  email,
  password,
});

/*
  The update schemas require what their Pydantic counterparts allow to be
  None. The endpoints accept a partial patch, but the edit form is not
  partial: it shows both fields filled in and always submits both, so a
  blank one is a mistake to catch rather than a patch to send.
*/
export const doctorUpdateSchema = z.object({
  full_name: fullName,
  email,
  specialization,
});

export const receptionistUpdateSchema = z.object({
  full_name: fullName,
  email,
});
