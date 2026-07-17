import { useState, useCallback } from 'react';
import type { ExamQuestion, AnswerItem } from '../types';
import { examApi } from '../api';

export function useExam() {
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [answers, setAnswers] = useState<Map<number, string[]>>(new Map());
  const [markedQuestions, setMarkedQuestions] = useState<Set<number>>(new Set());
  const [currentIndex, setCurrentIndex] = useState(0);
  const [examId, setExamId] = useState<number | null>(null);
  const [examTitle, setExamTitle] = useState('');
  const [durationMin, setDurationMin] = useState(0);
  const [loading, setLoading] = useState(false);

  const startExam = useCallback(async (certId: number, examType = 'mock') => {
    setLoading(true);
    try {
      const res = await examApi.create({
        certification_id: certId,
        exam_type: examType,
      });
      const data = res.data.data;
      setExamId(data.exam_id);
      setQuestions(data.questions);
      setDurationMin(data.duration_min);
      setExamTitle(data.certification?.name || '模拟考试');
      setAnswers(new Map());
      setMarkedQuestions(new Set());
      setCurrentIndex(0);
    } finally {
      setLoading(false);
    }
  }, []);

  const selectAnswer = useCallback((questionId: number, keys: string[]) => {
    setAnswers((prev) => {
      const next = new Map(prev);
      next.set(questionId, keys);
      return next;
    });
  }, []);

  const toggleMark = useCallback((questionId: number) => {
    setMarkedQuestions((prev) => {
      const next = new Set(prev);
      if (next.has(questionId)) next.delete(questionId);
      else next.add(questionId);
      return next;
    });
  }, []);

  const goTo = useCallback((index: number) => {
    if (index >= 0 && index < questions.length) setCurrentIndex(index);
  }, [questions.length]);

  const currentQuestion = questions[currentIndex] || null;

  const answeredCount = answers.size;
  const answeredQuestions = Array.from(answers.keys());

  return {
    questions,
    currentQuestion,
    currentIndex,
    markedQuestions,
    answers,
    examId,
    examTitle,
    durationMin,
    loading,
    answeredCount,
    answeredQuestions,
    startExam,
    selectAnswer,
    toggleMark,
    goTo,
    totalQuestions: questions.length,
  };
}
