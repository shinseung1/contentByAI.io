import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import { message } from 'antd';

interface User {
  username: string;
  role: string;
  isActive: boolean;
  expiresAt: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, userData: User) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // 토큰 유효성 검증
  const validateToken = async (authToken: string) => {
    try {
      const response = await axios.get('http://127.0.0.1:3001/api/v1/auth/validate', {
        headers: {
          Authorization: `Bearer ${authToken}`
        }
      });

      if (response.data.valid && response.data.user) {
        setToken(authToken);
        setUser(response.data.user);
        
        // 요청 헤더에 토큰 자동 추가
        axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
        
        return true;
      } else {
        return false;
      }
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  };

  // 앱 시작 시 저장된 토큰 확인
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = localStorage.getItem('authToken');
      
      if (savedToken) {
        const isValid = await validateToken(savedToken);
        if (!isValid) {
          localStorage.removeItem('authToken');
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = (authToken: string, userData: User) => {
    setToken(authToken);
    setUser(userData);
    localStorage.setItem('authToken', authToken);
    axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
    message.success(`${userData.username}님, 환영합니다!`);
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post('http://127.0.0.1:3001/api/v1/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('authToken');
      delete axios.defaults.headers.common['Authorization'];
      message.success('로그아웃 되었습니다');
    }
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};