import { useCallback, useState, type ReactNode } from "react";
import type { LearnerResponse } from "../api/types";
import { LearnerContext } from "./learner-context";

const STORAGE_KEY = "instructor_learner";

function loadLearner(): LearnerResponse | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as LearnerResponse;
  } catch {
    // ignore corrupt data
  }
  return null;
}

export function LearnerProvider({ children }: { children: ReactNode }) {
  const [learner, setLearnerState] = useState<LearnerResponse | null>(
    loadLearner,
  );

  const setLearner = useCallback((l: LearnerResponse) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(l));
    setLearnerState(l);
  }, []);

  const clearLearner = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setLearnerState(null);
  }, []);

  return (
    <LearnerContext value={{ learner, setLearner, clearLearner }}>
      {children}
    </LearnerContext>
  );
}
