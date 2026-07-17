import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { certApi, examApi } from '../api';
import type { Certification } from '../types';

export default function ExamSetup() {
  const { certId } = useParams<{ certId: string }>();
  const navigate = useNavigate();
  const [cert, setCert] = useState<Certification | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    certApi.list().then((res) => {
      const found = (res.data.data || []).find((c: Certification) => c.id === Number(certId));
      if (found) {
        setCert(found);
      }
    });
  }, [certId]);

  if (!cert) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400 animate-pulse">加载认证信息...</div>
      </div>
    );
  }

  const handleStart = async () => {
    setCreating(true);
    try {
      const res = await examApi.create({
        certification_id: Number(certId),
        exam_type: 'mock',
        question_count: cert.total_questions,
        duration_min: cert.duration_min,
      });
      const examData = res.data.data;
      navigate(`/exam/${examData.exam_id}/taking`, { state: { examData } });
    } catch (err) {
      alert('创建考试失败，请重试');
      setCreating(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-16 h-16 bg-blue-100 rounded-xl flex items-center justify-center text-2xl">☁️</div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{cert.name}</h1>
            <p className="text-sm text-gray-500">{cert.provider.toUpperCase()} · {cert.level}</p>
            <p className="text-xs text-gray-400 mt-1">{cert.description}</p>
          </div>
        </div>

        {/* Fixed stats — not editable */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="p-4 bg-blue-50 rounded-lg text-center">
            <p className="text-2xl font-bold text-blue-600">{cert.total_questions}</p>
            <p className="text-sm text-gray-600">官方题量</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg text-center">
            <p className="text-2xl font-bold text-green-600">{cert.duration_min}</p>
            <p className="text-sm text-gray-600">考试时长(分钟)</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg text-center">
            <p className="text-2xl font-bold text-purple-600">{cert.pass_score}</p>
            <p className="text-sm text-gray-600">通过分数</p>
          </div>
        </div>

        {/* Subject breakdown */}
        {cert.subjects && cert.subjects.length > 0 && (
          <div className="mb-8">
            <h3 className="font-medium text-gray-900 mb-3">📂 科目分布</h3>
            <div className="space-y-2">
              {cert.subjects.map((s) => (
                <div key={s.id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{s.name}</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-32 bg-gray-100 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${s.weight}%` }} />
                    </div>
                    <span className="text-gray-400 w-8 text-right">{s.weight}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={handleStart}
          disabled={creating}
          className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all text-lg"
        >
          {creating ? '创建中...' : '🚀 开始考试'}
        </button>
      </div>
    </div>
  );
}
