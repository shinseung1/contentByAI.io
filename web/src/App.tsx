import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import MainLayout from './components/layout/MainLayout'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import Generation from './pages/Generation'
import GenerationGemini from './pages/GenerationGemini'
import GenerationClaude from './pages/GenerationClaude'
import GenerationOpenAI from './pages/GenerationOpenAI'
import Bundles from './pages/Bundles'
import Publishing from './pages/Publishing'
import Settings from './pages/Settings'
import './App.css'

const AppContent: React.FC = () => {
  const { user, token, login, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh'
      }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user || !token) {
    return <LoginPage onLoginSuccess={login} />;
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <MainLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/generation" element={<Generation />} />
          <Route path="/generation/gemini" element={<GenerationGemini />} />
          <Route path="/generation/claude" element={<GenerationClaude />} />
          <Route path="/generation/openai" element={<GenerationOpenAI />} />
          <Route path="/bundles" element={<Bundles />} />
          <Route path="/publishing" element={<Publishing />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </MainLayout>
    </Layout>
  );
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </div>
  )
}

export default App