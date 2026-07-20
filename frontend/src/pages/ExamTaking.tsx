import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { examApi } from '../api';
import type { ExamCreateResponse } from '../types';
import QuestionCard from '../components/QuestionCard';

export default function ExamTaking() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const [examData, setExamData] = useState<ExamCreateResponse | null>(null);
  const [answers, setAnswers] = useState<Map<number, string[]>>(new Map());
  const [markedQuestions, setMarkedQuestions] = useState<Set<number>>(new Set());
  const [currentIndex, setCurrentIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showConfirm, setShowConfirm] = useState(false);

  // Track elapsed seconds with ref to avoid stale closures
  const startTimeRef = useRef(Date.now());
  const elapsedRef = useRef(0);

  // Visibility detection (anti-cheat)
  useEffect(() => {
    const handleVisibility = () => {
      if (document.hidden) console.warn('User left exam page');
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, []);

  // Load exam data from location state, fallback to sessionStorage
  useEffect(() => {
    const state = location.state as { examData?: ExamCreateResponse } | null;
    if (state?.examData) {
      setExamData(state.examData);
      sessionStorage.setItem(`exam_${examId}`, JSON.stringify(state.examData));
      startTimeRef.current = Date.now();
      setLoading(false);
    } else {
      // Try to restore from sessionStorage
      const saved = sessionStorage.getItem(`exam_${examId}`);
      if (saved) {
        try {
          const parsed = JSON.parse(saved) as ExamCreateResponse;
          setExamData(parsed);
          startTimeRef.current = Date.now();
          setLoading(false);
        } catch {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    }
  }, [location.state, examId]);

  // Persist answers to sessionStorage on change
  useEffect(() => {
    if (!examId) return;
    const answerObj: Record<number, string[]> = {};
    answers.forEach((v, k) => { answerObj[k] = v; });
    sessionStorage.setItem(`exam_${examId}_answers`, JSON.stringify(answerObj));
    sessionStorage.setItem(`exam_${examId}_marked`, JSON.stringify([...markedQuestions]));
    sessionStorage.setItem(`exam_${examId}_index`, String(currentIndex));
  }, [answers, markedQuestions, currentIndex, examId]);

  // Restore answers from sessionStorage
  useEffect(() => {
    if (!examId || !examData) return;
    const savedAnswers = sessionStorage.getItem(`exam_${examId}_answers`);
    const savedMarked = sessionStorage.getItem(`exam_${examId}_marked`);
    const savedIndex = sessionStorage.getItem(`exam_${examId}_index`);

    if (savedAnswers) {
      try {
        const obj = JSON.parse(savedAnswers) as Record<number, string[]>;
        const map = new Map<number, string[]>();
        Object.entries(obj).forEach(([k, v]) => map.set(Number(k), v));
        setAnswers(map);
      } catch {}
    }
    if (savedMarked) {
      try {
        setMarkedQuestions(new Set(JSON.parse(savedMarked)));
      } catch {}
    }
    if (savedIndex) {
      setCurrentIndex(Number(savedIndex));
    }
  }, [examId, examData]);

  // Clean up sessionStorage on unload or submit
  useEffect(() => {
    return () => {
      // Don't clean up here - user might refresh
    };
  }, []);

  // Update elapsed seconds every 10s
  useEffect(() => {
    if (!examData || submitting) return;
    const interval = setInterval(() => {
      elapsedRef.current = Math.floor((Date.now() - startTimeRef.current) / 1000);
    }, 10000);
    return () => clearInterval(interval);
  }, [examData, submitting]);

  const currentQuestion = examData?.questions?.[currentIndex] || null;

  const handleSelect = useCallback((keys: string[]) => {
    if (!currentQuestion) return;
    setAnswers((prev) => {
      const next = new Map(prev);
      next.set(currentQuestion.id, keys);
      return next;
    });
  }, [currentQuestion]);

  const handleMark = useCallback(() => {
    if (!currentQuestion) return;
    setMarkedQuestions((prev) => {
      const next = new Set(prev);
      next.has(currentQuestion.id) ? next.delete(currentQuestion.id) : next.add(currentQuestion.id);
      return next;
    });
  }, [currentQuestion]);

  const doSubmit = useCallback(async () => {
    if (!examId || !examData) return;
    setSubmitting(true);
    try {
      const usedSeconds = elapsedRef.current || Math.floor((Date.now() - startTimeRef.current) / 1000);
      const answerList = examData.questions.map((q) => ({
        question_id: q.id,
        selected_keys: answers.get(q.id) || [],
      }));
      await examApi.submit(Number(examId), { answers: answerList, used_seconds: usedSeconds });
      // Clean up sessionStorage on successful submit
      sessionStorage.removeItem(`exam_${examId}`);
      sessionStorage.removeItem(`exam_${examId}_answers`);
      sessionStorage.removeItem(`exam_${examId}_marked`);
      sessionStorage.removeItem(`exam_${examId}_index`);
      navigate(`/exam/${examId}/result`, { replace: true });
    } catch {
      alert('提交失败，请重试');
    } finally {
      setSubmitting(false);
      setShowConfirm(false);
    }
  }, [examId, examData, answers, navigate]);

  // Auto-submit on timeout
  const handleTimeout = useCallback(() => {
    elapsedRef.current = examData ? examData.duration_min * 60 : 0;
    doSubmit();
  }, [examData, doSubmit]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-gray-400 text-lg animate-pulse">加载考试数据...</div>
      </div>
    );
  }

  if (!examData || !currentQuestion) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">📝</div>
          <p className="text-gray-500 mb-6 text-lg">请先选择认证并创建考试</p>
          <button onClick={() => navigate('/dashboard')} className="px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors text-lg font-medium">
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const unansweredCount = examData.questions.filter((q) => !answers.has(q.id)).length;

  return (
    <div className="space-y-4">
      {/* Top bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-center justify-between sticky top-0 z-10">
        <div>
          <h1 className="font-semibold text-gray-900">{examData.certification?.name || '模拟考试'}</h1>
          <p className="text-sm text-gray-500">第 {currentIndex + 1}/{examData.questions.length} 题</p>
        </div>
        <div className="flex items-center space-x-4">
          <TimerDisplay
            totalSeconds={examData.duration_min * 60}
            startTimeRef={startTimeRef}
            onTimeout={handleTimeout}
          />
          <button
            onClick={() => setShowConfirm(true)}
            disabled={submitting}
            className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all"
          >
            {submitting ? '提交中...' : '交卷'}
          </button>
        </div>
      </div>

      {/* Question */}
      {currentQuestion && (
        <QuestionCard
          key={currentQuestion.id}
          content={currentQuestion.content}
          questionType={currentQuestion.question_type}
          options={currentQuestion.options}
          selectedKeys={answers.get(currentQuestion.id) || []}
          onSelect={handleSelect}
          isMarked={markedQuestions.has(currentQuestion.id)}
          onMark={handleMark}
        />
      )}

      {/* Prev / Next buttons */}
      <div className="flex items-center justify-between bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <button
          onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
          disabled={currentIndex === 0}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
        >
          ← 上一题
        </button>
        <span className="text-sm text-gray-500">
          已答 {answers.size}/{examData.total_questions} 题 · 未答 {unansweredCount} 题
        </span>
        <button
          onClick={() => setCurrentIndex((i) => Math.min(examData.questions.length - 1, i + 1))}
          disabled={currentIndex === examData.questions.length - 1}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed font-medium"
        >
          下一题 →
        </button>
      </div>

      {/* Question navigator grid */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-4 text-sm">
            <span className="flex items-center"><span className="w-3 h-3 bg-blue-500 rounded mr-1"></span> 已答</span>
            <span className="flex items-center"><span className="w-3 h-3 bg-yellow-400 rounded mr-1"></span> 标记</span>
            <span className="flex items-center"><span className="w-3 h-3 bg-gray-200 rounded mr-1"></span> 未答</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto">
          {examData.questions.map((q, idx) => {
            const isAnswered = answers.has(q.id);
            const isMarked = markedQuestions.has(q.id);
            const isCurrent = idx === currentIndex;
            return (
              <button
                key={q.id}
                onClick={() => setCurrentIndex(idx)}
                className={`w-10 h-10 text-sm font-medium rounded-lg transition-all shrink-0 ${
                  isCurrent ? 'ring-2 ring-blue-500 ring-offset-2' : ''
                } ${
                  isAnswered
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : isMarked
                    ? 'bg-yellow-400 text-white hover:bg-yellow-500'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Submit confirmation dialog */}
      {showConfirm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setShowConfirm(false)}>
          <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
            <div className="text-center">
              <div className="text-5xl mb-4">📤</div>
              <h2 className="text-xl font-bold text-gray-900 mb-2">确认交卷</h2>
              <p className="text-gray-500 mb-2">你还有 <span className="font-bold text-orange-500">{unansweredCount}</span> 道题未作答</p>
              <p className="text-gray-400 text-sm mb-6">交卷后无法修改答案</p>
              <div className="flex space-x-3">
                <button onClick={() => setShowConfirm(false)} className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 font-medium">
                  继续答题
                </button>
                <button onClick={doSubmit} disabled={submitting} className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 font-medium disabled:opacity-50">
                  {submitting ? '提交中...' : '确认交卷'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Inline timer that reads from startTimeRef for accuracy */
function TimerDisplay({ totalSeconds, startTimeRef, onTimeout }: {
  totalSeconds: number;
  startTimeRef: React.MutableRefObject<number>;
  onTimeout: () => void;
}) {
  const [display, setDisplay] = useState('');
  const firedRef = useRef(false);

  useEffect(() => {
    firedRef.current = false;
    const tick = () => {
      const elapsed = Math.floor((Date.now() - startTimeRef.current) / 1000);
      const remaining = Math.max(0, totalSeconds - elapsed);
      const h = Math.floor(remaining / 3600);
      const m = Math.floor((remaining % 3600) / 60);
      const s = remaining % 60;
      setDisplay(`${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
      if (remaining <= 0 && !firedRef.current) {
        firedRef.current = true;
        onTimeout();
      }
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [totalSeconds, startTimeRef, onTimeout]);

  const [h, m, s] = display.split(':').map(Number);
  const isDanger = h === 0 && m === 0 && s < 60;
  const isWarning = h === 0 && m < 5;

  return (
    <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-mono text-lg font-bold ${
      isDanger ? 'bg-red-100 text-red-600 animate-pulse' :
      isWarning ? 'bg-yellow-100 text-yellow-700' :
      'bg-gray-100 text-gray-700'
    }`}>
      <span>⏱</span>
      <span>{display}</span>
    </div>
  );
}
