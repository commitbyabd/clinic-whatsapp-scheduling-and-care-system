import { useRef, useState } from "react";
import { KeyRound, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import ChangePasswordModal from "./ChangePasswordModal.jsx";
import Toast from "../../ui/Toast.jsx";
import { useAuth } from "../../../context/authContext.js";

// Roles are stored lowercase; the header shows them the way a person
// would write them.
const titleCase = (value) =>
  value ? value.charAt(0).toUpperCase() + value.slice(1) : "";

const ICON_BUTTON =
  "grid size-10 place-items-center rounded-md text-muted transition duration-200 hover:bg-pale-lavender hover:text-plum focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none";

function HeaderUser() {
  const navigate = useNavigate();
  const { user, role: sessionRole, signIn, signOut } = useAuth();
  const [changing, setChanging] = useState(false);

  // a counter, so a second toast gets its own key and a fresh timer
  const toastId = useRef(0);
  const [toast, setToast] = useState(null);

  const name = user?.full_name || "Signed in";
  const role = titleCase(user?.role || sessionRole) || "Staff";

  const handleSignOut = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  // the old token stopped working with the change, so the new one takes
  // its place and the user stays signed in
  const handleChanged = (token) => {
    signIn({ token, user });
    setChanging(false);
    toastId.current += 1;
    setToast({ id: toastId.current, text: "Password changed." });
  };

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <p className="font-primary text-sm font-medium text-plum">{name}</p>
        <p className="font-primary text-xs text-muted">{role}</p>
      </div>

      <button
        type="button"
        onClick={() => setChanging(true)}
        aria-label="Change password"
        title="Change password"
        className={ICON_BUTTON}
      >
        <KeyRound className="size-4.5" strokeWidth={2} />
      </button>

      <button
        type="button"
        onClick={handleSignOut}
        aria-label="Sign out"
        title="Sign out"
        className={ICON_BUTTON}
      >
        <LogOut className="size-4.5" strokeWidth={2} />
      </button>

      {changing && (
        <ChangePasswordModal
          onClose={() => setChanging(false)}
          onChanged={handleChanged}
        />
      )}

      {toast && (
        <Toast
          key={toast.id}
          message={toast.text}
          onDone={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default HeaderUser;
