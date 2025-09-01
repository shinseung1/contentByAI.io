import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Select,
  Input,
  Typography,
  Space,
  Alert,
  Spin,
  Tag,
  Divider,
  Row,
  Col,
  Statistic,
  Timeline,
  message
} from 'antd';
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ApiOutlined,
  RocketOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { ApiService, TestResult } from '../services/apiService';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface ApiTesterProps {
  className?: string;
}

const ApiTester: React.FC<ApiTesterProps> = ({ className }) => {
  const [selectedProvider, setSelectedProvider] = useState<string>('gemini');
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [currentTest, setCurrentTest] = useState<TestResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<any>(null);

  // 사용 가능한 AI 제공자
  const aiProviders = [
    { value: 'gemini', label: 'Google Gemini', icon: '🤖' },
    { value: 'claude', label: 'Anthropic Claude', icon: '🧠' },
    { value: 'openai', label: 'OpenAI GPT', icon: '🚀' },
    { value: 'grok', label: 'X.AI Grok', icon: '✨' }
  ];

  // 컴포넌트 마운트 시 헬스체크 실행
  useEffect(() => {
    checkHealthStatus();
  }, []);

  // 헬스체크
  const checkHealthStatus = async () => {
    try {
      const status = await ApiService.healthCheck();
      setHealthStatus(status);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'error', message: 'API 서버에 연결할 수 없습니다' });
    }
  };

  // AI API 테스트 실행
  const runApiTest = async () => {
    setIsLoading(true);
    setCurrentTest(null);

    try {
      const prompt = customPrompt.trim() || undefined;
      const result = await ApiService.testAiApi(selectedProvider, prompt);
      
      setCurrentTest(result);
      setTestResults(prev => [result, ...prev.slice(0, 9)]); // 최근 10개만 유지

      if (result.success) {
        message.success(`${selectedProvider} API 테스트가 성공했습니다!`);
      } else {
        message.error(`${selectedProvider} API 테스트가 실패했습니다.`);
      }
    } catch (error) {
      const errorResult: TestResult = {
        success: false,
        provider: selectedProvider,
        message: '네트워크 오류가 발생했습니다',
        timestamp: new Date().toISOString()
      };
      setCurrentTest(errorResult);
      message.error('API 테스트 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 프리셋 프롬프트
  const presetPrompts = [
    { label: '기본 인사', value: '안녕하세요! 간단한 인사말로 답해주세요.' },
    { label: '콘텐츠 생성', value: '인공지능의 미래에 대해 300자 정도로 전문적인 톤으로 설명해주세요.' },
    { label: '창작 글쓰기', value: '봄날의 따뜻한 햇살을 주제로 감성적인 시 한 편을 써주세요.' },
    { label: '기술 설명', value: '블록체인 기술을 초보자도 이해할 수 있게 쉽게 설명해주세요.' }
  ];

  return (
    <div className={className}>
      <Card>
        <Title level={2}>
          <ApiOutlined /> AI API 테스터
        </Title>
        <Paragraph type="secondary">
          설정된 AI API들의 연결 상태를 테스트하고 응답을 확인할 수 있습니다.
        </Paragraph>

        {/* 서버 상태 */}
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Statistic 
                title="API 서버 상태" 
                value={healthStatus?.status || 'Unknown'}
                valueStyle={{ 
                  color: healthStatus?.status === 'healthy' ? '#3f8600' : '#cf1322' 
                }}
                prefix={
                  healthStatus?.status === 'healthy' ? 
                    <CheckCircleOutlined /> : 
                    <ExclamationCircleOutlined />
                }
              />
            </Col>
            <Col span={12}>
              <Statistic 
                title="테스트 실행 횟수" 
                value={testResults.length}
                prefix={<RocketOutlined />}
              />
            </Col>
          </Row>
        </Card>

        <Divider />

        {/* 테스트 설정 */}
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>AI 제공자 선택</Text>
              <Select
                style={{ width: '100%' }}
                value={selectedProvider}
                onChange={setSelectedProvider}
                size="large"
              >
                {aiProviders.map(provider => (
                  <Option key={provider.value} value={provider.value}>
                    <Space>
                      <span>{provider.icon}</span>
                      <span>{provider.label}</span>
                    </Space>
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>프리셋 프롬프트</Text>
              <Select
                style={{ width: '100%' }}
                placeholder="프리셋 선택 (선택사항)"
                allowClear
                size="large"
                onChange={(value) => setCustomPrompt(value || '')}
              >
                {presetPrompts.map((preset, index) => (
                  <Option key={index} value={preset.value}>
                    {preset.label}
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>
        </Row>

        <Space direction="vertical" style={{ width: '100%', marginTop: 16 }}>
          <Text strong>사용자 정의 프롬프트</Text>
          <TextArea
            placeholder="테스트할 프롬프트를 입력하세요 (비워두면 기본 인사말 사용)"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            rows={3}
            maxLength={500}
            showCount
          />
        </Space>

        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Button
            type="primary"
            size="large"
            icon={<PlayCircleOutlined />}
            onClick={runApiTest}
            loading={isLoading}
            disabled={!healthStatus || healthStatus.status !== 'healthy'}
          >
            {isLoading ? '테스트 실행 중...' : 'AI API 테스트 실행'}
          </Button>
        </div>

        <Divider />

        {/* 현재 테스트 결과 */}
        {isLoading && (
          <Card style={{ marginBottom: 16 }}>
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">
                  {selectedProvider} API 테스트 실행 중...
                </Text>
              </div>
            </div>
          </Card>
        )}

        {currentTest && !isLoading && (
          <Card 
            title={
              <Space>
                <span>{aiProviders.find(p => p.value === currentTest.provider)?.icon}</span>
                <span>{currentTest.provider.toUpperCase()} 테스트 결과</span>
                <Tag color={currentTest.success ? 'success' : 'error'}>
                  {currentTest.success ? '성공' : '실패'}
                </Tag>
              </Space>
            }
            style={{ marginBottom: 16 }}
          >
            {currentTest.success ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Alert
                  message="API 테스트 성공!"
                  type="success"
                  showIcon
                />
                
                {currentTest.response && (
                  <div>
                    <Text strong>AI 응답:</Text>
                    <Card size="small" style={{ marginTop: 8, backgroundColor: '#f6f8fa' }}>
                      <Paragraph>{currentTest.response}</Paragraph>
                    </Card>
                  </div>
                )}

                {currentTest.tokenUsage && (
                  <Row gutter={16}>
                    <Col span={8}>
                      <Statistic 
                        title="입력 토큰" 
                        value={currentTest.tokenUsage.promptTokenCount} 
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic 
                        title="출력 토큰" 
                        value={currentTest.tokenUsage.candidatesTokenCount} 
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic 
                        title="총 토큰" 
                        value={currentTest.tokenUsage.totalTokenCount} 
                      />
                    </Col>
                  </Row>
                )}
              </Space>
            ) : (
              <Alert
                message="API 테스트 실패"
                description={currentTest.message}
                type="error"
                showIcon
              />
            )}
          </Card>
        )}

        {/* 테스트 히스토리 */}
        {testResults.length > 0 && (
          <Card title="최근 테스트 히스토리" size="small">
            <Timeline
              items={testResults.slice(0, 5).map(result => ({
                color: result.success ? 'green' : 'red',
                dot: result.success ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />,
                children: (
                  <div>
                    <Space>
                      <Text strong>{result.provider.toUpperCase()}</Text>
                      <Tag color={result.success ? 'success' : 'error'}>
                        {result.success ? '성공' : '실패'}
                      </Tag>
                      <Text type="secondary">
                        <ClockCircleOutlined /> {new Date(result.timestamp).toLocaleString()}
                      </Text>
                    </Space>
                    {!result.success && (
                      <div style={{ marginTop: 4 }}>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {result.message}
                        </Text>
                      </div>
                    )}
                  </div>
                )
              }))}
            />
          </Card>
        )}
      </Card>
    </div>
  );
};

export default ApiTester;