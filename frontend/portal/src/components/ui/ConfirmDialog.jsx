import Modal from "./Modal.jsx";
import Button from "./Button.jsx";
import Alert from "./Alert.jsx";

// Yes/no prompt. The parent owns the request, so it owns busy and error
// too: the dialog stays open while the call is in flight and reports a
// failure in place rather than closing and losing the context.
function ConfirmDialog({
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  confirmVariant = "danger",
  busy = false,
  error = "",
  onConfirm,
  onClose,
}) {
  return (
    <Modal title={title} onClose={onClose} width="max-w-[460px]">
      <p className="font-primary text-md leading-body text-ink">{message}</p>

      {error && <Alert className="mt-4">{error}</Alert>}

      <div className="mt-7 flex justify-end gap-2">
        <Button variant="outline" onClick={onClose} disabled={busy}>
          {cancelLabel}
        </Button>

        <Button
          variant={confirmVariant}
          onClick={onConfirm}
          disabled={busy}
          className="disabled:pointer-events-none disabled:opacity-70"
        >
          {busy ? "Working…" : confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}

export default ConfirmDialog;
