import { useParams } from "react-router";

export default function PlacementTestPage() {
  const { language } = useParams<{ language: string }>();

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <h1 className="text-2xl font-bold text-stone-900">
        Placement Test — {language}
      </h1>
      <p className="mt-2 text-stone-600">
        Find your starting level in {language}.
      </p>
    </div>
  );
}
