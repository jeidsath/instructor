import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { useLearner } from "../hooks/useLearner";
import { getVocabularySets, getGrammarConcepts } from "../api/curriculum";
import { submitPlacement } from "../api/placement";
import type {
  GrammarConceptResponse,
  Language,
  PlacementResponseItem,
  PlacementResultResponse,
  VocabularySetResponse,
} from "../api/types";

interface Probe {
  id: string;
  probe_type: string;
  difficulty: number;
  prompt: string;
  options: string[];
  correctIndex: number;
}

function buildProbes(
  vocabSets: VocabularySetResponse[],
  grammarConcepts: GrammarConceptResponse[],
): Probe[] {
  const probes: Probe[] = [];

  // Generate vocabulary probes from available sets at graduated difficulty
  vocabSets.slice(0, 5).forEach((set, i) => {
    probes.push({
      id: `vocab-${set.set_name}`,
      probe_type: "vocabulary",
      difficulty: Math.min(5, i + 1),
      prompt: `How many items are in the "${set.set_name}" vocabulary set?`,
      options: [
        String(set.item_count),
        String(set.item_count + 10),
        String(Math.max(1, set.item_count - 5)),
        String(set.item_count + 25),
      ],
      correctIndex: 0,
    });
  });

  // Generate grammar probes from concepts at different difficulty levels
  const byDifficulty = [1, 2, 3, 4, 5]
    .map((d) => grammarConcepts.filter((c) => c.difficulty_level === d)[0])
    .filter(Boolean);

  byDifficulty.forEach((concept) => {
    if (!concept) return;
    probes.push({
      id: `grammar-${concept.name}`,
      probe_type: "grammar",
      difficulty: concept.difficulty_level,
      prompt: `What category does "${concept.name}" belong to?`,
      options: [
        concept.category,
        concept.category === "morphology" ? "syntax" : "morphology",
        "phonology",
        "prosody",
      ],
      correctIndex: 0,
    });
  });

  // Shuffle options for each probe (keep track of correctIndex)
  return probes.map((p) => {
    const correct = p.options[p.correctIndex];
    const shuffled = [...p.options].sort(() => Math.random() - 0.5);
    return { ...p, options: shuffled, correctIndex: shuffled.indexOf(correct) };
  });
}

type Phase =
  | { type: "loading" }
  | { type: "error"; message: string }
  | { type: "probing"; probes: Probe[]; current: number; responses: PlacementResponseItem[] }
  | { type: "submitting" }
  | { type: "results"; data: PlacementResultResponse };

export default function PlacementTestPage() {
  const { language } = useParams<{ language: string }>();
  const { learner } = useLearner();
  const [phase, setPhase] = useState<Phase>({ type: "loading" });
  const lang = language as Language;

  useEffect(() => {
    if (!learner || !lang) return;
    let cancelled = false;

    async function load() {
      try {
        const [vocabSets, grammarConcepts] = await Promise.all([
          getVocabularySets(lang),
          getGrammarConcepts(lang),
        ]);
        if (cancelled) return;
        const probes = buildProbes(vocabSets, grammarConcepts);
        if (probes.length === 0) {
          setPhase({ type: "error", message: "No curriculum data available for this language." });
          return;
        }
        setPhase({ type: "probing", probes, current: 0, responses: [] });
      } catch {
        if (!cancelled) {
          setPhase({ type: "error", message: "Failed to load curriculum data." });
        }
      }
    }

    load();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [learner?.id, lang]);

  async function handleAnswer(optionIndex: number) {
    if (phase.type !== "probing" || !learner) return;
    const probe = phase.probes[phase.current];
    const correct = optionIndex === probe.correctIndex;

    const response: PlacementResponseItem = {
      probe_type: probe.probe_type,
      difficulty: probe.difficulty,
      correct,
      item_id: probe.id,
    };

    const newResponses = [...phase.responses, response];
    const nextIndex = phase.current + 1;

    if (nextIndex >= phase.probes.length) {
      // All probes done — submit
      setPhase({ type: "submitting" });
      try {
        const result = await submitPlacement(learner.id, lang, newResponses);
        setPhase({ type: "results", data: result });
      } catch {
        setPhase({ type: "error", message: "Failed to submit placement results." });
      }
    } else {
      setPhase({ type: "probing", probes: phase.probes, current: nextIndex, responses: newResponses });
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">
        Placement Test — {lang === "greek" ? "Ancient Greek" : "Latin"}
      </h1>

      {phase.type === "loading" && (
        <p className="mt-6 text-stone-600">Loading placement test...</p>
      )}

      {phase.type === "error" && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-red-700">{phase.message}</p>
          <Link
            to="/dashboard"
            className="mt-3 inline-block text-sm font-medium text-stone-700"
          >
            Back to Dashboard
          </Link>
        </div>
      )}

      {phase.type === "probing" && (
        <div className="mt-6">
          <p className="text-sm text-stone-500">
            Let's see what you already know.
          </p>
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm text-stone-500">
              <span>
                Question {phase.current + 1} of {phase.probes.length}
              </span>
            </div>
            <div className="mt-1 h-2 rounded-full bg-stone-200">
              <div
                className="h-2 rounded-full bg-stone-600 transition-all"
                style={{
                  width: `${((phase.current + 1) / phase.probes.length) * 100}%`,
                }}
              />
            </div>
          </div>

          <div className="mt-6">
            <p className="text-lg text-stone-800">
              {phase.probes[phase.current].prompt}
            </p>
            <div className="mt-4 space-y-2">
              {phase.probes[phase.current].options.map((opt, i) => (
                <button
                  key={i}
                  onClick={() => handleAnswer(i)}
                  className="block w-full rounded-lg border-2 border-stone-200 px-4 py-3 text-left transition hover:border-stone-400"
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {phase.type === "submitting" && (
        <p className="mt-6 text-stone-600">Submitting results...</p>
      )}

      {phase.type === "results" && (
        <div className="mt-6 space-y-6 rounded-lg border border-stone-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-stone-900">
            Placement Results
          </h2>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              Overall:{" "}
              <span className="font-medium">
                {(phase.data.total_score * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              Vocabulary:{" "}
              <span className="font-medium">
                {(phase.data.vocabulary_score * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              Grammar:{" "}
              <span className="font-medium">
                {(phase.data.grammar_score * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              Reading:{" "}
              <span className="font-medium">
                {(phase.data.reading_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <p className="text-stone-700">
            You'll begin at{" "}
            <span className="font-semibold">
              Unit {phase.data.starting_unit}
            </span>
            .
          </p>

          <div className="flex gap-3">
            <Link
              to="/dashboard"
              className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
            >
              Go to Dashboard
            </Link>
            <Link
              to={`/practice/${lang}`}
              className="rounded-lg bg-stone-800 px-4 py-2 text-sm font-medium text-white hover:bg-stone-700"
            >
              Start Practicing
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
