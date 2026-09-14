import { ShieldAlert } from "lucide-react";
import { useNavigate } from "react-router-dom";
import MessageScreen from "../components/ui/MessageScreen.jsx";
import { usePageTitle } from "../hooks/usePageTitle.js";
import { useAuth } from "../context/authContext.js";

// Reached when a valid session lacks the role a route requires. The way out
// has to sign out first: a plain link to /login would bounce straight back
// here, since the session is still good.
function Forbidden() {
  usePageTitle("No access");
  const navigate = useNavigate();
  const { signOut } = useAuth();

  const handleSignOut = () => {
    signOut();
    navigate("/login", { replace: true });
  };

  return (
    <MessageScreen
      icon={<ShieldAlert className="size-6 text-error" strokeWidth={2} />}
      iconClassName="bg-error-bg"
      title="No access"
      message="Your account does not have permission to open this area. Sign in with an account that does."
      action={{ onClick: handleSignOut, label: "Sign out" }}
    />
  );
}

export default Forbidden;
