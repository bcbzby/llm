import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { reportApi } from '../api';
import type { ReportResponse } from '../types';
import RadarChart from '../components/RadarChart';

export default function Report() {
  const { examId } = useParams<{ examId: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!examId) return;
    reportApi.get(Number(examId)).then((res) => {
      setReport(res.data.data);
    }).finally(() => setLoading(false));
  }, [examId]);

  if (loading) {
    return <div className="text-center py-16 text-gray-400">生成评估报告...</div>;
  }

  if (!report) {
    return <div className="text-center py-16 text-gray-400">报告数据不存在</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* 报告头部 */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">📊 考试报告</h1>
        <p className="text-gray-500 mt-1">
          {report.exam_summary.title || '模拟考试'} · {report.exam_summary.correct_rate} 正确率
        </p>
      </div>

      {/* 成绩摘要 */}
      <div className={`rounded-2xl p-6 ${
        report.exam_summary.is_passed
          ? 'bg-gradient-to-r from-green-500 to-emerald-600'
          : 'bg-gradient-to-r from-orange-500 to-red-600'
      } text-white text-center`}>
        <div className="text-5xl font-bold">{report.exam_summary.score}</div>
        <div className="text-xl opacity-90">/ {report.exam_summary.total_score}</div>
        <div className="mt-2 text-lg">
          {report.exam_summary.is_passed ? '✅ 恭喜通过！' : '❌ 未通过'}
          {!report.exam_summary.is_passed && report.exam_summary.gap_to_pass > 0 && (
            <span className="ml-2 opacity-80">距离及格还差 {report.exam_summary.gap_to_pass} 分</span>
          )}
        </div>
      </div>

      {/* 雷达图 + 科目分析 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">🎯 科目能力雷达</h2>
          <RadarChart
            data={report.subject_breakdown.map((s) => ({
              subject: s.subject_name,
              correctRate: parseFloat(s.correct_rate),
              weight: s.weight,
            }))}
          />
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">📊 科目正确率</h2>
          <div className="space-y-4">
            {report.subject_breakdown.map((s) => (
              <div key={s.subject_id}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700">{s.subject_name}</span>
                  <span className="font-medium">{s.correct_rate}</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all"
                    style={{ width: s.correct_rate || '0%' }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  {s.correct}/{s.total} 题 · 权重 {s.weight}%
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 薄弱环节 */}
      {report.weakness_tags.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">⚠️ 薄弱环节</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.weakness_tags.map((wt) => (
              <div key={wt.tag_id} className="p-4 bg-red-50 rounded-lg border border-red-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-red-800">{wt.tag_name}</span>
                  <span className="text-red-600 font-bold">{wt.correct_rate}</span>
                </div>
                <p className="text-sm text-red-600">{wt.suggested_action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 优势领域 */}
      {report.strength_tags.length > 0 && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">✅ 优势领域</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {report.strength_tags.map((st) => (
              <div key={st.tag_id} className="p-4 bg-green-50 rounded-lg border border-green-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-green-800">{st.tag_name}</span>
                  <span className="text-green-600 font-bold">{st.correct_rate}</span>
                </div>
                <p className="text-sm text-green-600">{st.suggested_action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex justify-center space-x-4 pb-8">
        <button
          onClick={() => navigate(`/exam/${examId}/result`)}
          className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition-all"
        >
          查看答题详情
        </button>
        <button
          onClick={() => navigate('/dashboard')}
          className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all"
        >
          返回首页
        </button>
      </div>
    </div>
  );
}
