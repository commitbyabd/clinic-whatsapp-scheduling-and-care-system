/* Right-sized copies (npm run images:thumbs), not the 1254px masters. */
const portrait = (file) => `/images/pages/our-team/doctors/w720/${file}`;

export const doctorsData = [
  {
    id: "doctor-rao",
    name: "Dr. Anjali Rao",
    specialization: "Cardiology",
    note: "Medical Director · 22 yrs",
    photo: portrait("doc-1.avif"),
  },
  {
    id: "doctor-okafor",
    name: "Dr. Samuel Okafor",
    specialization: "Orthopedics",
    note: "Joint reconstruction",
    photo: portrait("doc-2-male.avif"),
  },
  {
    id: "doctor-fischer",
    name: "Dr. Lena Fischer",
    specialization: "Pediatrics",
    note: "Neonatal & child health",
    photo: portrait("doc-4.avif"),
  },
  {
    id: "doctor-qureshi",
    name: "Dr. Hasan Qureshi",
    specialization: "General Surgery",
    note: "Laparoscopic lead",
    photo: portrait("doc-3-male.avif"),
  },
  {
    id: "doctor-menon",
    name: "Dr. Priya Menon",
    specialization: "Gynecology",
    note: "Obstetrics & high-risk care",
    photo: portrait("doc-6.avif"),
  },
  {
    id: "doctor-herrera",
    name: "Dr. Tomás Herrera",
    specialization: "Dermatology",
    note: "Clinic & day procedures",
    photo: portrait("doc-5-male.avif"),
  },
  {
    id: "doctor-lim",
    name: "Dr. Grace Lim",
    specialization: "Internal Medicine",
    note: "Diabetes & thyroid",
    photo: portrait("doc-7.avif"),
  },
  {
    id: "doctor-adeyemi",
    name: "Dr. Yusuf Adeyemi",
    specialization: "ENT",
    note: "Head, neck & audiology",
    photo: portrait("doc-8-male.avif"),
  },
];
