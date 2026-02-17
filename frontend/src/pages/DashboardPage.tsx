import { useEffect, useState } from "react";
import { Link } from "react-router";
import { useLearner } from "../hooks/useLearner";
import { getLearnerState } from "../api/learners";
import { ApiError } from "../api/client";
import type { Language, LearnerStateResponse } from "../api/types";

type LanguageState =
  | { status: "loading" }
  | { status: "not_started" }
  | { status: "loaded"; data: LearnerStateResponse }
  | { status: "error"; message: string };

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "greek", label: "Ancient Greek" },
  { value: "latin", label: "Latin" },
];

function formatStudyTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}

function SkillBar({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, (value / 10) * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="w-20 text-sm text-stone-600">{label}</span>
      <div className="h-2 flex-1 rounded-full bg-stone-200">
        <div
          className="h-2 rounded-full bg-stone-600"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-sm text-stone-500">
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function LanguageCard({
  language,
  state,
  onRetry,
}: {
  language: { value: Language; label: string };
  state: LanguageState;
  onRetry: () => void;
}) {
  if (state.status === "loading") {
    return (
      <div className="animate-pulse rounded-lg border border-stone-200 bg-white p-6">
        <div className="h-6 w-32 rounded bg-stone-200" />
        <div className="mt-4 space-y-3">
          <div className="h-4 w-full rounded bg-stone-100" />
          <div className="h-4 w-3/4 rounded bg-stone-100" />
          <div className="h-4 w-1/2 rounded bg-stone-100" />
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="rounded-lg border border-red-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-stone-900">
          {language.label}
        </h2>
        <p className="mt-2 text-sm text-red-600">{state.message}</p>
        <button
          onClick={onRetry}
          className="mt-3 text-sm font-medium text-stone-700 hover:text-stone-900"
        >
          Retry
        </button>
      </div>
    );
  }

  if (state.status === "not_started") {
    return (
      <div className="rounded-lg border border-stone-200 bg-white p-6">
        <h2 className="text-lg font-semibold text-stone-900">
          {language.label}
        </h2>
        <p className="mt-2 text-sm text-stone-600">
          Take a placement test to find your level, or start from the beginning.
        </p>
        <div className="mt-4 flex gap-3">
          <Link
            to={`/placement/${language.value}`}
            className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
          >
            Take Placement Test
          </Link>
          <Link
            to={`/practice/${language.value}`}
            className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
          >
            Start Practicing
          </Link>
        </div>
      </div>
    );
  }

  const d = state.data;
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-6">
      <h2 className="text-lg font-semibold text-stone-900">
        {language.label}
      </h2>

      <div className="mt-4 space-y-2">
        <SkillBar label="Reading" value={d.reading_level} />
        <SkillBar label="Writing" value={d.writing_level} />
        <SkillBar label="Listening" value={d.listening_level} />
        <SkillBar label="Speaking" value={d.speaking_level} />
      </div>

      <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-stone-600">
        <div>
          <span className="font-medium text-stone-900">
            {d.active_vocabulary_size}
          </span>{" "}
          words learned
        </div>
        <div>
          <span className="font-medium text-stone-900">
            {d.grammar_concepts_mastered}
          </span>{" "}
          concepts mastered
        </div>
        <div>
          Study time:{" "}
          <span className="font-medium text-stone-900">
            {formatStudyTime(d.total_study_time_minutes)}
          </span>
        </div>
        <div>
          Last session:{" "}
          <span className="font-medium text-stone-900">
            {d.last_session_at
              ? formatRelativeTime(d.last_session_at)
              : "Never"}
          </span>
        </div>
      </div>

      <div className="mt-4 flex gap-3">
        <Link
          to={`/practice/${language.value}`}
          className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
        >
          Practice
        </Link>
        <Link
          to={`/placement/${language.value}`}
          className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
        >
          Placement Test
        </Link>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { learner } = useLearner();
  const [states, setStates] = useState<Record<Language, LanguageState>>({
    greek: { status: "loading" },
    latin: { status: "loading" },
  });

  const fetchState = (lang: Language) => {
    if (!learner) return;
    setStates((prev) => ({ ...prev, [lang]: { status: "loading" } }));
    getLearnerState(learner.id, lang)
      .then((data) =>
        setStates((prev) => ({ ...prev, [lang]: { status: "loaded", data } })),
      )
      .catch((err) => {
        if (err instanceof ApiError && err.status === 404) {
          setStates((prev) => ({
            ...prev,
            [lang]: { status: "not_started" },
          }));
        } else {
          setStates((prev) => ({
            ...prev,
            [lang]: {
              status: "error",
              message: "Failed to load. Please try again.",
            },
          }));
        }
      });
  };

  useEffect(() => {
    if (!learner) return;
    fetchState("greek");
    fetchState("latin");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learner?.id]);

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">Dashboard</h1>
      <p className="mt-1 text-stone-600">
        Welcome back{learner ? `, ${learner.name}` : ""}.
      </p>

      <div className="mt-6 grid gap-6 md:grid-cols-2">
        {LANGUAGES.map((lang) => (
          <LanguageCard
            key={lang.value}
            language={lang}
            state={states[lang.value]}
            onRetry={() => fetchState(lang.value)}
          />
        ))}
      </div>
    </div>
  );
}
