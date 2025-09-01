import React from 'react';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import { ProtectedRoute, AdminRoute } from '../components/layout/ProtectedRoute';
import MainLayout from '../components/layout/MainLayout';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Generate from '../pages/Generate';
import Jobs from '../pages/Jobs';
import JobDetail from '../pages/JobDetail';
import Schedule from '../pages/Schedule';
import Posts from '../pages/Posts';
import AdminUsers from '../pages/AdminUsers';
import Settings from '../pages/Settings';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />
  },
  {
    path: '/',
    element: <ProtectedRoute />,
    children: [
      {
        path: '/',
        element: <MainLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: 'dashboard', element: <Dashboard /> },
          { path: 'generate', element: <Generate /> },
          { path: 'jobs', element: <Jobs /> },
          { path: 'jobs/:jobId', element: <JobDetail /> },
          { path: 'schedule', element: <Schedule /> },
          { path: 'posts', element: <Posts /> },
          { path: 'settings', element: <Settings /> },
          {
            path: 'admin',
            element: <AdminRoute />,
            children: [
              { path: 'users', element: <AdminUsers /> }
            ]
          }
        ]
      }
    ]
  }
], {
  future: {
    v7_startTransition: true,
  },
});

export default function AppRouter() {
  return <RouterProvider router={router} />;
}