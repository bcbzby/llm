import { useState, useEffect } from 'react';
import { contributeApi } from '../api';
import type { Subject } from '../types';

interface CertGroup {
  cert_id: number;
  cert_name: string;
  subjects: Subject[];
}

interface OptionField {
  key: string;
  content: string;
  is_correct: boolean;
}

const DEFAULT_OPTIONS: OptionField[] = [
  { key: 'A', content: '', is_correct: false },
  { key: 'B', content: '', is_correct: false },
  { key: 'C', content: '', is_correct: false },
  { key: 'D', content: '', is_correct: false },
];

export default function ContributePage() {
  const [certGroups, setCertGroups] = useState<CertGroup[]>([]);
  const [loadingSubjects, setLoadingSubjects] = useState(true);
  const [form, setForm] = useState({
    subject_id: 0,
    question_type: 'single_choice',
    difficulty: 'medium',
    content: '',
    explanation: '',
    tags: '',
    options: [...DEFAULT_OPTIONS],
  });
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    contributeApi.subjects().then((res) => {
      setCertGroups(res.data.data || []);
    }).catch((err) => {
      const detail = err.response?.data?.detail || err.message || '';
      setMessage({ type: 'error', text: `加载科目列表失败: ${detail}` });
    }).finally(() => setLoadingSubjects(false));
  }, []);

  // Reset options when switching type
  useEffect(() => {
    if (form.question_type === 'single_choice') {
      setForm((prev) => ({ ...prev, options: [...DEFAULT_OPTIONS] }));
    } else {
      setForm((prev) => {
        if (prev.options.length < 5) {
          const newOpts = [...prev.options];
          while (newOpts.length < 5) {
            const key = String.fromCharCode(65 + newOpts.length);
            newOpts.push({ key, content: '', is_correct: false });
          }
          return { ...prev, options: newOpts };
        }
        return prev;
      });
    }
  }, [form.question_type]);

  const addOption = () => {
    const keys = form.options.map((o) => o.key);
    for (let i = 0; i < 26; i++) {
      const letter = String.fromCharCode(65 + i);
      if (!keys.includes(letter)) {
        setForm({ ...form, options: [...form.options, { key: letter, content: '', is_correct: false }] });
        return;
      }
    }
  };

  const removeOption = (key: string) => {
    // Minimum 4 for multi_choice
    if (form.options.length <= 4) return;
    setForm({ ...form, options: form.options.filter((o) => o.key !== key) });
  };

  const updateOption = (idx: number, field: 'content' | 'is_correct', value: string | boolean) => {
    const newOpts = form.options.map((o) => ({ ...o }));
    if (field === 'is_correct' && form.question_type === 'single_choice') {
      newOpts.forEach((o) => (o.is_correct = false));
    }
    (newOpts[idx] as any)[field] = value;
    if (field === 'is_correct' && form.question_type === 'single_choice') {
      newOpts[idx].is_correct = value as boolean;
    }
    setForm({ ...form, options: newOpts });
  };

  const handleSubmit = async () => {
    if (!form.subject_id) { setMessage({ type: 'error', text: '请选择科目' }); return; }
    if (!form.content.trim()) { setMessage({ type: 'error', text: '请输入题目内容' }); return; }
    if (form.options.some((o) => !o.content.trim())) { setMessage({ type: 'error', text: '请填写所有选项内容' }); return; }
    if (!form.options.some((o) => o.is_correct)) { setMessage({ type: 'error', text: '请至少选择一个正确答案' }); return; }

    setSubmitting(true);
    setMessage(null);
    try {
      await contributeApi.submit({
        subject_id: form.subject_id,
        question_type: form.question_type,
        difficulty: form.difficulty,
        content: form.content,
        explanation: form.explanation,
        tags: form.tags.split(',').map((t) => t.trim()).filter(Boolean),
        options: form.options,
      });
      setMessage({ type: 'success', text: '✅ 题目已提交，待管理员审核！' });
      setForm({
        subject_id: 0, question_type: 'single_choice', difficulty: 'medium',
        content: '', explanation: '', tags: '',
        options: [...DEFAULT_OPTIONS],
      });
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || '提交失败' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="text-center">
        <div className="text-5xl mb-4">✍️</div>
        <h1 className="text-2xl font-bold text-gray-900">贡献题目</h1>
        <p className="text-gray-500 mt-1">提交题目或纠错，帮助大家共同进步</p>
      </div>

      {message && (
        <div className={`p-4 rounded-xl text-sm font-medium ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">认证科目 *</label>
            <select value={form.subject_id} onChange={(e) => setForm({ ...form, subject_id: Number(e.target.value) })}
              className={`w-full px-3 py-2.5 border rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none ${!form.subject_id && !loadingSubjects ? 'border-red-300' : 'border-gray-300'}`}
              disabled={loadingSubjects}>
              <option value={0}>{loadingSubjects ? '加载中...' : '-- 请选择科目 --'}</option>
              {certGroups.map((g) => (
                <optgroup key={g.cert_id} label={g.cert_name}>
                  {g.subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                </optgroup>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">题型 *</label>
            <select value={form.question_type} onChange={(e) => setForm({ ...form, question_type: e.target.value })}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm">
              <option value="single_choice">单选题（四选一）</option>
              <option value="multi_choice">多选题（自定义选项数量）</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">难度</label>
          <div className="flex space-x-2">
            {[{k:'easy',l:'简单'},{k:'medium',l:'中等'},{k:'hard',l:'困难'}].map((d) => (
              <button key={d.k} onClick={() => setForm({...form, difficulty: d.k})}
                className={`flex-1 py-2.5 rounded-xl text-sm font-medium transition-all ${form.difficulty === d.k ? 'bg-blue-600 text-white shadow' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>{d.l}</button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">题目内容 *</label>
          <textarea value={form.content} onChange={(e) => setForm({...form, content: e.target.value})}
            rows={4} placeholder="描述一个真实场景，然后提出问题..."
            className="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm resize-y focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">选项 *</label>
            {form.question_type === 'multi_choice' && (
              <button onClick={addOption} className="text-sm text-blue-600 hover:text-blue-700 font-medium">+ 添加选项</button>
            )}
          </div>
          <div className="space-y-2">
            {form.options.map((opt, idx) => (
              <div key={opt.key} className="flex items-center space-x-3">
                <span className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-100 text-sm font-bold text-gray-600 flex-shrink-0">{opt.key}</span>
                <input type="text" value={opt.content}
                  onChange={(e) => updateOption(idx, 'content', e.target.value)}
                  placeholder={`选项 ${opt.key} 的内容`}
                  className="flex-1 px-3 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
                <label className={`flex items-center space-x-1.5 text-sm cursor-pointer whitespace-nowrap px-3 py-2 rounded-xl border transition-all ${opt.is_correct ? 'border-green-400 bg-green-50 text-green-700' : 'border-gray-200 text-gray-500 hover:border-gray-300'}`}>
                  <input type="checkbox" checked={opt.is_correct}
                    onChange={(e) => updateOption(idx, 'is_correct', e.target.checked)} className="rounded" />
                  <span>正确答案</span>
                </label>
                {/* Only show delete for multi_choice with > 4 options */}
                {form.question_type === 'multi_choice' && form.options.length > 4 && (
                  <button onClick={() => removeOption(opt.key)} className="text-gray-400 hover:text-red-500 text-lg px-1">×</button>
                )}
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            {form.question_type === 'multi_choice'
              ? '多选题：至少勾选 2 个正确答案，可点「+ 添加选项」增加选项（最少保留 4 个）'
              : '单选题：请勾选 1 个正确答案'}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">答案解析（选填）</label>
          <textarea value={form.explanation} onChange={(e) => setForm({...form, explanation: e.target.value})}
            rows={3} placeholder="解释为什么正确答案是对的，错误选项为什么不对..."
            className="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm resize-y focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">知识点标签（选填，逗号分隔）</label>
          <input type="text" value={form.tags} onChange={(e) => setForm({...form, tags: e.target.value})}
            placeholder="例如: EC2, Auto Scaling, 高可用"
            className="w-full px-4 py-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>

        <button onClick={handleSubmit} disabled={submitting}
          className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition-all text-lg">
          {submitting ? '提交中...' : '✍️ 提交题目'}
        </button>
      </div>
    </div>
  );
}
