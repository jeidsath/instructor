// Enums matching backend StrEnum/IntEnum values

export type Language = "greek" | "latin";

export type MasteryLevel = 0 | 1 | 2 | 3 | 4 | 5;

export type SessionType = "lesson" | "practice" | "evaluation" | "placement";

// Learner

export interface CreateLearnerRequest {
  name: string;
}

export interface LearnerResponse {
  id: string;
  name: string;
}

export interface LearnerStateResponse {
  language: Language;
  reading_level: number;
  writing_level: number;
  listening_level: number;
  speaking_level: number;
  active_vocabulary_size: number;
  grammar_concepts_mastered: number;
  last_session_at: string | null;
  total_study_time_minutes: number;
}

export interface VocabularyItemResponse {
  lemma: string;
  definition: string;
  strength: number;
  next_review: string | null;
  times_correct: number;
  times_incorrect: number;
}

export interface GrammarItemResponse {
  concept_name: string;
  mastery_level: MasteryLevel;
  times_practiced: number;
  recent_error_rate: number;
}

// Session

export interface StartSessionRequest {
  learner_id: string;
  language: Language;
}

export interface SessionResponse {
  id: string;
  session_type: SessionType;
  started_at: string;
  ended_at: string | null;
}

export interface ActivityResponse {
  index: number;
  exercise_type: string;
  prompt: string;
  options: string[];
}

export interface SubmitResponseRequest {
  response: string;
  time_taken_ms: number;
}

export interface ActivityResultResponse {
  score: number;
  correct: boolean;
  feedback: string;
}

export interface SessionSummaryResponse {
  total_activities: number;
  correct_count: number;
  incorrect_count: number;
  accuracy: number;
}

// Curriculum

export interface VocabularySetResponse {
  set_name: string;
  language: Language;
  item_count: number;
}

export interface GrammarConceptResponse {
  name: string;
  category: string;
  subcategory: string;
  difficulty_level: number;
  prerequisite_names: string[];
}

// Placement

export interface PlacementResponseItem {
  probe_type: string;
  difficulty: number;
  correct: boolean;
  item_id: string;
}

export interface PlacementSubmitRequest {
  responses: PlacementResponseItem[];
}

export interface PlacementResultResponse {
  total_score: number;
  vocabulary_score: number;
  grammar_score: number;
  reading_score: number;
  starting_unit: number;
}
