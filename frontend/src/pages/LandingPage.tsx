import { Link } from "react-router";
import { useLearner } from "../hooks/useLearner";

const features = [
  {
    title: "Adaptive Practice",
    description:
      "Exercises matched to your level with spaced repetition to build lasting knowledge.",
  },
  {
    title: "Placement Testing",
    description:
      "Start where you belong. A placement test finds your level so you skip what you already know.",
  },
  {
    title: "Progress Tracking",
    description:
      "Watch your vocabulary, grammar mastery, and language skills grow over time.",
  },
  {
    title: "AI-Powered Feedback",
    description:
      "Intelligent scoring and explanations that help you learn from every answer.",
  },
];

const languages = [
  {
    value: "greek",
    label: "Ancient Greek",
    description:
      "Study Attic Greek from the foundations, progressing through classical authors and texts.",
  },
  {
    value: "latin",
    label: "Latin",
    description:
      "Learn Classical Latin with graded readings and a systematic approach to grammar.",
  },
];

export default function LandingPage() {
  const { learner } = useLearner();
  const ctaPath = learner ? "/dashboard" : "/register";
  const ctaLabel = learner ? "Go to Dashboard" : "Get Started";

  return (
    <div className="mx-auto max-w-5xl px-4 py-16">
      {/* Hero */}
      <section className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-stone-900 sm:text-5xl">
          Learn Ancient Greek and Latin
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-stone-600">
          Adaptive, AI-powered instruction that meets you where you are. Build
          real reading ability through personalized practice and intelligent
          feedback.
        </p>
        <Link
          to={ctaPath}
          className="mt-8 inline-block rounded-lg bg-stone-800 px-8 py-3 text-lg font-medium text-white hover:bg-stone-700"
        >
          {ctaLabel}
        </Link>
      </section>

      {/* Features */}
      <section className="mt-20">
        <h2 className="text-center text-2xl font-bold text-stone-900">
          How It Works
        </h2>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-lg border border-stone-200 bg-white p-6"
            >
              <h3 className="font-semibold text-stone-900">{f.title}</h3>
              <p className="mt-2 text-sm text-stone-600">{f.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Languages */}
      <section className="mt-20">
        <h2 className="text-center text-2xl font-bold text-stone-900">
          Choose Your Language
        </h2>
        <div className="mt-8 grid gap-6 sm:grid-cols-2">
          {languages.map((lang) => (
            <div
              key={lang.value}
              className="rounded-lg border border-stone-200 bg-white p-6"
            >
              <h3 className="text-lg font-semibold text-stone-900">
                {lang.label}
              </h3>
              <p className="mt-2 text-sm text-stone-600">
                {lang.description}
              </p>
              <Link
                to={ctaPath}
                className="mt-4 inline-block rounded-lg bg-stone-800 px-5 py-2 text-sm font-medium text-white hover:bg-stone-700"
              >
                Start {lang.label}
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
