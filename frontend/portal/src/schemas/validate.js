/*
  Adapters between Zod and the shape a form needs.

  Zod reports a flat list of issues carrying a path; a form wants one
  message per field, keyed by field name.
*/

// Returns { valid, data, errors }. The parsed data is what should be sent:
// Zod applies the schema's transforms and drops undeclared keys, so a
// receptionist payload loses specialization and an edit loses password.
export function validateWith(schema, values) {
  const result = schema.safeParse(values);

  if (result.success) {
    return { valid: true, data: result.data, errors: {} };
  }

  const errors = {};

  for (const issue of result.error.issues) {
    const field = issue.path[0];
    if (field && !errors[field]) errors[field] = issue.message;
  }

  return { valid: false, data: null, errors };
}

// Like validateWith, but keyed by the whole path ("prescriptions.0.medicine"),
// for forms that hold lists of rows.
export function validateWithPaths(schema, values) {
  const result = schema.safeParse(values);

  if (result.success) {
    return { valid: true, data: result.data, errors: {} };
  }

  const errors = {};

  for (const issue of result.error.issues) {
    const key = issue.path.join(".");
    if (key && !errors[key]) errors[key] = issue.message;
  }

  return { valid: false, data: null, errors };
}

// Checks one field, for validating on blur. A name the schema does not
// declare returns no message, so blurring password on an edit form is
// silent.
export function validateField(schema, name, value) {
  const fieldSchema = schema.shape?.[name];
  if (!fieldSchema) return "";

  const result = fieldSchema.safeParse(value);
  return result.success ? "" : result.error.issues[0].message;
}
