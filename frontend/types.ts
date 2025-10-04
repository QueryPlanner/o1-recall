// Backend API types
export interface Topic {
  id: number;
  name: string;
}

export interface SubTopic {
  id: number;
  name: string;
  topic_id: number;
}

export interface Choice {
  id: number;
  question_id: number;
  choice_text: string;
  is_correct: boolean;
}

export interface Question {
  id: number;
  sub_topic_id: number;
  question_text: string;
  explanation: string | null;
  image_url: string | null;
  choices: Choice[];
}

export interface AnswerRequest {
  question_id: number;
  choice_id: number;
}

export interface AnswerResponse {
  is_correct: boolean;
  correct_choice_id: number;
}

export interface StreakResponse {
  current_streak_days: number;
  today_answers_count: number;
  streak_goal: number;
}
