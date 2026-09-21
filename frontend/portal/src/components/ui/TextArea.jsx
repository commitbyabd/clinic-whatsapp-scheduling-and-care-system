/*
  Labelled multi-line input, styled to match TextField.

  error  message rendered beneath the field
  tone   "hint" while the form is being filled in, "error" after submit
*/
const TONES = {
  hint: "text-hint",
  error: "text-error",
};

function TextArea({
  id,
  label,
  error,
  tone = "error",
  rows = 3,
  className = "",
  ...textareaProps
}) {
  return (
    <div className={className}>
      <label
        htmlFor={id}
        className="block font-primary text-sm font-semibold text-plum"
      >
        {label}
      </label>

      <textarea
        id={id}
        rows={rows}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className="mt-2 block w-full resize-y rounded-md border border-border bg-input-surface px-4 py-3 font-primary text-md leading-body text-ink outline-none transition duration-200 placeholder:text-muted/60 focus:border-violet focus:shadow-input-focus"
        {...textareaProps}
      />

      {error && (
        <p
          id={`${id}-error`}
          role={tone === "error" ? "alert" : "status"}
          className={`mt-2 font-primary text-sm ${TONES[tone] ?? TONES.error}`}
        >
          {error}
        </p>
      )}
    </div>
  );
}

export default TextArea;
