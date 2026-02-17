import { useState, type FormEvent } from "react";
import type { ActivityResponse } from "../api/types";

interface ExerciseCardProps {
  activity: ActivityResponse;
  onSubmit: (response: string) => void;
  disabled: boolean;
}

export default function ExerciseCard({
  activity,
  onSubmit,
  disabled,
}: ExerciseCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [textInput, setTextInput] = useState("");
  const isMultipleChoice = activity.options.length > 0;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (isMultipleChoice && selected) {
      onSubmit(selected);
    } else if (!isMultipleChoice && textInput.trim()) {
      onSubmit(textInput.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <p className="text-lg text-stone-800">{activity.prompt}</p>

      {isMultipleChoice ? (
        <div className="space-y-2">
          {activity.options.map((opt) => (
            <button
              key={opt}
              type="button"
              disabled={disabled}
              onClick={() => setSelected(opt)}
              className={`block w-full rounded-lg border-2 px-4 py-3 text-left transition ${
                selected === opt
                  ? "border-stone-800 bg-stone-50"
                  : "border-stone-200 hover:border-stone-400"
              } disabled:opacity-50`}
            >
              {opt}
            </button>
          ))}
        </div>
      ) : (
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          disabled={disabled}
          placeholder="Type your answer"
          className="block w-full rounded-lg border border-stone-300 px-3 py-2 text-stone-900 placeholder:text-stone-400 focus:border-stone-500 focus:ring-1 focus:ring-stone-500 focus:outline-none disabled:opacity-50"
        />
      )}

      <button
        type="submit"
        disabled={
          disabled ||
          (isMultipleChoice ? !selected : !textInput.trim())
        }
        className="rounded-lg bg-stone-800 px-6 py-2 font-medium text-white hover:bg-stone-700 disabled:opacity-50"
      >
        Submit
      </button>
    </form>
  );
}
