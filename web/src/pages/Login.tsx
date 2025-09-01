import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Form, Input, Card, Alert, Typography } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

interface LoginForm {
  email: string;
  password: string;
}

export default function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.isLoading);
  const [error, setError] = useState<string | null>(null);
  const [form] = Form.useForm();

  const onFinish = async (values: LoginForm) => {
    try {
      setError(null);
      await login(values.email, values.password);
      
      const { user } = useAuthStore.getState();
      if (user?.role === 'admin') {
        navigate('/admin/users');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '로그인에 실패했습니다.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <Title level={2}>AI 블로그 플랫폼</Title>
          <Text type="secondary">계정에 로그인하세요</Text>
        </div>
        
        <Card className="shadow-lg">
          <Form
            form={form}
            name="login"
            onFinish={onFinish}
            layout="vertical"
            size="large"
            className="space-y-4"
          >
            {error && (
              <Alert
                message={error}
                type="error"
                showIcon
                className="mb-4"
                closable
                onClose={() => setError(null)}
              />
            )}
            
            <Form.Item
              label="이메일"
              name="email"
              rules={[
                { required: true, message: '이메일을 입력해주세요!' },
                { type: 'email', message: '올바른 이메일 형식을 입력해주세요!' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="이메일 주소"
                autoComplete="email"
              />
            </Form.Item>

            <Form.Item
              label="비밀번호"
              name="password"
              rules={[
                { required: true, message: '비밀번호를 입력해주세요!' },
                { min: 6, message: '비밀번호는 최소 6자 이상이어야 합니다!' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="비밀번호"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                className="w-full"
                loading={isLoading}
                size="large"
              >
                {isLoading ? '로그인 중...' : '로그인'}
              </Button>
            </Form.Item>
          </Form>
          
          <div className="text-center mt-4">
            <Text type="secondary" className="text-sm">
              테스트 계정: admin@example.com / admin123
            </Text>
          </div>
        </Card>
      </div>
    </div>
  );
}