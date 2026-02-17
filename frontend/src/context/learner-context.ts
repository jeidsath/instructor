import { createContext } from "react";
import type { LearnerResponse } from "../api/types";

export interface LearnerContextValue {
  learner: LearnerResponse | null;
  setLearner: (learner: LearnerResponse) => void;
  clearLearner: () => void;
}

export const LearnerContext = createContext<LearnerContextValue | null>(null);
