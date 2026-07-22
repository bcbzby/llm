import { useState, useEffect, useCallback, useRef } from 'react';
import { questionApi, certApi } from '../api';
import type { Question, Certification } from '../types';
import QuestionCard from '../components/QuestionCard';
import { useLangStore } from '../store/langStore';

export default function PracticeQuestions() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [certs, setCerts] = useState<Certification[]>([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [selectedCert, setSelectedCert] = useState<number | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [questionCount, setQuestionCount] = useState(10);

  // Quiz state
  const [phase, setPhase] = useState<'setup' | 'quiz' | 'result'>('setup');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Map<number, string[]>>(new Map());
  const [correctMap, setCorrectMap] = useState<Map<number, boolean>>(new Map());
  // Store correct keys and explanations per question for result display
  const correctKeysRef = useRef<Map<number, string[]>>(new Map());
  const explanationRef = useRef<Map<number, string>>(new Map());
  // Track used question IDs to avoid repeats across sessions
  const usedIdsRef = useRef<Set<number>>(new Set());

  // Timer
  const [startTime, setStartTime] = useState(0);

  useEffect(() => {
    certApi.list().then((res) => setCerts(res.data.data || []));
  }, []);

  const loadQuestions = useCallback(async () => {
    setLoading(true);
    try {
      const { lang } = useLangStore.getState();
      const params: any = {
        // 交由后端在整个题库中随机抽题，避免只在最新的一页里选而导致重复
        random_sample: true,
        page_size: questionCount,
        lang,
      };
      if (selectedDifficulty !== 'all') params.difficulty = selectedDifficulty;
      if (selectedCert) params.certification_id = selectedCert;

      // 排除已经出过的题目（尽量不重复），若剩余不足则由后端自动放宽
      const excluded = [...usedIdsRef.current];
      if (excluded.length > 0) params.exclude_ids = excluded.join(',');

      let res = await questionApi.list(params);
      let picked = res.data.data?.items || [];

      // 若因排除历史题导致数量不足，去掉排除条件再抽一次，保证题量
      if (picked.length < questionCount) {
        delete params.exclude_ids;
        res = await questionApi.list(params);
        picked = res.data.data?.items || [];
      }

      setQuestions(picked);
      return picked;
    } catch (err) {
      console.error('Failed to load questions:', err);
      return [];
    } finally {
      setLoading(false);
    }
  }, [selectedCert, selectedDifficulty, questionCount]);

  const handleStart = async () => {
    const picked = await loadQuestions();
    if (picked.length === 0) return;
    setAnswers(new Map());
    setCorrectMap(new Map());
    correctKeysRef.current = new Map();
    explanationRef.current = new Map();
    setCurrentIndex(0);
    setStartTime(Date.now());
    setPhase('quiz');
  };

  const currentQ = questions[currentIndex] || null;

  const handleSelect = (keys: string[]) => {
    if (!currentQ || phase !== 'quiz') return;
    setAnswers((prev) => {
      const next = new Map(prev);
      next.set(currentQ.id, keys);
      return next;
    });
  };

  const handleFinish = async () => {
    setLoading(true);
    const answeredIds = [...answers.keys()];
    const correctKeysMap = new Map<number, string[]>();
    const explanationMap = new Map<number, string>();
    const correctnessMap = new Map<number, boolean>();

    for (let i = 0; i < answeredIds.length; i += 10) {
      const batch = answeredIds.slice(i, i + 10);
      const results = await Promise.allSettled(
        batch.map((id) => questionApi.detail(id))
      );
      results.forEach((r, idx) => {
        if (r.status === 'fulfilled') {
          const qd = r.value.data.data;
          correctKeysMap.set(batch[idx], qd.correct_keys || []);
          explanationMap.set(batch[idx], qd.explanation || '');
        }
      });
    }

    for (const [qid, selected] of answers) {
      const correct = correctKeysMap.get(qid) || [];
      const isCorrect = selected.length > 0 &&
        selected.length === correct.length &&
        selected.every((k) => correct.includes(k));
      correctnessMap.set(qid, isCorrect);
    }

    // Store correct keys and explanations for result display
    correctKeysRef.current = correctKeysMap;
    explanationRef.current = explanationMap;
    setCorrectMap(correctnessMap);
    setLoading(false);
    setPhase('result');
  };

  const correctCount = [...correctMap.values()].filter(Boolean).length;
  const wrongCount = [...correctMap.values()].filter((v) => !v).length;
  const unansweredCount = questions.length - correctMap.size;
  const score = questions.length > 0 ? Math.round((correctCount / questions.length) * 100) : 0;

  // --- Result screen ---
  if (phase === 'result') {
    const passed = score >= 70;
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <div className={`rounded-2xl p-8 text-white text-center ${
          passed ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-orange-500 to-red-600'
        }`}>
          <div className="text-6xl mb-4">{passed ? '🎉' : '💪'}</div>
          <div className="text-5xl font-bold mb-2">{score}%</div>
          <p className="text-xl opacity-90">{passed ? '太棒了，继续加油！' : '继续努力，多练习！'}</p>
          <p className="mt-2 opacity-80">
            正确 {correctCount} / {questions.length} 题
            {wrongCount > 0 && ` · 错误 ${wrongCount} 题`}
            {unansweredCount > 0 && ` · 未答 ${unansweredCount} 题`}
          </p>
          <p className="text-sm mt-2 opacity-70">
            用时 {Math.floor((Date.now() - startTime) / 60000)} 分 {Math.floor((Date.now() - startTime) / 1000) % 60} 秒
          </p>
          <div className="flex justify-center space-x-4 mt-6">
            {/* Re-practice: same questions */}
            <button onClick={() => setPhase('setup')} className="px-6 py-2 bg-white/20 rounded-xl hover:bg-white/30 transition font-medium">
              🔄 再练一次
            </button>
            {/* New questions: mark current as used, retry */}
            <button
              onClick={async () => {
                questions.forEach((q) => usedIdsRef.current.add(q.id));
                setPhase('setup');
                const picked = await loadQuestions();
                if (picked.length === 0) return;
                setAnswers(new Map());
                setCorrectMap(new Map());
                correctKeysRef.current = new Map();
                setCurrentIndex(0);
                setStartTime(Date.now());
                setPhase('quiz');
              }}
              className="px-6 py-2 bg-white/20 rounded-xl hover:bg-white/30 transition font-medium"
            >
              📝 重新出题（不重复）
            </button>
          </div>
        </div>

        {/* Detailed review with correct answers shown directly */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">📋 答题回顾</h2>
          {questions.map((q, idx) => {
            const selected = answers.get(q.id) || [];
            const isCorrect = correctMap.get(q.id);
            const correctKeys = correctKeysRef.current.get(q.id) || [];
            return (
              <div key={q.id} className={`border-l-4 ${isCorrect ? 'border-green-500' : selected.length === 0 ? 'border-gray-300' : 'border-red-500'} bg-white rounded-r-xl shadow-sm`}>
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-400">第 {idx + 1} 题</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      isCorrect === undefined ? 'bg-gray-100 text-gray-500' :
                      isCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {isCorrect === undefined ? '未答' : isCorrect ? '正确' : '错误'}
                    </span>
                  </div>
                  <p className="text-gray-900 text-sm">{q.content}</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {q.options.map((opt) => {
                      const isSelected = selected.includes(opt.key);
                      const isRight = correctKeys.includes(opt.key);
                      return (
                        <span key={opt.key} className={`inline-flex items-center px-3 py-1 text-xs rounded-full border ${
                          isRight
                            ? 'border-green-500 bg-green-50 text-green-700'
                            : isSelected && !isRight
                            ? 'border-red-500 bg-red-50 text-red-700'
                            : 'border-gray-200 text-gray-500'
                        }`}>
                          {opt.key}. {opt.content}
                          {isRight && ' ✅'}
                          {isSelected && !isRight && ' ❌'}
                        </span>
                      );
                    })}
                  </div>
                  {!isCorrect && correctKeys.length > 0 && (
                    <p className="text-xs text-gray-500 mt-2">
                      正确答案: <span className="text-green-600 font-medium">{correctKeys.join(', ')}</span>
                      {selected.length > 0 && (
                        <> · 你的答案: <span className="text-red-600 font-medium">{selected.join(', ')}</span></>
                      )}
                    </p>
                  )}
                  {/* Show explanation for all questions */}
                  {(() => {
                    const exp = explanationRef.current.get(q.id);
                    if (!exp) return null;
                    return (
                      <div className="mt-2 p-3 bg-blue-50 rounded-lg border border-blue-100">
                        <p className="text-xs font-medium text-blue-800 mb-0.5">💡 解析</p>
                        <p className="text-xs text-blue-700 leading-relaxed">{exp}</p>
                      </div>
                    );
                  })()}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // --- Quiz screen ---
  if (phase === 'quiz') {
    const answeredCount = answers.size;
    const allAnswered = answeredCount === questions.length;
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 flex items-center justify-between sticky top-0 z-10">
          <div>
            <h1 className="font-semibold text-gray-900">📝 刷题练习</h1>
            <p className="text-sm text-gray-500">
              第 {currentIndex + 1}/{questions.length} 题 · 已答 {answeredCount} 题
              {allAnswered && <span className="text-green-600 ml-2">✅ 全部答完</span>}
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-32 bg-gray-100 rounded-full h-2">
              <div className="bg-blue-500 h-2 rounded-full transition-all" style={{ width: `${(answeredCount / questions.length) * 100}%` }} />
            </div>
            <button onClick={handleFinish}
              className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 font-medium"
            >
              {allAnswered ? '✅ 完成答题' : '结束答题'}
            </button>
          </div>
        </div>

        {currentQ && (
          <QuestionCard
            key={currentQ.id}
            content={currentQ.content}
            questionType={currentQ.question_type}
            options={currentQ.options}
            selectedKeys={answers.get(currentQ.id) || []}
            onSelect={handleSelect}
          />
        )}

        <div className="flex items-center justify-between bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <button onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
            disabled={currentIndex === 0}
            className="px-5 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-40 text-sm font-medium">
            ← 上一题
          </button>
          <span className="text-sm text-gray-500">{currentIndex + 1} / {questions.length}</span>
          <button onClick={() => setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))}
            disabled={currentIndex === questions.length - 1}
            className="px-5 py-2 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-40 text-sm font-medium">
            下一题 →
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <p className="text-sm text-gray-500 mb-2">题目导航</p>
          <div className="flex flex-wrap gap-2">
            {questions.map((q, idx) => (
              <button key={q.id} onClick={() => setCurrentIndex(idx)}
                className={`w-9 h-9 text-xs font-medium rounded-lg ${
                  idx === currentIndex ? 'ring-2 ring-blue-500 ring-offset-1' : ''
                } ${answers.has(q.id) ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {idx + 1}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // --- Setup screen ---
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center">
        <div className="text-6xl mb-4">📝</div>
        <h1 className="text-2xl font-bold text-gray-900">刷题练习</h1>
        <p className="text-gray-500 mt-1">随机选题，巩固云认证知识</p>
      </div>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">选择认证</label>
          <select value={selectedCert ?? ''}
            onChange={(e) => setSelectedCert(e.target.value ? Number(e.target.value) : null)}
            className="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm">
            <option value="">全部认证（混合出题）</option>
            {certs.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">难度</label>
          <div className="flex space-x-2">
            {[{k:'all',l:'全部'},{k:'easy',l:'简单'},{k:'medium',l:'中等'},{k:'hard',l:'困难'}].map((d) => (
              <button key={d.k} onClick={() => setSelectedDifficulty(d.k)}
                className={`flex-1 py-3 rounded-xl text-sm font-medium transition-all ${selectedDifficulty === d.k ? 'bg-blue-600 text-white shadow' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {d.l}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">题目数量</label>
          <div className="flex space-x-2">
            {[5, 10, 20, 50].map((n) => (
              <button key={n} onClick={() => setQuestionCount(n)}
                className={`flex-1 py-3 rounded-xl text-sm font-medium ${questionCount === n ? 'bg-purple-600 text-white shadow' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                {n} 题
              </button>
            ))}
          </div>
        </div>

        <button onClick={handleStart} disabled={loading}
          className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all text-lg">
          {loading ? '加载中...' : '🚀 开始刷题'}
        </button>
      </div>
    </div>
  );
}
