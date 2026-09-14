import { doctorsData } from "../doctors/DoctorsData";

export const clinicDaysIntro = {
  eyebrow: "Clinic days",
  heading: "When each department runs.",
  description:
    "Walk-ins are welcome on any OPD day; booked slots always come first. Emergency cover is continuous across all eight specialties.",
};

export const clinicDaysColumns = [
  { id: "col-department", label: "Department" },
  { id: "col-lead", label: "Lead clinician" },
  { id: "col-opd", label: "OPD days" },
  { id: "col-theatre", label: "Theatre" },
];

/* Order controls the zebra striping, the same way the nurses array controls
   the shape of the tribute wall. The lead clinician is stored as an id and
   resolved against the doctors roster so there is one source of truth for
   names — and so each row can link to that doctor's card above. */
const departments = [
  {
    id: "dept-cardiology",
    name: "Cardiology",
    leadDoctorId: "doctor-rao",
    opdDays: "Mon · Tue · Thu",
    theatreDays: "Thu",
  },
  {
    id: "dept-pediatrics",
    name: "Pediatrics",
    leadDoctorId: "doctor-fischer",
    opdDays: "Daily, 8am–6pm",
    theatreDays: "—",
  },
  {
    id: "dept-orthopedics",
    name: "Orthopedics",
    leadDoctorId: "doctor-okafor",
    opdDays: "Mon · Wed · Fri",
    theatreDays: "Mon · Fri",
  },
  {
    id: "dept-general-surgery",
    name: "General Surgery",
    leadDoctorId: "doctor-qureshi",
    opdDays: "Tue · Thu",
    theatreDays: "Tue · Thu · Sat",
  },
  {
    id: "dept-gynecology",
    name: "Gynecology",
    leadDoctorId: "doctor-menon",
    opdDays: "Mon · Wed · Sat",
    theatreDays: "Wed",
  },
  {
    id: "dept-dermatology",
    name: "Dermatology",
    leadDoctorId: "doctor-herrera",
    opdDays: "Tue · Fri",
    theatreDays: "Fri (day list)",
  },
  {
    id: "dept-internal-medicine",
    name: "Internal Medicine",
    leadDoctorId: "doctor-lim",
    opdDays: "Daily, 8am–8pm",
    theatreDays: "—",
  },
  {
    id: "dept-ent",
    name: "ENT",
    leadDoctorId: "doctor-adeyemi",
    opdDays: "Wed · Sat",
    theatreDays: "Sat",
  },
];

export const clinicDaysData = departments.map((department) => ({
  ...department,
  leadName:
    doctorsData.find((doctor) => doctor.id === department.leadDoctorId)?.name ??
    "—",
}));

export const clinicDaysFootnote = {
  full: "Wednesday and Saturday theatre lists are reserved for Marigold Fund patients. Emergency surgery is never scheduled — it goes ahead whenever it's needed.",
  short:
    "Wednesday and Saturday theatre lists are reserved for Marigold Fund patients.",
};
