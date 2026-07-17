import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { knowledgeApi } from '../api';
import type { KnowledgeDetail } from '../types';

export default function KnowledgeDetailPage() {
  const { articleId } = useParams<{ articleId: string }>();
  const [article, setArticle] = useState<KnowledgeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!articleId) return;
    knowledgeApi.detail(Number(articleId)).then((res) => {
      setArticle(res.data.data);
    }).catch(() => {
      // ignore
    }).finally(() => setLoading(false));
  }, [articleId]);

  if (loading) {
    return <div className="text-center py-16 text-gray-400 animate-pulse">加载文章...</div>;
  }

  if (!article) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-500 mb-4">文章不存在</p>
        <Link to="/knowledge" className="text-blue-600 hover:underline">返回知识库</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <Link to="/knowledge" className="text-blue-600 hover:underline text-sm">← 返回知识库</Link>
      </div>
      <article className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-8 border-b border-gray-100">
          <div className="flex items-center space-x-2 mb-4">
            {article.provider && (
              <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full text-xs font-medium">
                {article.provider.toUpperCase()}
              </span>
            )}
            <span className="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">
              {article.category}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{article.title}</h1>
          {article.summary && (
            <p className="text-gray-500 mt-2">{article.summary}</p>
          )}
          <div className="flex items-center space-x-4 mt-4 text-sm text-gray-400">
            <span>👁 {article.view_count} 阅读</span>
            <span>👍 {article.like_count} 点赞</span>
            {article.published_at && <span>📅 {new Date(article.published_at).toLocaleDateString()}</span>}
          </div>
        </div>
        <div className="p-8 prose max-w-none">
          {article.content.split('\n').map((line, i) => {
            if (line.startsWith('## ')) return <h2 key={i} className="text-xl font-bold mt-6 mb-3 text-gray-900">{line.slice(3)}</h2>;
            if (line.startsWith('- ')) return <li key={i} className="text-gray-700 ml-4">{line.slice(2)}</li>;
            if (line.trim() === '') return <br key={i} />;
            return <p key={i} className="text-gray-700 leading-relaxed mb-2">{line}</p>;
          })}
        </div>
        {article.source_url && (
          <div className="px-8 pb-6">
            <a href={article.source_url} target="_blank" rel="noopener noreferrer"
              className="text-blue-600 hover:underline text-sm">
              🔗 原文链接
            </a>
          </div>
        )}
      </article>
    </div>
  );
}
