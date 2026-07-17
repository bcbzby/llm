import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { examApi } from '../api';
import type { ExamResultResponse, QuestionOption } from '../types';
import QuestionCard from '../components/QuestionCard';

export default function ExamResult() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<ExamResultResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!examId) return;
    setLoading(true);
    examApi.result(Number(examId)).then((res) => {
      setResult(res.data.data);
    }).catch(() => {
      setError('获取考试结果失败，请刷新重试');
    }).finally(() => setLoading(false));
  }, [examId]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-[60vh]"><div className="text-gray-400 text-lg animate-pulse">加载考试结果...</div></div>;
  }

  if (error || !result) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="text-5xl mb-4">😵</div>
          <p className="text-gray-500 mb-6 text-lg">{error || '考试结果不存在'}</p>
          <Link to="/dashboard" className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700">返回首页</Link>
        </div>
      </div>
    );
  }

  // Build lookup map for all options across all questions
  // The actual options are stored in the backend but not returned as full list in result
  // We infer option labels A,B,C,D from correct_keys + selected_keys

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Score card */}
      <div className={`rounded-2xl p-8 text-white ${
        result.is_passed
          ? 'bg-gradient-to-r from-green-500 to-emerald-600'
          : 'bg-gradient-to-r from-red-500 to-pink-600'
      }`}>
        <div className="text-center">
          <div className="text-6xl mb-4">{result.is_passed ? '🎉' : '😅'}</div>
          <h1 className="text-2xl font-bold mb-2">{result.title || '模拟考试'}</h1>
          <div className="text-6xl font-bold mb-2">{result.score}</div>
          <div className="text-xl opacity-90">/ {result.total_score}</div>
          <div className="mt-4 inline-block px-6 py-2 bg-white/20 rounded-full text-lg font-medium">
            {result.is_passed ? '✅ 通过' : '❌ 未通过'}
          </div>
          {!result.is_passed && result.gap_to_pass > 0 && (
            <p className="mt-2 text-white/80">距离及格还差 {result.gap_to_pass} 分</p>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: '正确', value: result.correct_count, color: 'emerald' },
          { label: '错误', value: result.wrong_count, color: 'red' },
          { label: '未答', value: result.unanswered_count, color: 'gray' },
          { label: '用时', value: `${Math.floor(result.used_seconds / 60)}分${result.used_seconds % 60}秒`, color: 'blue' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl p-4 text-center shadow-sm border border-gray-100">
            <p className={`text-3xl font-bold text-${stat.color}-600`}>{stat.value}</p>
            <p className="text-sm text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Question review */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
          <span>📋 答题回顾</span>
          <span className="text-sm font-normal text-gray-400">
            ({result.correct_count + result.wrong_count}/{result.total_questions} 题)
          </span>
        </h2>
        {result.question_results.map((qr, idx) => {
          const options = qr.options || [];
          // If options not returned (backward compat), infer from keys
          const displayOptions = options.length > 0 ? options : (() => {
            const allKeys = new Set([...qr.correct_keys, ...qr.selected_keys]);
            const sortedKeys = ['A', 'B', 'C', 'D', 'E', 'F'].filter(k => allKeys.has(k));
            return (sortedKeys.length > 0 ? sortedKeys : ['A', 'B', 'C', 'D']).map(k => ({ key: k, content: `Option ${k}` }));
          })();

          return (
            <div key={qr.question_id}>
              <div className="mb-1 text-sm text-gray-400">第 {idx + 1} 题</div>
              <QuestionCard
                content={qr.content}
                questionType={qr.question_type}
                options={displayOptions}
                selectedKeys={qr.selected_keys}
                onSelect={() => {}}
                showResult={true}
                correctKeys={qr.correct_keys}
                explanation={qr.explanation}
              />
            </div>
          );
        })}
      </div>

      {/* Actions */}
      <div className="flex justify-center space-x-4 pb-8">
        <Link
          to={`/report/${examId}`}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all"
        >
          📊 查看详细报告
        </Link>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-all"
        >
          返回首页
        </button>
      </div>
    </div>
  );
}
