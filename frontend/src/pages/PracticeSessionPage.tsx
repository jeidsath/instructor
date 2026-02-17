import { useParams } from "react-router";

export default function PracticeSessionPage() {
  const { language } = useParams<{ language: string }>();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">
        Practice — {language}
      </h1>
      <p className="mt-2 text-stone-600">
        Interactive exercises for {language}.
      </p>
    </div>
  );
}
