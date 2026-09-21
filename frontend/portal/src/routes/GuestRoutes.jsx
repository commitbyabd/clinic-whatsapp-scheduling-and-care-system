import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/authContext.js";
import { homePathFor } from "../utils/roleHome.js";

// The mirror of ProtectedRoutes: keeps a signed-in user off the login form,
// so pressing Back after signing in does not look like being signed out.
function GuestRoutes() {
  const { isAuthenticated, role } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={homePathFor(role)} replace />;
  }

  return <Outlet />;
}

export default GuestRoutes;
