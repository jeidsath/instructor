import type { ActivityResultResponse } from "../api/types";

interface FeedbackCardProps {
  result: ActivityResultResponse;
  onNext: () => void;
}

export default function FeedbackCard({ result, onNext }: FeedbackCardProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {result.correct ? (
          <span className="text-2xl text-green-600" aria-label="correct">
            &#10003;
          </span>
        ) : (
          <span className="text-2xl text-red-600" aria-label="incorrect">
            &#10007;
          </span>
        )}
        <span
          className={`text-lg font-semibold ${result.correct ? "text-green-700" : "text-red-700"}`}
        >
          {result.correct ? "Correct!" : "Incorrect"}
        </span>
      </div>

      {result.feedback && (
        <p className="text-stone-600">{result.feedback}</p>
      )}

      <button
        onClick={onNext}
        className="rounded-lg bg-stone-800 px-6 py-2 font-medium text-white hover:bg-stone-700"
      >
        Next
      </button>
    </div>
  );
}
