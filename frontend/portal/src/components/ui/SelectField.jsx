import { ChevronDown } from "lucide-react";

/*
  Labelled select, styled to match TextField. Options come as children.

  error  message rendered beneath the field
  tone   "hint" while the form is being filled in, "error" after submit
*/
const TONES = {
  hint: "text-hint",
  error: "text-error",
};

function SelectField({
  id,
  label,
  icon,
  error,
  tone = "error",
  className = "",
  children,
  ...selectProps
}) {
  return (
    <div className={className}>
      <label
        htmlFor={id}
        className="block font-primary text-sm font-semibold text-plum"
      >
        {label}
      </label>

      <div className="relative mt-2 flex h-(--input-height) items-center rounded-md border border-border bg-input-surface transition duration-200 has-[select:focus]:border-violet has-[select:focus]:shadow-input-focus">
        {icon && (
          <span className="pointer-events-none absolute left-3 flex">{icon}</span>
        )}

        <select
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
          className={`h-full w-full cursor-pointer appearance-none truncate rounded-md bg-transparent pr-10 font-primary text-md text-ink outline-none disabled:cursor-default ${icon ? "pl-14" : "pl-4"}`}
          {...selectProps}
        >
          {children}
        </select>

        <ChevronDown
          aria-hidden="true"
          className="pointer-events-none absolute right-3 size-4 text-muted"
          strokeWidth={2}
        />
      </div>

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

export default SelectField;
