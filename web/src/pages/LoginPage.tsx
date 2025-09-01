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
      const response = await axios.post('http://127.0.0.1:3001/api/v1/auth/login', {
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
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card
        title="AI Writer 로그인"
        style={{
          width: 400,
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          borderRadius: '12px'
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
                borderRadius: '8px'
              }}
            >
              로그인
            </Button>
          </Form.Item>
        </Form>

        <div style={{ 
          marginTop: '24px', 
          padding: '16px', 
          background: '#f8f9fa', 
          borderRadius: '8px',
          fontSize: '14px',
          color: '#666'
        }}>
          <div><strong>테스트 계정:</strong></div>
          <div>Admin: admin / admin123!</div>
          <div>Validator: validator / validator123!</div>
          <div>User: testuser / test123!</div>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;