import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../../context/authContext.js";

// Roles are stored lowercase; the header shows them the way a person
// would write them.
const titleCase = (value) =>
  value ? value.charAt(0).toUpperCase() + value.slice(1) : "";

function HeaderUser() {
  const navigate = useNavigate();
  const { user, role: sessionRole, signOut } = useAuth();

  const name = user?.full_name || "Signed in";
  const role = titleCase(user?.role || sessionRole) || "Staff";

  const handleSignOut = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className="flex items-center gap-3">
      <div className="text-right">
        <p className="font-primary text-sm font-medium text-plum">{name}</p>
        <p className="font-primary text-xs text-muted">{role}</p>
      </div>

      <button
        type="button"
        onClick={handleSignOut}
        aria-label="Sign out"
        className="grid size-10 place-items-center rounded-md text-muted transition duration-200 hover:bg-pale-lavender hover:text-plum focus-visible:ring-2 focus-visible:ring-violet/22 focus-visible:outline-none"
      >
        <LogOut className="size-4.5" strokeWidth={2} />
      </button>
    </div>
  );
}

export default HeaderUser;
