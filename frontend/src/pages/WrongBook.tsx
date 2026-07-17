import { useState, useEffect } from 'react';
import { wrongBookApi } from '../api';
import type { WrongBookItem } from '../types';
import QuestionCard from '../components/QuestionCard';

export default function WrongBook() {
  const [items, setItems] = useState<WrongBookItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    wrongBookApi.list({
      is_mastered: filter === 'mastered' ? true : filter === 'unmastered' ? false : undefined,
    }).then((res) => {
      setItems(res.data.data?.items || []);
    }).finally(() => setLoading(false));
  }, [filter]);

  const handleMaster = async (id: number) => {
    try {
      await wrongBookApi.markMastered(id);
      setItems((prev) => prev.map((item) =>
        item.id === id ? { ...item, is_mastered: true } : item
      ));
    } catch {
      alert('操作失败');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📕 错题本</h1>
          <p className="text-gray-500 mt-1">共 {items.length} 道错题</p>
        </div>
        <div className="flex space-x-2">
          {[
            { key: 'all', label: '全部' },
            { key: 'unmastered', label: '未掌握' },
            { key: 'mastered', label: '已掌握' },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-4 py-2 text-sm font-medium rounded-lg ${
                filter === f.key
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">加载中...</div>
      ) : items.length === 0 ? (
        <div className="text-center py-16">
          <div className="text-4xl mb-4">🎉</div>
          <p className="text-gray-500">暂无错题，继续保持！</p>
        </div>
      ) : (
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              <QuestionCard
                content={item.question.content}
                questionType={item.question.question_type}
                options={item.question.options}
                selectedKeys={[]}
                onSelect={() => {}}
              />
              <div className="px-6 pb-4 flex items-center justify-between bg-gray-50">
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <span>❌ 错误 {item.wrong_count} 次</span>
                  <span>🕐 {new Date(item.last_wrong_at).toLocaleDateString()}</span>
                  {item.is_mastered && <span className="text-green-600">✅ 已掌握</span>}
                </div>
                {!item.is_mastered && (
                  <button
                    onClick={() => handleMaster(item.id)}
                    className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700"
                  >
                    标记已掌握
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
