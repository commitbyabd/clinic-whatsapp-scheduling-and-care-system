const text = (value) =>
  value === null || value === undefined ? "" : String(value);

export const emptyPrescription = () => ({
  medicine: "",
  dose: "",
  frequency: "",
  days: "",
  instructions: "",
});

// The saved consultation as the form holds it: every field as text, the way
// inputs keep their values.
export function consultationForm(appointment) {
  const saved = appointment.consultation ?? {};
  const vitals = saved.vitals ?? {};

  return {
    diagnosis: text(saved.diagnosis),
    bp: text(vitals.bp),
    pulse: text(vitals.pulse),
    temperature: text(vitals.temperature),
    weight: text(vitals.weight),
    prescriptions: (saved.prescriptions ?? []).map((row) => ({
      medicine: text(row.medicine),
      dose: text(row.dose),
      frequency: text(row.frequency),
      days: text(row.days),
      instructions: text(row.instructions),
    })),
    follow_up_on: text(saved.follow_up_on),
    doctor_notes: text(appointment.doctor_notes),
  };
}

// The parsed form, reshaped for PUT /doctor/appointments/{id}/consultation.
// A medicine row left completely empty is dropped.
export function consultationPayload(form) {
  return {
    diagnosis: form.diagnosis,
    vitals: {
      bp: form.bp || null,
      pulse: form.pulse,
      temperature: form.temperature,
      weight: form.weight,
    },
    prescriptions: form.prescriptions.filter((row) => row.medicine),
    follow_up_on: form.follow_up_on || null,
    doctor_notes: form.doctor_notes,
  };
}

// "Penicillin, dust, penicillin" -> ["Penicillin", "dust"]
export function parseList(value) {
  const seen = new Set();
  const items = [];

  for (const part of value.split(",")) {
    const item = part.trim();
    if (item && !seen.has(item.toLowerCase())) {
      seen.add(item.toLowerCase());
      items.push(item);
    }
  }
  return items;
}

export const joinList = (items) => (items ?? []).join(", ");
