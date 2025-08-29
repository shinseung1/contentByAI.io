import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './components/layout/MainLayout'
import Dashboard from './pages/Dashboard'
import Generation from './pages/Generation'
import Bundles from './pages/Bundles'
import Publishing from './pages/Publishing'
import Settings from './pages/Settings'
import './App.css'

function App() {
  return (
    <div className="App">
      <Layout style={{ minHeight: '100vh' }}>
        <MainLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/generation" element={<Generation />} />
            <Route path="/bundles" element={<Bundles />} />
            <Route path="/publishing" element={<Publishing />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </MainLayout>
      </Layout>
    </div>
  )
}

export default App