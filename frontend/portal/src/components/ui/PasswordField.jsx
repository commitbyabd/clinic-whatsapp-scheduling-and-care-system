import { useState } from "react";
import { Lock, Eye, EyeOff } from "lucide-react";
import TextField from "./TextField.jsx";
import IconBox from "./IconBox.jsx";

// Password input with a visibility toggle. Defaults suit a sign-in form;
// pass id, label, placeholder or autoComplete to reuse it elsewhere.
function PasswordField({ error, ...props }) {
  const [visible, setVisible] = useState(false);

  return (
    <TextField
      id="password"
      name="password"
      type={visible ? "text" : "password"}
      label="Password"
      placeholder="Enter your password"
      autoComplete="current-password"
      error={error}
      {...props}
      icon={
        <IconBox className="bg-password-icon-bg">
          <Lock className="size-4 text-coral" strokeWidth={2} />
        </IconBox>
      }
      trailing={
        <button
          type="button"
          onClick={() => setVisible((shown) => !shown)}
          aria-label={visible ? "Hide password" : "Show password"}
          aria-pressed={visible}
          className="grid size-9 place-items-center rounded-sm text-muted transition duration-200 hover:bg-password-toggle-hover focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none"
        >
          {visible ? (
            <Eye className="size-4.5" strokeWidth={2} />
          ) : (
            <EyeOff className="size-4.5" strokeWidth={2} />
          )}
        </button>
      }
    />
  );
}

export default PasswordField;
