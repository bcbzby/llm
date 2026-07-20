import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useLangStore } from '../store/langStore';

const NAV_ZH = {
  dashboard: '学习首页', questions: '刷题', wrongBook: '错题本',
  knowledge: '知识库', contribute: '✍️ 贡献题目', review: '🛡️ 审核',
  login: '登录', register: '注册', logout: '退出',
};

const NAV_EN = {
  dashboard: 'Dashboard', questions: 'Practice', wrongBook: 'Wrong Book',
  knowledge: 'Knowledge', contribute: '✍️ Contribute', review: '🛡️ Review',
  login: 'Login', register: 'Register', logout: 'Logout',
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, logout } = useAuthStore();
  const { lang, toggle } = useLangStore();
  const navigate = useNavigate();
  const t = lang === 'zh' ? NAV_ZH : NAV_EN;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center space-x-2">
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  ☁️ CloudCert Pro
                </span>
              </Link>
              {isAuthenticated && (
                <div className="ml-10 flex space-x-4">
                  <Link to="/dashboard" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 rounded-md hover:bg-blue-50">
                    {t.dashboard}
                  </Link>
                  <Link to="/questions" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 rounded-md hover:bg-blue-50">
                    {t.questions}
                  </Link>
                  <Link to="/wrong-book" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 rounded-md hover:bg-blue-50">
                    {t.wrongBook}
                  </Link>
                  <Link to="/knowledge" className="px-3 py-2 text-sm font-medium text-gray-700 hover:text-blue-600 rounded-md hover:bg-blue-50">
                    {t.knowledge}
                  </Link>
                  <Link to="/contribute" className="px-3 py-2 text-sm font-medium text-orange-600 hover:text-orange-700 rounded-md hover:bg-orange-50">
                    {t.contribute}
                  </Link>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-3">
              {isAuthenticated && user?.role === 'admin' && (
                <Link to="/admin/review" className="px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 rounded-md hover:bg-red-50">
                  {t.review}
                </Link>
              )}
              <button
                onClick={toggle}
                className="px-3 py-1.5 text-xs font-medium rounded-full border border-gray-300 text-gray-600 hover:bg-gray-100 transition-colors"
                title={lang === 'zh' ? 'Switch to English' : '切换到中文'}
              >
                {lang === 'zh' ? 'EN' : '中'}
              </button>
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-gray-600">👋 {user?.nickname}</span>
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    {t.logout}
                  </button>
                </>
              ) : (
                <div className="flex space-x-2">
                  <Link to="/login" className="px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg">
                    {t.login}
                  </Link>
                  <Link to="/register" className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg">
                    {t.register}
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
