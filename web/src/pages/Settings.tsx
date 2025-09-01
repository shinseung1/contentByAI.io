import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Form,
  Input,
  Switch,
  Button,
  Typography,
  Divider,
  Row,
  Col,
  Select,
  InputNumber,
  Alert,
  Space,
  Tabs,
  message
} from 'antd';
import {
  SettingOutlined,
  ApiOutlined,
  BellOutlined,
  SafetyOutlined,
  ExperimentOutlined,
  SaveOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { generationAPI } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

interface Settings {
  api_settings: {
    openai_api_key?: string;
    claude_api_key?: string;
    gemini_api_key?: string;
    grok_api_key?: string;
    default_ai_provider: string;
    max_tokens: number;
    temperature: number;
  };
  platform_settings: {
    wordpress_url?: string;
    wordpress_username?: string;
    wordpress_password?: string;
    blogger_client_id?: string;
    blogger_client_secret?: string;
    auto_publish: boolean;
    default_platform: string;
  };
  notification_settings: {
    email_notifications: boolean;
    job_completion_alerts: boolean;
    error_notifications: boolean;
    weekly_reports: boolean;
  };
  security_settings: {
    session_timeout: number;
    max_login_attempts: number;
    require_2fa: boolean;
    password_expiry_days: number;
  };
}

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('api');
  const queryClient = useQueryClient();

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => generationAPI.getSettings(),
    select: (data) => data.data
  });

  const updateSettingsMutation = useMutation({
    mutationFn: (data: Partial<Settings>) => generationAPI.updateSettings(data),
    onSuccess: () => {
      message.success('설정이 저장되었습니다.');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '설정 저장에 실패했습니다.');
    }
  });

  const testConnectionMutation = useMutation({
    mutationFn: (provider: string) => generationAPI.testConnection(provider),
    onSuccess: () => {
      message.success('연결 테스트가 성공했습니다.');
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || '연결 테스트에 실패했습니다.');
    }
  });

  const onFinish = (values: any) => {
    updateSettingsMutation.mutate(values);
  };

  const handleTestConnection = (provider: string) => {
    testConnectionMutation.mutate(provider);
  };

  React.useEffect(() => {
    if (settings) {
      form.setFieldsValue(settings);
    }
  }, [settings, form]);

  const aiProviderOptions = [
    { value: 'openai', label: 'OpenAI (ChatGPT)' },
    { value: 'claude', label: 'Anthropic Claude' },
    { value: 'gemini', label: 'Google Gemini' },
    { value: 'grok', label: 'xAI Grok' }
  ];

  const platformOptions = [
    { value: 'wordpress', label: 'WordPress' },
    { value: 'blogger', label: 'Google Blogger' },
    { value: 'medium', label: 'Medium' }
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-6">
        <Title level={2}>
          <SettingOutlined className="mr-2" />
          설정
        </Title>
        <Text type="secondary">
          AI 블로그 플랫폼의 설정을 관리하세요.
        </Text>
      </div>

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        initialValues={{
          'api_settings.default_ai_provider': 'openai',
          'api_settings.max_tokens': 2000,
          'api_settings.temperature': 0.7,
          'platform_settings.auto_publish': false,
          'platform_settings.default_platform': 'wordpress',
          'notification_settings.email_notifications': true,
          'notification_settings.job_completion_alerts': true,
          'notification_settings.error_notifications': true,
          'notification_settings.weekly_reports': false,
          'security_settings.session_timeout': 60,
          'security_settings.max_login_attempts': 5,
          'security_settings.require_2fa': false,
          'security_settings.password_expiry_days': 90
        }}
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={
              <span>
                <ApiOutlined />
                AI API 설정
              </span>
            } 
            key="api"
          >
            <Card title="AI 제공업체 설정">
              <Alert
                message="API 키 보안"
                description="API 키는 안전하게 암호화되어 저장됩니다. 테스트 연결 버튼으로 설정을 확인하세요."
                type="info"
                showIcon
                className="mb-6"
              />

              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="OpenAI API Key"
                    name={['api_settings', 'openai_api_key']}
                  >
                    <Input.Password
                      placeholder="sk-..."
                      addonAfter={
                        <Button
                          size="small"
                          onClick={() => handleTestConnection('openai')}
                          loading={testConnectionMutation.isPending}
                        >
                          테스트
                        </Button>
                      }
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="Claude API Key"
                    name={['api_settings', 'claude_api_key']}
                  >
                    <Input.Password
                      placeholder="sk-ant-..."
                      addonAfter={
                        <Button
                          size="small"
                          onClick={() => handleTestConnection('claude')}
                          loading={testConnectionMutation.isPending}
                        >
                          테스트
                        </Button>
                      }
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="Gemini API Key"
                    name={['api_settings', 'gemini_api_key']}
                  >
                    <Input.Password
                      placeholder="AIza..."
                      addonAfter={
                        <Button
                          size="small"
                          onClick={() => handleTestConnection('gemini')}
                          loading={testConnectionMutation.isPending}
                        >
                          테스트
                        </Button>
                      }
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="Grok API Key"
                    name={['api_settings', 'grok_api_key']}
                  >
                    <Input.Password
                      placeholder="xai-..."
                      addonAfter={
                        <Button
                          size="small"
                          onClick={() => handleTestConnection('grok')}
                          loading={testConnectionMutation.isPending}
                        >
                          테스트
                        </Button>
                      }
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Row gutter={[24, 16]}>
                <Col xs={24} md={8}>
                  <Form.Item
                    label="기본 AI 제공업체"
                    name={['api_settings', 'default_ai_provider']}
                  >
                    <Select placeholder="기본 AI 선택">
                      {aiProviderOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} md={8}>
                  <Form.Item
                    label="최대 토큰 수"
                    name={['api_settings', 'max_tokens']}
                  >
                    <InputNumber
                      min={500}
                      max={8000}
                      step={100}
                      className="w-full"
                      formatter={(value) => `${value} 토큰`}
                      parser={(value) => value?.replace(' 토큰', '') as any}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={8}>
                  <Form.Item
                    label="창의성 (Temperature)"
                    name={['api_settings', 'temperature']}
                  >
                    <InputNumber
                      min={0}
                      max={1}
                      step={0.1}
                      className="w-full"
                      formatter={(value) => `${value}`}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <ExperimentOutlined />
                플랫폼 설정
              </span>
            } 
            key="platform"
          >
            <Card title="발행 플랫폼 설정">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Card size="small" title="WordPress 설정">
                    <Form.Item
                      label="WordPress URL"
                      name={['platform_settings', 'wordpress_url']}
                    >
                      <Input placeholder="https://your-site.com" />
                    </Form.Item>
                    
                    <Form.Item
                      label="사용자명"
                      name={['platform_settings', 'wordpress_username']}
                    >
                      <Input placeholder="WordPress 사용자명" />
                    </Form.Item>
                    
                    <Form.Item
                      label="비밀번호"
                      name={['platform_settings', 'wordpress_password']}
                    >
                      <Input.Password placeholder="WordPress 비밀번호" />
                    </Form.Item>
                  </Card>
                </Col>

                <Col xs={24} md={12}>
                  <Card size="small" title="Google Blogger 설정">
                    <Form.Item
                      label="Client ID"
                      name={['platform_settings', 'blogger_client_id']}
                    >
                      <Input placeholder="Google OAuth Client ID" />
                    </Form.Item>
                    
                    <Form.Item
                      label="Client Secret"
                      name={['platform_settings', 'blogger_client_secret']}
                    >
                      <Input.Password placeholder="Google OAuth Client Secret" />
                    </Form.Item>
                  </Card>
                </Col>
              </Row>

              <Row gutter={[24, 16]} className="mt-4">
                <Col xs={24} md={12}>
                  <Form.Item
                    label="기본 발행 플랫폼"
                    name={['platform_settings', 'default_platform']}
                  >
                    <Select placeholder="기본 플랫폼 선택">
                      {platformOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="자동 발행"
                    name={['platform_settings', 'auto_publish']}
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="활성"
                      unCheckedChildren="비활성"
                    />
                  </Form.Item>
                  <Text type="secondary" className="text-xs">
                    콘텐츠 생성 완료 시 자동으로 발행합니다.
                  </Text>
                </Col>
              </Row>
            </Card>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <BellOutlined />
                알림 설정
              </span>
            } 
            key="notifications"
          >
            <Card title="알림 설정">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="이메일 알림"
                    name={['notification_settings', 'email_notifications']}
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="활성"
                      unCheckedChildren="비활성"
                    />
                  </Form.Item>
                  <Text type="secondary" className="text-xs">
                    중요한 알림을 이메일로 받습니다.
                  </Text>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="작업 완료 알림"
                    name={['notification_settings', 'job_completion_alerts']}
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="활성"
                      unCheckedChildren="비활성"
                    />
                  </Form.Item>
                  <Text type="secondary" className="text-xs">
                    콘텐츠 생성 완료 시 알림을 받습니다.
                  </Text>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="오류 알림"
                    name={['notification_settings', 'error_notifications']}
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="활성"
                      unCheckedChildren="비활성"
                    />
                  </Form.Item>
                  <Text type="secondary" className="text-xs">
                    시스템 오류 발생 시 즉시 알림을 받습니다.
                  </Text>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="주간 리포트"
                    name={['notification_settings', 'weekly_reports']}
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="활성"
                      unCheckedChildren="비활성"
                    />
                  </Form.Item>
                  <Text type="secondary" className="text-xs">
                    매주 활동 요약 리포트를 받습니다.
                  </Text>
                </Col>
              </Row>
            </Card>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <SafetyOutlined />
                보안 설정
              </span>
            } 
            key="security"
          >
            <Card title="보안 설정">
              <Alert
                message="보안 주의사항"
                description="보안 설정을 변경하면 모든 사용자의 세션이 영향을 받을 수 있습니다."
                type="warning"
                showIcon
                className="mb-6"
              />

              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="세션 타임아웃 (분)"
                    name={['security_settings', 'session_timeout']}
                  >
                    <InputNumber
                      min={5}
                      max={480}
                      step={5}
                      className="w-full"
                      formatter={(value) => `${value}분`}
                      parser={(value) => value?.replace('분', '') as any}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="최대 로그인 시도 횟수"
                    name={['security_settings', 'max_login_attempts']}
                  >
                    <InputNumber
                      min={3}
                      max={10}
                      className="w-full"
                      formatter={(value) => `${value}회`}
                      parser={(value) => value?.replace('회', '') as any}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="2단계 인증 필수"
                    name={['security_settings', 'require_2fa']}
                    valuePropName="checked"
                  >
                    <Switch
                      checkedChildren="필수"
                      unCheckedChildren="선택"
                    />
                  </Form.Item>
                  <Text type="secondary" className="text-xs">
                    모든 사용자에게 2단계 인증을 요구합니다.
                  </Text>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    label="비밀번호 만료 기간 (일)"
                    name={['security_settings', 'password_expiry_days']}
                  >
                    <InputNumber
                      min={30}
                      max={365}
                      step={30}
                      className="w-full"
                      formatter={(value) => `${value}일`}
                      parser={(value) => value?.replace('일', '') as any}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </TabPane>
        </Tabs>

        <div className="flex justify-end space-x-4 mt-6 pt-6 border-t">
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              form.resetFields();
              if (settings) {
                form.setFieldsValue(settings);
              }
            }}
          >
            초기화
          </Button>
          
          <Button
            type="primary"
            htmlType="submit"
            icon={<SaveOutlined />}
            loading={updateSettingsMutation.isPending}
            size="large"
          >
            설정 저장
          </Button>
        </div>
      </Form>
    </div>
  );
};

export default Settings;