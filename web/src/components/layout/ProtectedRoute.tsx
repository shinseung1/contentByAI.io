import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export function ProtectedRoute() {
  const accessToken = useAuthStore((state) => state.accessToken);
  
  return accessToken ? <Outlet /> : <Navigate to="/login" replace />;
}

export function AdminRoute() {
  const { accessToken, user } = useAuthStore.getState();
  
  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }
  
  if (user?.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <Outlet />;
}