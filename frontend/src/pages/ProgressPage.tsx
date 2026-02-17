import { useEffect, useState } from "react";
import { useLearner } from "../hooks/useLearner";
import { getLearnerState } from "../api/learners";
import { ApiError } from "../api/client";
import type { Language, LearnerStateResponse } from "../api/types";

type LangData =
  | { status: "loading" }
  | { status: "not_started" }
  | { status: "loaded"; data: LearnerStateResponse }
  | { status: "error" };

const LANGUAGES: { value: Language; label: string }[] = [
  { value: "greek", label: "Ancient Greek" },
  { value: "latin", label: "Latin" },
];

const MASTERY_COLORS: Record<string, string> = {
  low: "bg-red-400",
  medium: "bg-yellow-400",
  high: "bg-green-500",
};

function skillColor(value: number): string {
  if (value < 3) return MASTERY_COLORS.low;
  if (value < 6) return MASTERY_COLORS.medium;
  return MASTERY_COLORS.high;
}

function formatStudyTime(minutes: number): string {
  if (minutes === 0) return "0 minutes";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  const parts: string[] = [];
  if (h > 0) parts.push(`${h} hour${h !== 1 ? "s" : ""}`);
  if (m > 0) parts.push(`${m} minute${m !== 1 ? "s" : ""}`);
  return parts.join(" ");
}

function formatDate(iso: string | null): string {
  if (!iso) return "Never";
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function SkillRow({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, (value / 10) * 100);
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 text-sm font-medium text-stone-700">{label}</span>
      <div className="h-3 flex-1 rounded-full bg-stone-200">
        <div
          className={`h-3 rounded-full ${skillColor(value)} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-10 text-right text-sm font-medium text-stone-600">
        {value.toFixed(1)}
      </span>
    </div>
  );
}

function LanguageProgress({ data }: { data: LearnerStateResponse }) {
  return (
    <div className="space-y-8">
      {/* Skills */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
          Skills
        </h3>
        <div className="mt-3 space-y-3">
          <SkillRow label="Reading" value={data.reading_level} />
          <SkillRow label="Writing" value={data.writing_level} />
          <SkillRow label="Listening" value={data.listening_level} />
          <SkillRow label="Speaking" value={data.speaking_level} />
        </div>
      </section>

      {/* Stats */}
      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-500">
          Progress
        </h3>
        <div className="mt-3 grid grid-cols-2 gap-4">
          <div className="rounded-lg border border-stone-200 bg-white p-4">
            <p className="text-2xl font-bold text-stone-900">
              {data.active_vocabulary_size}
            </p>
            <p className="text-sm text-stone-500">Words learned</p>
          </div>
          <div className="rounded-lg border border-stone-200 bg-white p-4">
            <p className="text-2xl font-bold text-stone-900">
              {data.grammar_concepts_mastered}
            </p>
            <p className="text-sm text-stone-500">Concepts mastered</p>
          </div>
          <div className="rounded-lg border border-stone-200 bg-white p-4">
            <p className="text-2xl font-bold text-stone-900">
              {formatStudyTime(data.total_study_time_minutes)}
            </p>
            <p className="text-sm text-stone-500">Study time</p>
          </div>
          <div className="rounded-lg border border-stone-200 bg-white p-4">
            <p className="text-2xl font-bold text-stone-900">
              {formatDate(data.last_session_at)}
            </p>
            <p className="text-sm text-stone-500">Last session</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default function ProgressPage() {
  const { learner } = useLearner();
  const [langData, setLangData] = useState<Record<Language, LangData>>({
    greek: { status: "loading" },
    latin: { status: "loading" },
  });
  const [activeTab, setActiveTab] = useState<Language>("latin");

  useEffect(() => {
    if (!learner) return;

    for (const lang of ["greek", "latin"] as Language[]) {
      getLearnerState(learner.id, lang)
        .then((data) =>
          setLangData((prev) => ({
            ...prev,
            [lang]: { status: "loaded", data },
          })),
        )
        .catch((err) => {
          if (err instanceof ApiError && err.status === 404) {
            setLangData((prev) => ({
              ...prev,
              [lang]: { status: "not_started" },
            }));
          } else {
            setLangData((prev) => ({ ...prev, [lang]: { status: "error" } }));
          }
        });
    }
  }, [learner]);

  const startedLanguages = LANGUAGES.filter(
    (l) => langData[l.value].status === "loaded",
  );
  const hasMultiple = startedLanguages.length > 1;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">Progress</h1>
      <p className="mt-1 text-stone-600">
        Detailed view of your learning progress.
      </p>

      {startedLanguages.length === 0 &&
        langData.greek.status !== "loading" &&
        langData.latin.status !== "loading" && (
          <p className="mt-6 text-stone-500">
            No progress yet. Start practicing or take a placement test to begin.
          </p>
        )}

      {hasMultiple && (
        <div className="mt-6 flex gap-1 rounded-lg bg-stone-100 p-1">
          {startedLanguages.map((lang) => (
            <button
              key={lang.value}
              onClick={() => setActiveTab(lang.value)}
              className={`flex-1 rounded-md px-4 py-2 text-sm font-medium transition ${
                activeTab === lang.value
                  ? "bg-white text-stone-900 shadow-sm"
                  : "text-stone-500 hover:text-stone-700"
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}

      <div className="mt-6">
        {startedLanguages.length === 1 && (
          <>
            <h2 className="text-lg font-semibold text-stone-900">
              {startedLanguages[0].label}
            </h2>
            <div className="mt-4">
              <LanguageProgress
                data={
                  (langData[startedLanguages[0].value] as { status: "loaded"; data: LearnerStateResponse }).data
                }
              />
            </div>
          </>
        )}

        {hasMultiple && langData[activeTab].status === "loaded" && (
          <LanguageProgress
            data={
              (langData[activeTab] as { status: "loaded"; data: LearnerStateResponse }).data
            }
          />
        )}
      </div>
    </div>
  );
}
