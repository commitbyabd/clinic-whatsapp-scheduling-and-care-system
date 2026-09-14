import { Mail } from "lucide-react";
import TextField from "./TextField.jsx";
import IconBox from "./IconBox.jsx";

// Email input with the shared icon treatment. Pass id, label or
// autoComplete to reuse it outside the sign-in form.
function EmailField({ error, ...props }) {
  return (
    <TextField
      id="email"
      name="email"
      type="email"
      label="Email address"
      placeholder="you@clinic.com"
      autoComplete="email"
      error={error}
      {...props}
      icon={
        <IconBox className="bg-lavender">
          <Mail className="size-4 text-violet" strokeWidth={2} />
        </IconBox>
      }
    />
  );
}

export default EmailField;
