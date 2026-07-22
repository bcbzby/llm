import client from './client';
import type {
  ApiResponse,
  LoginResponse,
  User,
  Certification,
  Question,
  QuestionDetail,
  ExamCreateRequest,
  ExamCreateResponse,
  ExamSubmitRequest,
  ExamSubmitResponse,
  ExamResultResponse,
  ReportResponse,
  WrongBookItem,
  KnowledgeArticle,
  KnowledgeDetail,
  ExamHistoryItem,
} from '../types';

// ===== Auth =====
export const authApi = {
  register: (data: { email: string; password: string; nickname: string }) =>
    client.post<ApiResponse>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    client.post<ApiResponse<LoginResponse>>('/auth/login', data),

  refresh: (refresh_token: string) =>
    client.post<ApiResponse>('/auth/refresh', { refresh_token }),

  getMe: () => client.get<ApiResponse<User>>('/auth/me'),
};

// ===== Certifications =====
export const certApi = {
  list: () => client.get<ApiResponse<Certification[]>>('/certifications'),
};

// ===== Questions =====
export const questionApi = {
  list: (params?: {
    subject_id?: number;
    certification_id?: number;
    difficulty?: string;
    tag_ids?: string;
    lang?: 'zh' | 'en';
    random_sample?: boolean;
    exclude_ids?: string;
    page?: number;
    page_size?: number;
  }) => client.get<ApiResponse<{ items: Question[]; total: number; page: number; page_size: number }>>('/questions', { params }),

  detail: (id: number) => client.get<ApiResponse<QuestionDetail>>(`/questions/${id}`),

  /** Batch fetch correct answers for practice mode */
  batchCorrectKeys: async (ids: number[]): Promise<Record<number, string[]>> => {
    const result: Record<number, string[]> = {};
    // Fetch in parallel batches of 10
    for (let i = 0; i < ids.length; i += 10) {
      const batch = ids.slice(i, i + 10);
      const res = await Promise.allSettled(
        batch.map((id) => client.get<ApiResponse<QuestionDetail>>(`/questions/${id}`))
      );
      res.forEach((r, idx) => {
        if (r.status === 'fulfilled') {
          result[batch[idx]] = r.value.data.data.correct_keys || [];
        }
      });
    }
    return result;
  },
};

// ===== Exams =====
export const examApi = {
  create: (data: ExamCreateRequest) =>
    client.post<ApiResponse<ExamCreateResponse>>('/exams', data),

  submit: (examId: number, data: ExamSubmitRequest) =>
    client.post<ApiResponse<ExamSubmitResponse>>(`/exams/${examId}/submit`, data),

  result: (examId: number) =>
    client.get<ApiResponse<ExamResultResponse>>(`/exams/${examId}/result`),

  history: () => client.get<ApiResponse<ExamHistoryItem[]>>('/exams/history'),
};

// ===== Reports =====
export const reportApi = {
  get: (examId: number) =>
    client.get<ApiResponse<ReportResponse>>(`/reports/${examId}`),
};

// ===== Wrong Book =====
export const wrongBookApi = {
  list: (params?: { certification_id?: number; is_mastered?: boolean; page?: number; page_size?: number }) =>
    client.get<ApiResponse<{ items: WrongBookItem[]; total: number }>>('/wrong-book', { params }),

  markMastered: (id: number) =>
    client.post<ApiResponse>(`/wrong-book/${id}/master`),
};

// ===== Knowledge =====
export const knowledgeApi = {
  list: (params?: { provider?: string; category?: string; page?: number; page_size?: number }) =>
    client.get<ApiResponse<{ items: KnowledgeArticle[]; total: number }>>('/knowledge', { params }),

  detail: (id: number) =>
    client.get<ApiResponse<KnowledgeDetail>>(`/knowledge/${id}`),

  search: (q: string) =>
    client.get<ApiResponse<{ items: any[]; total: number }>>('/knowledge/search', { params: { q } }),
};

// ===== Tags =====
export const tagApi = {
  list: () =>
    client.get<ApiResponse<{ id: number; name: string; full_path: string; level: number }[]>>('/tags'),
};

// ===== Contribute =====
export const contributeApi = {
  subjects: () => client.get<ApiResponse<{ cert_id: number; cert_name: string; subjects: { id: number; name: string }[] }[]>>('/questions/contribute/subjects'),
  submit: (data: {
    subject_id: number;
    question_type: string;
    difficulty: string;
    content: string;
    explanation: string;
    tags: string[];
    options: { key: string; content: string; is_correct: boolean }[];
  }) => client.post<ApiResponse>('/questions/contribute', data),
  // Admin review
  reviewList: (status: string) =>
    client.get<ApiResponse<{ questions: any[]; total: number }>>(`/questions/contribute/admin/list?status=${status}`),
  reviewAction: (questionId: number, action: string) =>
    client.post<ApiResponse>(`/questions/contribute/admin/review/${questionId}`, { action }),
};
