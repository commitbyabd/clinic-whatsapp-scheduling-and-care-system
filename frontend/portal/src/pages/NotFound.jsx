import { Compass } from "lucide-react";
import MessageScreen from "../components/ui/MessageScreen.jsx";
import { usePageTitle } from "../hooks/usePageTitle.js";
import { useAuth } from "../context/authContext.js";

function NotFound() {
  usePageTitle("Page not found");
  const { isAuthenticated } = useAuth();

  return (
    <MessageScreen
      icon={<Compass className="size-6 text-violet" strokeWidth={2} />}
      title="Page not found"
      message="That address does not match anything in the clinic dashboard."
      action={
        isAuthenticated
          ? { to: "/dashboard", label: "Back to dashboard" }
          : { to: "/login", label: "Go to sign in" }
      }
    />
  );
}

export default NotFound;
