/*
  A compact labelled input, for rows that repeat: a medicine in a
  prescription, a block of working hours. TextField is for full forms.

  tone  "hint" while the form is being filled in, "error" after submit
*/
const TONES = {
  hint: "text-hint",
  error: "text-error",
};

function SmallField({
  id,
  label,
  error,
  tone = "error",
  className = "",
  ...inputProps
}) {
  return (
    <div className={className}>
      <label
        htmlFor={id}
        className="block font-primary text-xs font-semibold text-plum"
      >
        {label}
      </label>

      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className="mt-1 h-10 w-full rounded-md border border-border bg-input-surface px-3 font-primary text-sm text-ink outline-none transition duration-200 placeholder:text-muted/60 focus:border-violet focus:shadow-input-focus"
        {...inputProps}
      />

      {error && (
        <p
          id={`${id}-error`}
          role={tone === "error" ? "alert" : "status"}
          className={`mt-1 font-primary text-xs ${TONES[tone] ?? TONES.error}`}
        >
          {error}
        </p>
      )}
    </div>
  );
}

export default SmallField;
