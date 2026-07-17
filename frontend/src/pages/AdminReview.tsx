import { useState, useEffect } from 'react';
import { contributeApi } from '../api';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

interface ReviewQuestion {
  id: number;
  cert_name: string;
  question_type: string;
  difficulty: string;
  content: string;
  explanation: string;
  options: { key: string; content: string; is_correct: boolean }[];
  submitted_by: string;
  created_at: string;
}

export default function AdminReview() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [tab, setTab] = useState<'pending' | 'published' | 'rejected'>('pending');
  const [questions, setQuestions] = useState<ReviewQuestion[]>([]);
  const [loading, setLoading] = useState(true);

  // Redirect non-admin users
  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  const loadQuestions = () => {
    setLoading(true);
    contributeApi.reviewList(tab)
      .then((res) => setQuestions(res.data.data?.questions || []))
      .catch(() => setQuestions([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (user?.role === 'admin') loadQuestions();
  }, [tab, user]);

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
    try {
      await contributeApi.reviewAction(id, action);
      setQuestions((prev) => prev.filter((q) => q.id !== id));
    } catch {
      alert('操作失败');
    }
  };

  if (!user || user.role !== 'admin') {
    return <div className="text-center py-16 text-gray-400">无权限访问</div>;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">🛡️ 题目审核</h1>
          <p className="text-gray-500 mt-1">审核用户提交的题目</p>
        </div>
        <div className="flex space-x-2">
          {[
            { k: 'pending' as const, l: '待审核' },
            { k: 'published' as const, l: '已通过' },
            { k: 'rejected' as const, l: '已拒绝' },
          ].map((t) => (
            <button key={t.k} onClick={() => setTab(t.k)}
              className={`px-4 py-2 rounded-lg text-sm font-medium ${tab === t.k ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
              {t.l}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400 animate-pulse">加载中...</div>
      ) : questions.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-4">📭</div>
          <p>{tab === 'pending' ? '暂无需审核的题目' : tab === 'published' ? '暂无已通过的题目' : '暂无已拒绝的题目'}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {questions.map((q) => (
            <div key={q.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${
                    q.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                    q.difficulty === 'hard' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                  }`}>
                    {q.difficulty === 'easy' ? '简单' : q.difficulty === 'hard' ? '困难' : '中等'}
                  </span>
                  <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full font-medium">
                    {q.question_type === 'single_choice' ? '单选' : '多选'}
                  </span>
                  <span className="text-xs text-gray-400">{q.cert_name}</span>
                </div>
                <span className="text-xs text-gray-400">
                  {q.submitted_by} · {new Date(q.created_at).toLocaleString('zh-CN')}
                </span>
              </div>

              {/* Content */}
              <p className="text-gray-900">{q.content}</p>

              {/* Options */}
              <div className="space-y-1.5">
                {q.options.map((opt) => (
                  <div key={opt.key} className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm ${
                    opt.is_correct ? 'bg-green-50 border border-green-200' : 'bg-gray-50'
                  }`}>
                    <span className="w-6 h-6 flex items-center justify-center rounded-full bg-white text-xs font-bold border">
                      {opt.key}
                    </span>
                    <span>{opt.content}</span>
                    {opt.is_correct && <span className="text-green-600 text-xs ml-auto font-medium">✅ 正确答案</span>}
                  </div>
                ))}
              </div>

              {/* Explanation */}
              {q.explanation && (
                <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                  💡 {q.explanation}
                </div>
              )}

              {/* Actions */}
              {tab === 'pending' && (
                <div className="flex space-x-3 pt-2">
                  <button onClick={() => handleAction(q.id, 'approve')}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium">
                    ✅ 通过
                  </button>
                  <button onClick={() => handleAction(q.id, 'reject')}
                    className="px-6 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm font-medium">
                    ❌ 拒绝
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
