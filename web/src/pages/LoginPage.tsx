import React, { useState } from 'react';
import { Form, Input, Button, Card, Alert, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import axios from 'axios';

interface LoginFormValues {
  username: string;
  password: string;
}

interface LoginPageProps {
  onLoginSuccess: (token: string, user: any) => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const onFinish = async (values: LoginFormValues) => {
    setLoading(true);
    setErrorMessage('');

    try {
      const response = await axios.post('http://127.0.0.1:3000/api/v1/auth/login', {
        username: values.username,
        password: values.password
      });

      if (response.data.success) {
        message.success('로그인 성공');
        localStorage.setItem('authToken', response.data.token);
        onLoginSuccess(response.data.token, response.data.user);
      } else {
        setErrorMessage(response.data.message);
      }
    } catch (error: any) {
      console.error('Login error:', error);
      if (error.response?.data?.message) {
        setErrorMessage(error.response.data.message);
      } else if (error.response?.data?.detail) {
        setErrorMessage(error.response.data.detail);
      } else {
        setErrorMessage('로그인 중 오류가 발생했습니다. 서버 연결을 확인해주세요.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page" style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0a0a0a 0%, #1f1f1f 50%, #262626 100%)',
      padding: '20px'
    }}>
      <Card
        title={
          <div style={{
            textAlign: 'center',
            background: 'linear-gradient(135deg, #722ed1, #1890ff)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            fontSize: '24px',
            fontWeight: 'bold',
            marginBottom: '8px'
          }}>
            AI Writer
          </div>
        }
        style={{
          width: 400,
          background: '#262626',
          border: '1px solid #434343',
          borderRadius: '16px',
          boxShadow: '0 12px 40px rgba(0,0,0,0.6)',
        }}
        headStyle={{
          background: '#1f1f1f',
          border: 'none',
          borderRadius: '16px 16px 0 0',
          borderBottom: '1px solid #434343'
        }}
        bodyStyle={{
          background: '#262626',
          borderRadius: '0 0 16px 16px'
        }}
      >
        {errorMessage && (
          <Alert
            message={errorMessage}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}
        
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: '사용자명을 입력해주세요!' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="사용자명"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: '비밀번호를 입력해주세요!' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="비밀번호"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              style={{
                height: '48px',
                fontSize: '16px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #722ed1, #1890ff)',
                border: 'none',
                boxShadow: '0 4px 12px rgba(114, 46, 209, 0.3)',
                transition: 'all 0.3s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 6px 16px rgba(114, 46, 209, 0.4)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(114, 46, 209, 0.3)'
              }}
            >
              로그인
            </Button>
          </Form.Item>
        </Form>

        <div style={{ 
          marginTop: '24px', 
          padding: '16px', 
          background: 'rgba(114, 46, 209, 0.1)', 
          border: '1px solid rgba(114, 46, 209, 0.2)',
          borderRadius: '8px',
          fontSize: '14px',
          color: '#ffffff'
        }}>
          <div style={{ color: '#722ed1', fontWeight: 'bold', marginBottom: '8px' }}>
            💡 테스트 계정
          </div>
          <div style={{ color: '#a6a6a6' }}>
            <strong style={{ color: '#ffffff' }}>Admin:</strong> admin / admin123!
          </div>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;