// ===== API Response =====
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
  request_id?: string;
}

// ===== User =====
export interface User {
  id: number;
  email: string;
  nickname: string;
  role: string;
  avatar_url: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// ===== Certification =====
export interface Subject {
  id: number;
  name: string;
  weight: number;
}

export interface Certification {
  id: number;
  provider: string;
  code: string;
  name: string;
  level: string;
  description: string | null;
  total_questions: number;
  pass_score: number;
  duration_min: number;
  image_url: string | null;
  subjects: Subject[];
}

// ===== Question =====
export interface QuestionOption {
  key: string;
  content: string;
}

export interface QuestionTag {
  id: number;
  name: string;
}

export interface Question {
  id: number;
  question_type: string;
  difficulty: string;
  content: string;
  options: QuestionOption[];
  tags?: QuestionTag[];
  subject?: { id: number; name: string };
}

export interface QuestionDetail extends Question {
  explanation: string;
  correct_keys: string[];
  reference_url?: string;
}

// ===== Exam =====
export interface ExamCreateRequest {
  certification_id: number;
  exam_type: string;
  question_count?: number;
  duration_min?: number;
  custom_tags?: number[];
}

export interface ExamCreateResponse {
  exam_id: number;
  certification: { id: number; name: string; pass_score: number } | null;
  total_questions: number;
  duration_min: number;
  questions: ExamQuestion[];
  status: string;
  started_at: string;
}

export interface ExamQuestion {
  id: number;
  question_type: string;
  content: string;
  options: QuestionOption[];
}

export interface AnswerItem {
  question_id: number;
  selected_keys: string[];
}

export interface ExamSubmitRequest {
  answers: AnswerItem[];
  used_seconds: number;
}

export interface ExamSubmitResponse {
  exam_id: number;
  status: string;
  total_questions: number;
  correct_count: number;
  wrong_count: number;
  unanswered_count: number;
  score: number;
  total_score: number;
  pass_score: number | null;
  is_passed: boolean | null;
  used_seconds: number;
  completed_at: string | null;
}

export interface QuestionResult {
  question_id: number;
  content: string;
  question_type: string;
  options: { key: string; content: string }[];
  selected_keys: string[];
  correct_keys: string[];
  is_correct: boolean;
  explanation: string | null;
}

export interface ExamResultResponse {
  exam_id: number;
  title: string | null;
  status: string;
  total_questions: number;
  correct_count: number;
  wrong_count: number;
  unanswered_count: number;
  score: number;
  total_score: number;
  pass_score: number | null;
  is_passed: boolean | null;
  gap_to_pass: number;
  used_seconds: number;
  duration_min: number;
  started_at: string | null;
  completed_at: string | null;
  question_results: QuestionResult[];
}

// ===== Report =====
export interface SubjectBreakdown {
  subject_id: number;
  subject_name: string;
  weight: number;
  total: number;
  correct: number;
  correct_rate: string;
}

export interface TagBreakdown {
  tag_id: number;
  tag_name: string;
  total: number;
  correct: number;
  correct_rate: string;
}

export interface WeaknessTag {
  tag_id: number;
  tag_name: string;
  correct_rate: string;
  suggested_action: string;
}

export interface ReportResponse {
  exam_summary: {
    exam_id: number;
    title: string | null;
    score: number;
    total_score: number;
    correct_rate: string;
    is_passed: boolean | null;
    gap_to_pass: number;
  };
  subject_breakdown: SubjectBreakdown[];
  tag_breakdown: TagBreakdown[];
  weakness_tags: WeaknessTag[];
  strength_tags: { tag_id: number; tag_name: string; correct_rate: string; suggested_action: string }[];
  history_trend: { date: string; score: number }[];
}

// ===== Wrong Book =====
export interface WrongBookItem {
  id: number;
  question_id: number;
  question: {
    content: string;
    question_type: string;
    difficulty: string;
    options: QuestionOption[];
  };
  wrong_count: number;
  last_wrong_at: string;
  is_mastered: boolean;
}

// ===== Knowledge =====
export interface KnowledgeArticle {
  id: number;
  provider: string | null;
  category: string;
  title: string;
  summary: string | null;
  view_count: number;
  like_count: number;
  tags: QuestionTag[];
  created_at: string;
}

export interface KnowledgeDetail extends KnowledgeArticle {
  content: string;
  source_url: string | null;
  updated_at: string;
  published_at: string | null;
}

// ===== Exam History =====
export interface ExamHistoryItem {
  exam_id: number;
  title: string | null;
  exam_type: string;
  score: number;
  total_score: number;
  is_passed: boolean | null;
  correct_count: number;
  total_questions: number;
  status: string;
  started_at: string;
  completed_at: string | null;
}
