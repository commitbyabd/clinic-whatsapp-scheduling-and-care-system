import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoutes from "./ProtectedRoutes.jsx";
import GuestRoutes from "./GuestRoutes.jsx";
import RouteFallback from "./RouteFallback.jsx";
import Login from "../pages/login/Login.jsx";
import Forbidden from "../pages/Forbidden.jsx";
import NotFound from "../pages/NotFound.jsx";
import { useAuth } from "../context/authContext.js";

// Split out so the login page does not ship the dashboard with it.
const Dashboard = lazy(() => import("../pages/dashboard/Dashboard.jsx"));

function RootRedirect() {
  const { isAuthenticated } = useAuth();
  return <Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />;
}

// Route table for the whole app. Each element points at a page in
// src/pages, never at a component directly.
function ProjectRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<RootRedirect />} />

        <Route element={<GuestRoutes />}>
          <Route path="/login" element={<Login />} />
        </Route>

        {/* Pathless layout route: anything nested here is guarded by default */}
        <Route element={<ProtectedRoutes roles={["admin"]} />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>

        <Route path="/forbidden" element={<Forbidden />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}

export default ProjectRoutes;
