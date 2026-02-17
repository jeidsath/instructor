import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router";
import { useLearner } from "../hooks/useLearner";
import { startSession, getNextActivity, submitResponse, endSession } from "../api/sessions";
import { ApiError } from "../api/client";
import type {
  ActivityResponse,
  ActivityResultResponse,
  Language,
  SessionSummaryResponse,
} from "../api/types";
import ExerciseCard from "../components/ExerciseCard";
import FeedbackCard from "../components/FeedbackCard";

type Phase =
  | { type: "starting" }
  | { type: "error"; message: string }
  | { type: "exercise"; activity: ActivityResponse }
  | { type: "submitting"; activity: ActivityResponse }
  | { type: "feedback"; result: ActivityResultResponse }
  | { type: "loading_next" }
  | { type: "summary"; data: SessionSummaryResponse };

export default function PracticeSessionPage() {
  const { language } = useParams<{ language: string }>();
  const { learner } = useLearner();
  const [phase, setPhase] = useState<Phase>({ type: "starting" });
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [questionNum, setQuestionNum] = useState(0);
  const exerciseStartTime = useRef<number>(0);

  const lang = language as Language;

  const loadNextActivity = useCallback(
    async (sid: string) => {
      setPhase({ type: "loading_next" });
      try {
        const activity = await getNextActivity(sid);
        setQuestionNum((n) => n + 1);
        exerciseStartTime.current = Date.now();
        setPhase({ type: "exercise", activity });
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          // Session complete — no more activities
          try {
            const summary = await endSession(sid);
            setPhase({ type: "summary", data: summary });
          } catch {
            setPhase({ type: "error", message: "Failed to end session." });
          }
        } else {
          setPhase({ type: "error", message: "Failed to load next exercise." });
        }
      }
    },
    [],
  );

  useEffect(() => {
    if (!learner || !lang) return;

    let cancelled = false;

    async function init() {
      try {
        const session = await startSession(learner!.id, lang);
        if (cancelled) return;
        setSessionId(session.id);
        await loadNextActivity(session.id);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setPhase({
            type: "error",
            message: "No learner state found. Take a placement test first.",
          });
        } else {
          setPhase({ type: "error", message: "Failed to start session." });
        }
      }
    }

    init();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learner?.id, lang]);

  async function handleSubmit(response: string) {
    if (!sessionId || phase.type !== "exercise") return;
    const timeMs = Date.now() - exerciseStartTime.current;

    setPhase({ type: "submitting", activity: phase.activity });

    try {
      const result = await submitResponse(sessionId, response, timeMs);
      setPhase({ type: "feedback", result });
    } catch {
      setPhase({ type: "error", message: "Failed to submit response." });
    }
  }

  function handleNext() {
    if (sessionId) {
      loadNextActivity(sessionId);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">
        Practice — {lang === "greek" ? "Ancient Greek" : "Latin"}
      </h1>

      {questionNum > 0 &&
        phase.type !== "summary" &&
        phase.type !== "error" && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm text-stone-500">
              <span>
                Question {questionNum} of ~15
              </span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-stone-200">
              <div
                className="h-2 rounded-full bg-stone-600 transition-all"
                style={{ width: `${Math.min(100, (questionNum / 15) * 100)}%` }}
              />
            </div>
          </div>
        )}

      <div className="mt-6">
        {phase.type === "starting" && (
          <p className="text-stone-600">Starting session...</p>
        )}

        {phase.type === "loading_next" && (
          <p className="text-stone-600">Loading next exercise...</p>
        )}

        {phase.type === "error" && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-red-700">{phase.message}</p>
            <Link
              to="/dashboard"
              className="mt-3 inline-block text-sm font-medium text-stone-700 hover:text-stone-900"
            >
              Back to Dashboard
            </Link>
          </div>
        )}

        {(phase.type === "exercise" || phase.type === "submitting") && (
          <ExerciseCard
            activity={phase.activity}
            onSubmit={handleSubmit}
            disabled={phase.type === "submitting"}
          />
        )}

        {phase.type === "feedback" && (
          <FeedbackCard result={phase.result} onNext={handleNext} />
        )}

        {phase.type === "summary" && (
          <div className="space-y-4 rounded-lg border border-stone-200 bg-white p-6">
            <h2 className="text-lg font-semibold text-stone-900">
              Session Complete
            </h2>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                Total:{" "}
                <span className="font-medium">
                  {phase.data.total_activities}
                </span>
              </div>
              <div>
                Correct:{" "}
                <span className="font-medium text-green-700">
                  {phase.data.correct_count}
                </span>
              </div>
              <div>
                Incorrect:{" "}
                <span className="font-medium text-red-700">
                  {phase.data.incorrect_count}
                </span>
              </div>
              <div>
                Accuracy:{" "}
                <span className="font-medium">
                  {(phase.data.accuracy * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="flex gap-3">
              <Link
                to="/dashboard"
                className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
              >
                Back to Dashboard
              </Link>
              <button
                onClick={() => window.location.reload()}
                className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
              >
                Practice Again
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
