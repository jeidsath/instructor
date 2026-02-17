import { useContext } from "react";
import {
  LearnerContext,
  type LearnerContextValue,
} from "../context/learner-context";

export function useLearner(): LearnerContextValue {
  const ctx = useContext(LearnerContext);
  if (!ctx) throw new Error("useLearner must be used within LearnerProvider");
  return ctx;
}
