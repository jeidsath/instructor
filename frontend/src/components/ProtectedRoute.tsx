import { Navigate, Outlet } from "react-router";
import { useLearner } from "../hooks/useLearner";

export default function ProtectedRoute() {
  const { learner } = useLearner();

  if (!learner) {
    return <Navigate to="/register" replace />;
  }

  return <Outlet />;
}
