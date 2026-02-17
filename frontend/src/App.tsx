import { BrowserRouter, Route, Routes } from "react-router";
import { LearnerProvider } from "./context/LearnerContext";
import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import PracticeSessionPage from "./pages/PracticeSessionPage";
import PlacementTestPage from "./pages/PlacementTestPage";
import ProgressPage from "./pages/ProgressPage";

export default function App() {
  return (
    <BrowserRouter>
      <LearnerProvider>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<LandingPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route
                path="practice/:language"
                element={<PracticeSessionPage />}
              />
              <Route
                path="placement/:language"
                element={<PlacementTestPage />}
              />
              <Route path="progress" element={<ProgressPage />} />
            </Route>
          </Route>
        </Routes>
      </LearnerProvider>
    </BrowserRouter>
  );
}
