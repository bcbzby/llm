import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { certApi, examApi } from '../api';
import type { Certification, ExamHistoryItem } from '../types';
import { useAuthStore } from '../store/authStore';

export default function Dashboard() {
  const { user } = useAuthStore();
  const [certs, setCerts] = useState<Certification[]>([]);
  const [examHistory, setExamHistory] = useState<ExamHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      certApi.list(),
      examApi.history(),
    ]).then(([certRes, examRes]) => {
      if (cancelled) return;
      setCerts(certRes.data.data || []);
      setExamHistory(examRes.data.data || []);
    }).catch(() => {
      if (!cancelled) {
        setCerts([]);
        setExamHistory([]);
      }
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  const passedCount = examHistory.filter((e) => e.is_passed).length;
  const avgScore = examHistory.length
    ? Math.round(examHistory.reduce((s, e) => s + e.score, 0) / examHistory.length)
    : 0;

  return (
    <div className="space-y-8">
      {/* 欢迎区域 */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <h1 className="text-2xl font-bold">👋 欢迎回来，{user?.nickname}！</h1>
        <p className="mt-2 text-blue-100">继续你的云认证学习之旅</p>
      </div>

      {/* 学习统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: '考试次数', value: examHistory.length, color: 'blue', icon: '📝' },
          { label: '通过次数', value: passedCount, color: 'green', icon: '✅' },
          { label: '平均分', value: avgScore, color: 'purple', icon: '📊' },
          { label: '连续学习', value: '0 天', color: 'orange', icon: '🔥' },
        ].map((stat) => (
          <div key={stat.label} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
              </div>
              <span className="text-2xl">{stat.icon}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 目标认证 */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">🎯 目标认证</h2>
        </div>
        {loading ? (
          <div className="text-center py-8 text-gray-400">加载中...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {certs.map((cert) => (
              <div key={cert.id} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                <div className="flex items-start space-x-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-xl">
                    {cert.provider === 'aws' ? '☁️' : '🔷'}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">{cert.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{cert.provider.toUpperCase()} · {cert.level}</p>
                    <div className="flex items-center space-x-4 mt-3 text-sm text-gray-500">
                      <span>📝 {cert.total_questions} 题</span>
                      <span>⏱ {cert.duration_min} 分钟</span>
                      <span>🎯 {cert.pass_score} 分通过</span>
                    </div>
                    <Link
                      to={`/exam/new/${cert.id}`}
                      className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      开始模拟考试
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 考试历史 */}
      {examHistory.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📋 最近考试</h2>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">考试</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">得分</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">结果</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {examHistory.slice(0, 5).map((exam) => (
                  <tr key={exam.exam_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{exam.title || '模拟考试'}</td>
                    <td className="px-6 py-4 text-sm font-medium">{exam.score}/{exam.total_score}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        exam.is_passed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {exam.is_passed ? '✅ 通过' : '❌ 未通过'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {exam.completed_at ? new Date(exam.completed_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        to={`/exam/${exam.exam_id}/result`}
                        className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                      >
                        查看详情 →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
