import { useState } from "react";
import { CheckCircle2, KeyRound } from "lucide-react";
import EmailField from "../../ui/EmailField.jsx";
import Button from "../../ui/Button.jsx";
import IconBox from "../../ui/IconBox.jsx";
import Alert from "../../ui/Alert.jsx";
import { readApiError, requestPasswordHelp } from "../../../api/auth.js";
import { passwordHelpSchema } from "../../../schemas/password.js";
import { validateWith } from "../../../schemas/validate.js";

/*
  "Forgot your password?" on the sign-in page. It sends the email address
  and nothing else: an admin sees it in their Requests tab and resets the
  password by hand, so no link and no token is ever sent to anybody.

  Closed to start with, so the page has one email field until it is asked
  for. The reply is the server's, and it reads the same whether the address
  is registered or not.
*/
function ForgotPasswordBox() {
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    const { valid, data, errors } = validateWith(passwordHelpSchema, { email });
    setError(errors.email ?? "");
    if (!valid) return;

    setSending(true);
    try {
      const envelope = await requestPasswordHelp(data.email);
      setSent(envelope.message);
    } catch (failure) {
      setError(readApiError(failure));
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <div className="flex items-start gap-3 rounded-md bg-seafoam/40 p-3.5">
        <IconBox className="bg-white">
          <CheckCircle2 className="size-4 text-violet" strokeWidth={2} />
        </IconBox>
        <p
          role="status"
          className="font-primary text-sm leading-body text-plum"
        >
          {sent}
        </p>
      </div>
    );
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="flex w-full items-center gap-3 rounded-md bg-lavender p-3.5 text-left transition duration-200 hover:bg-pale-lavender focus-visible:ring-4 focus-visible:ring-violet/22 focus-visible:outline-none"
      >
        <IconBox className="bg-white">
          <KeyRound className="size-4 text-violet" strokeWidth={2} />
        </IconBox>
        <span className="font-primary text-sm leading-body text-muted">
          <span className="font-semibold text-plum">Forgot your password?</span>{" "}
          Send us your email and our admin team will reset it.
        </span>
      </button>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="rounded-md bg-lavender p-3.5"
    >
      <p className="font-primary text-sm leading-body text-muted">
        <span className="font-semibold text-plum">Forgot your password?</span>{" "}
        Type the email you sign in with. Our admin team resets it and gets in
        touch — no link is sent.
      </p>

      {error && <Alert className="mt-3">{error}</Alert>}

      <div className="mt-3">
        <EmailField
          id="help-email"
          name="help-email"
          label="Your email address"
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
            setError("");
          }}
          disabled={sending}
        />
      </div>

      <div className="mt-3 flex justify-end gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setOpen(false)}
          disabled={sending}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={sending}
          className="disabled:pointer-events-none disabled:opacity-70"
        >
          {sending ? "Sending…" : "Send"}
        </Button>
      </div>
    </form>
  );
}

export default ForgotPasswordBox;
