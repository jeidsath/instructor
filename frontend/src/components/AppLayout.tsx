import { Link, Outlet } from "react-router";
import { useLearner } from "../hooks/useLearner";

export default function AppLayout() {
  const { learner, clearLearner } = useLearner();

  return (
    <div className="flex min-h-screen flex-col bg-stone-50 text-stone-800">
      <header className="border-b border-stone-200 bg-white">
        <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-xl font-bold text-stone-900">
            Instructor
          </Link>
          <div className="flex items-center gap-4 text-sm">
            {learner ? (
              <>
                <Link
                  to="/dashboard"
                  className="text-stone-600 hover:text-stone-900"
                >
                  Dashboard
                </Link>
                <Link
                  to="/progress"
                  className="text-stone-600 hover:text-stone-900"
                >
                  Progress
                </Link>
                <button
                  onClick={clearLearner}
                  className="text-stone-500 hover:text-stone-700"
                >
                  Sign out
                </button>
              </>
            ) : (
              <Link
                to="/register"
                className="text-stone-600 hover:text-stone-900"
              >
                Register
              </Link>
            )}
          </div>
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-stone-200 py-4 text-center text-xs text-stone-400">
        Instructor — Ancient Greek &amp; Latin
      </footer>
    </div>
  );
}
