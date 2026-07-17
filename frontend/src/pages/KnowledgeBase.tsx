import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { knowledgeApi } from '../api';
import type { KnowledgeArticle } from '../types';

const PROVIDERS = ['all', 'aws', 'azure', 'gcp'];
const CATEGORIES = ['all', 'compute', 'storage', 'network', 'database', 'security', 'ai'];

export default function KnowledgeBase() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState('all');
  const [category, setCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      // Clear search: reload from filters
      setLoading(true);
      const params: any = {};
      if (provider !== 'all') params.provider = provider;
      if (category !== 'all') params.category = category;
      knowledgeApi.list(params).then((res) => {
        setArticles(res.data.data?.items || []);
      }).finally(() => setLoading(false));
      return;
    }
    setLoading(true);
    try {
      const res = await knowledgeApi.search(searchQuery);
      setArticles(res.data.data?.items || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  // Reload when filters change
  useEffect(() => {
    setLoading(true);
    const params: any = {};
    if (provider !== 'all') params.provider = provider;
    if (category !== 'all') params.category = category;

    knowledgeApi.list(params).then((res) => {
      setArticles(res.data.data?.items || []);
    }).catch(() => {
      setArticles([]);
    }).finally(() => setLoading(false));
  }, [provider, category]);

  return (
    <div className="space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">📚 知识库</h1>
          <p className="text-gray-500 mt-1">云认证知识学习资源</p>
        </div>
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="🔍 搜索知识..."
            className="w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* 筛选器 */}
      <div className="flex space-x-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">厂商</label>
          <div className="flex space-x-2">
            {PROVIDERS.map((p) => (
              <button
                key={p}
                onClick={() => setProvider(p)}
                className={`px-3 py-1.5 text-sm rounded-lg ${
                  provider === p
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {p === 'all' ? '全部' : p.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">分类</label>
          <div className="flex space-x-2">
            {CATEGORIES.map((c) => (
              <button
                key={c}
                onClick={() => setCategory(c)}
                className={`px-3 py-1.5 text-sm rounded-lg ${
                  category === c
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {c === 'all' ? '全部' : c === 'ai' ? 'AI' : c.charAt(0).toUpperCase() + c.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 文章列表 */}
      {loading ? (
        <div className="text-center py-16 text-gray-400">加载中...</div>
      ) : articles.length === 0 ? (
        <div className="text-center py-16 text-gray-400">暂无文章</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {articles.map((article) => (
            <Link
              key={article.id}
              to={`/knowledge/${article.id}`}
              className="bg-white rounded-xl p-6 shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
            >
              <h3 className="font-semibold text-gray-900 mb-2">{article.title}</h3>
              <p className="text-sm text-gray-500 mb-4 line-clamp-2">{article.summary}</p>
              <div className="flex items-center justify-between text-xs text-gray-400">
                <div className="flex space-x-2">
                  <span className="px-2 py-1 bg-blue-50 text-blue-600 rounded">
                    {article.provider?.toUpperCase()}
                  </span>
                  <span className="px-2 py-1 bg-gray-100 rounded">
                    {article.category}
                  </span>
                </div>
                <div className="flex items-center space-x-3">
                  <span>👁 {article.view_count}</span>
                  <span>👍 {article.like_count}</span>
                  <span>{new Date(article.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
