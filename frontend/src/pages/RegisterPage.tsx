import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { createLearner } from "../api/learners";
import { ApiError } from "../api/client";
import { useLearner } from "../hooks/useLearner";
import type { Language } from "../api/types";

export default function RegisterPage() {
  const { learner, setLearner } = useLearner();
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [language, setLanguage] = useState<Language | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (learner) {
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-stone-900">Welcome back</h1>
        <p className="mt-2 text-stone-600">
          You are signed in as <strong>{learner.name}</strong>.
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <button
            onClick={() => navigate("/dashboard")}
            className="rounded-lg bg-stone-800 px-6 py-3 font-medium text-white hover:bg-stone-700"
          >
            Go to Dashboard
          </button>
          <button
            onClick={() => {
              setName("");
              setLanguage(null);
              setError("");
            }}
            className="text-sm text-stone-500 hover:text-stone-700"
          >
            Or register a new learner
          </button>
        </div>
      </div>
    );
  }

  const nameError =
    name.length > 200 ? "Name must be 200 characters or fewer" : "";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");

    if (!name.trim()) {
      setError("Please enter your name.");
      return;
    }
    if (name.length > 200) {
      setError("Name must be 200 characters or fewer.");
      return;
    }
    if (!language) {
      setError("Please select a language.");
      return;
    }

    setSubmitting(true);
    try {
      const learnerResponse = await createLearner(name.trim());
      setLearner(learnerResponse);
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        const detail =
          typeof err.body === "object" &&
          err.body !== null &&
          "detail" in err.body
            ? String((err.body as { detail: unknown }).detail)
            : `Server error (${err.status})`;
        setError(detail);
      } else {
        setError("Network error. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const languageCards: { value: Language; label: string; desc: string }[] = [
    {
      value: "greek",
      label: "Ancient Greek",
      desc: "Attic Greek with classical authors",
    },
    {
      value: "latin",
      label: "Latin",
      desc: "Classical Latin with graded readings",
    },
  ];

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-center text-2xl font-bold text-stone-900">
        Welcome to Instructor
      </h1>
      <p className="mt-2 text-center text-stone-600">
        Enter your name and choose a language to begin.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-6">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-stone-700"
          >
            Your name
          </label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            maxLength={200}
            className="mt-1 block w-full rounded-lg border border-stone-300 px-3 py-2 text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:ring-1 focus:ring-stone-500 focus:outline-none"
          />
          {nameError && (
            <p className="mt-1 text-sm text-red-600">{nameError}</p>
          )}
        </div>

        <fieldset>
          <legend className="block text-sm font-medium text-stone-700">
            Choose a language
          </legend>
          <div className="mt-2 grid grid-cols-2 gap-3">
            {languageCards.map((lang) => (
              <button
                key={lang.value}
                type="button"
                onClick={() => setLanguage(lang.value)}
                className={`rounded-lg border-2 p-4 text-left transition ${
                  language === lang.value
                    ? "border-stone-800 bg-stone-50"
                    : "border-stone-200 hover:border-stone-400"
                }`}
              >
                <span className="block font-medium text-stone-900">
                  {lang.label}
                </span>
                <span className="mt-1 block text-sm text-stone-500">
                  {lang.desc}
                </span>
              </button>
            ))}
          </div>
        </fieldset>

        {error && (
          <p role="alert" className="text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-stone-800 px-6 py-3 font-medium text-white hover:bg-stone-700 disabled:opacity-50"
        >
          {submitting ? "Creating account..." : "Begin Learning"}
        </button>
      </form>
    </div>
  );
}
