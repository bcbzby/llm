import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ExamList from './pages/ExamList';
import ExamTaking from './pages/ExamTaking';
import ExamResult from './pages/ExamResult';
import Report from './pages/Report';
import WrongBook from './pages/WrongBook';
import KnowledgeBase from './pages/KnowledgeBase';
import KnowledgeDetail from './pages/KnowledgeDetail';
import PracticeQuestions from './pages/PracticeQuestions';
import Contribute from './pages/Contribute';
import AdminReview from './pages/AdminReview';
import { useAuthStore } from './store/authStore';

function App() {
  const { loadFromStorage } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* 受保护路由 */}
          <Route path="/dashboard" element={
            <ProtectedRoute><Dashboard /></ProtectedRoute>
          } />
          <Route path="/certifications" element={
            <ProtectedRoute><Dashboard /></ProtectedRoute>
          } />
          <Route path="/questions" element={
            <ProtectedRoute><PracticeQuestions /></ProtectedRoute>
          } />
          <Route path="/exam/new/:certId" element={
            <ProtectedRoute><ExamList /></ProtectedRoute>
          } />
          <Route path="/exam/:examId/taking" element={
            <ProtectedRoute><ExamTaking /></ProtectedRoute>
          } />
          <Route path="/exam/:examId/result" element={
            <ProtectedRoute><ExamResult /></ProtectedRoute>
          } />
          <Route path="/report/:examId" element={
            <ProtectedRoute><Report /></ProtectedRoute>
          } />
          <Route path="/wrong-book" element={
            <ProtectedRoute><WrongBook /></ProtectedRoute>
          } />
          <Route path="/knowledge" element={
            <ProtectedRoute><KnowledgeBase /></ProtectedRoute>
          } />
          <Route path="/knowledge/:articleId" element={
            <ProtectedRoute><KnowledgeDetail /></ProtectedRoute>
          } />
          <Route path="/contribute" element={
            <ProtectedRoute><Contribute /></ProtectedRoute>
          } />
          <Route path="/admin/review" element={
            <ProtectedRoute><AdminReview /></ProtectedRoute>
          } />

          {/* 默认重定向 */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
