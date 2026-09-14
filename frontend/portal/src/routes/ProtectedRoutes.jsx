import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/authContext.js";

/*
  Layout route guarding the private area. Pass 'roles' to restrict a branch
  to particular roles.

  A usability guard, not a security boundary: the bundle is already in the
  browser. Access control lives on the API, which rejects any request
  without a valid token of the right role.
*/
function ProtectedRoutes({ roles }) {
  const location = useLocation();
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) {
    // state.from is what a "return to where you were headed" redirect
    // after sign-in would be built on.
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  // Signed in, wrong role. Sending them to the login form would be a lie,
  // since their session is perfectly valid.
  if (roles && !roles.includes(role)) {
    return <Navigate to="/forbidden" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoutes;
