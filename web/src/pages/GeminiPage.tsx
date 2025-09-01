import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
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
  Table,
  Select,
  message,
  Progress
} from 'antd';
import {
  PlayCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  RocketOutlined,
  ClockCircleOutlined,
  GoogleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { ApiService } from '../services/apiService';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { Option } = Select;

interface TestResult {
  id: number;
  provider: string;
  prompt: string;
  response: string;
  success: boolean;
  errorMessage?: string;
  tokenUsage?: {
    promptTokenCount: number;
    candidatesTokenCount: number;
    totalTokenCount: number;
  };
  responseTimeMs?: number;
  createdAt: string;
}

interface GenerationJob {
  jobId: string;
  provider: string;
  topic: string;
  tone: string;
  wordCount: number;
  status: string;
  progress: number;
  content?: string;
  errorMessage?: string;
  createdAt: string;
}

interface ProviderStats {
  totalTests: number;
  successfulTests: number;
  failedTests: number;
  successRate: number;
  avgResponseTime: number;
  lastTestAt?: string;
}

const GeminiPage: React.FC = () => {
  const [testPrompt, setTestPrompt] = useState<string>('');
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [stats, setStats] = useState<ProviderStats | null>(null);
  
  const [generationTopic, setGenerationTopic] = useState<string>('');
  const [generationTone, setGenerationTone] = useState<string>('professional');
  const [wordCount, setWordCount] = useState<number>(800);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationJobs, setGenerationJobs] = useState<GenerationJob[]>([]);

  useEffect(() => {
    loadTestResults();
    loadStats();
    loadGenerationJobs();
  }, []);

  const loadTestResults = async () => {
    try {
      const results = await ApiService.getTestResults('gemini');
      setTestResults(results);
    } catch (error) {
      console.error('Failed to load test results:', error);
    }
  };

  const loadStats = async () => {
    try {
      const providerStats = await ApiService.getProviderStats('gemini');
      setStats(providerStats);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const loadGenerationJobs = async () => {
    try {
      const jobs = await ApiService.getGenerationJobs('gemini');
      setGenerationJobs(jobs);
    } catch (error) {
      console.error('Failed to load generation jobs:', error);
    }
  };

  const runTest = async () => {
    if (!testPrompt.trim()) {
      message.warning('테스트할 프롬프트를 입력해주세요.');
      return;
    }

    setIsTestLoading(true);
    
    try {
      const result = await ApiService.testAiApi('gemini', testPrompt);
      
      if (result.success) {
        message.success('Gemini API 테스트가 성공했습니다!');
        loadTestResults();
        loadStats();
      } else {
        message.error('Gemini API 테스트가 실패했습니다.');
      }
    } catch (error) {
      message.error('API 테스트 중 오류가 발생했습니다.');
    } finally {
      setIsTestLoading(false);
    }
  };

  const generateContent = async () => {
    if (!generationTopic.trim()) {
      message.warning('생성할 콘텐츠의 주제를 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    
    try {
      const response = await ApiService.generateContent({
        provider: 'gemini',
        topic: generationTopic,
        tone: generationTone,
        wordCount: wordCount,
        includeImages: true,
        targetLanguage: 'ko'
      });
      
      message.success('콘텐츠 생성이 시작되었습니다!');
      loadGenerationJobs();
      
      // 작업 상태 모니터링
      monitorJob(response.jobId);
      
    } catch (error) {
      message.error('콘텐츠 생성 요청에 실패했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  const monitorJob = async (jobId: string) => {
    const checkStatus = async () => {
      try {
        const status = await ApiService.getJobStatus(jobId);
        
        // 작업 목록 업데이트
        setGenerationJobs(prev => 
          prev.map(job => 
            job.jobId === jobId 
              ? { ...job, status: status.status, progress: status.progress || 0 }
              : job
          )
        );
        
        if (status.status === 'completed') {
          message.success('콘텐츠 생성이 완료되었습니다!');
          loadGenerationJobs();
        } else if (status.status === 'failed') {
          message.error('콘텐츠 생성에 실패했습니다.');
          loadGenerationJobs();
        } else if (status.status === 'in_progress') {
          setTimeout(checkStatus, 3000); // 3초 후 다시 확인
        }
      } catch (error) {
        console.error('Failed to check job status:', error);
      }
    };
    
    setTimeout(checkStatus, 1000);
  };

  const testResultColumns = [
    {
      title: '시간',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 140,
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '프롬프트',
      dataIndex: 'prompt',
      key: 'prompt',
      ellipsis: true,
      render: (text: string) => (
        <Text style={{ maxWidth: 200 }} ellipsis={{ tooltip: text }}>
          {text}
        </Text>
      ),
    },
    {
      title: '결과',
      dataIndex: 'success',
      key: 'success',
      width: 80,
      render: (success: boolean) => (
        <Tag color={success ? 'success' : 'error'}>
          {success ? '성공' : '실패'}
        </Tag>
      ),
    },
    {
      title: '응답시간',
      dataIndex: 'responseTimeMs',
      key: 'responseTimeMs',
      width: 100,
      render: (ms: number) => ms ? `${ms}ms` : '-',
    },
    {
      title: '토큰',
      dataIndex: 'tokenUsage',
      key: 'tokenUsage',
      width: 100,
      render: (usage: any) => 
        usage ? `${usage.totalTokenCount || 0}` : '-',
    },
  ];

  const generationJobColumns = [
    {
      title: '생성 시간',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 140,
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: '주제',
      dataIndex: 'topic',
      key: 'topic',
      ellipsis: true,
    },
    {
      title: '톤',
      dataIndex: 'tone',
      key: 'tone',
      width: 100,
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string, record: GenerationJob) => (
        <div>
          <Tag color={
            status === 'completed' ? 'success' :
            status === 'failed' ? 'error' :
            status === 'in_progress' ? 'processing' : 'default'
          }>
            {status === 'completed' ? '완료' :
             status === 'failed' ? '실패' :
             status === 'in_progress' ? '진행중' : '대기'}
          </Tag>
          {status === 'in_progress' && (
            <Progress 
              percent={record.progress} 
              size="small" 
              style={{ marginTop: 4 }}
            />
          )}
        </div>
      ),
    },
  ];

  const presetPrompts = [
    { label: '기본 인사', value: '안녕하세요! 간단한 인사말로 답해주세요.' },
    { label: '한국어 테스트', value: '한국의 전통 음식에 대해 200자 정도로 설명해주세요.' },
    { label: '기술 설명', value: 'React와 TypeScript의 장점을 초보자도 이해할 수 있게 설명해주세요.' },
    { label: '창의적 글쓰기', value: '미래의 스마트 시티를 상상하여 짧은 이야기를 써주세요.' },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={1}>
          <GoogleOutlined style={{ color: '#4285f4' }} /> Google Gemini
        </Title>
        <Paragraph type="secondary" style={{ fontSize: '16px' }}>
          Google의 최신 AI 모델 Gemini를 사용하여 콘텐츠를 생성하고 테스트할 수 있습니다.
          다국어 지원과 뛰어난 자연어 이해 능력을 제공합니다.
        </Paragraph>
      </div>

      {/* 통계 카드 */}
      {stats && (
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="총 테스트 수"
                value={stats.totalTests}
                prefix={<RocketOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="성공률"
                value={stats.successRate}
                suffix="%"
                precision={1}
                valueStyle={{ 
                  color: stats.successRate >= 90 ? '#3f8600' : 
                          stats.successRate >= 70 ? '#faad14' : '#cf1322' 
                }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="평균 응답시간"
                value={stats.avgResponseTime}
                suffix="ms"
                precision={0}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="실패 횟수"
                value={stats.failedTests}
                valueStyle={{ color: stats.failedTests > 0 ? '#cf1322' : '#3f8600' }}
              />
            </Col>
          </Row>
        </Card>
      )}

      <Row gutter={[24, 24]}>
        {/* API 테스트 섹션 */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <CheckCircleOutlined />
                <span>API 연결 테스트</span>
              </Space>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>프리셋 프롬프트</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="프리셋 선택 (선택사항)"
                  allowClear
                  onChange={(value) => setTestPrompt(value || '')}
                >
                  {presetPrompts.map((preset, index) => (
                    <Option key={index} value={preset.value}>
                      {preset.label}
                    </Option>
                  ))}
                </Select>
              </div>

              <div>
                <Text strong>테스트 프롬프트</Text>
                <TextArea
                  placeholder="Gemini에게 보낼 메시지를 입력하세요"
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  rows={4}
                  maxLength={1000}
                  showCount
                  style={{ marginTop: 8 }}
                />
              </div>

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={runTest}
                loading={isTestLoading}
                disabled={!testPrompt.trim()}
                style={{ width: '100%' }}
                size="large"
              >
                {isTestLoading ? '테스트 실행 중...' : 'Gemini API 테스트'}
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 콘텐츠 생성 섹션 */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <FileTextOutlined />
                <span>콘텐츠 생성</span>
              </Space>
            }
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>생성 주제</Text>
                <Input
                  placeholder="생성할 콘텐츠의 주제를 입력하세요"
                  value={generationTopic}
                  onChange={(e) => setGenerationTopic(e.target.value)}
                  maxLength={200}
                  showCount
                  style={{ marginTop: 8 }}
                />
              </div>

              <Row gutter={12}>
                <Col span={12}>
                  <Text strong>톤앤매너</Text>
                  <Select
                    style={{ width: '100%', marginTop: 8 }}
                    value={generationTone}
                    onChange={setGenerationTone}
                  >
                    <Option value="professional">전문적</Option>
                    <Option value="casual">캐주얼</Option>
                    <Option value="friendly">친근한</Option>
                    <Option value="academic">학술적</Option>
                    <Option value="conversational">대화형</Option>
                  </Select>
                </Col>
                <Col span={12}>
                  <Text strong>목표 단어 수</Text>
                  <Select
                    style={{ width: '100%', marginTop: 8 }}
                    value={wordCount}
                    onChange={setWordCount}
                  >
                    <Option value={300}>300자</Option>
                    <Option value={500}>500자</Option>
                    <Option value={800}>800자</Option>
                    <Option value={1000}>1000자</Option>
                    <Option value={1500}>1500자</Option>
                  </Select>
                </Col>
              </Row>

              <Button
                type="primary"
                icon={<FileTextOutlined />}
                onClick={generateContent}
                loading={isGenerating}
                disabled={!generationTopic.trim()}
                style={{ width: '100%' }}
                size="large"
              >
                {isGenerating ? '생성 중...' : '콘텐츠 생성 시작'}
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Divider />

      {/* 테스트 결과 테이블 */}
      <Card 
        title="최근 테스트 결과" 
        extra={
          <Button onClick={loadTestResults} icon={<RocketOutlined />}>
            새로고침
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          columns={testResultColumns}
          dataSource={testResults}
          rowKey="id"
          pagination={{ pageSize: 10 }}
          size="middle"
        />
      </Card>

      {/* 생성 작업 테이블 */}
      <Card 
        title="콘텐츠 생성 기록"
        extra={
          <Button onClick={loadGenerationJobs} icon={<FileTextOutlined />}>
            새로고침
          </Button>
        }
      >
        <Table
          columns={generationJobColumns}
          dataSource={generationJobs}
          rowKey="jobId"
          pagination={{ pageSize: 10 }}
          size="middle"
          expandable={{
            expandedRowRender: (record: GenerationJob) => (
              <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
                {record.content ? (
                  <div>
                    <Text strong>생성된 콘텐츠:</Text>
                    <Paragraph style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>
                      {record.content}
                    </Paragraph>
                  </div>
                ) : record.errorMessage ? (
                  <Alert
                    message="생성 실패"
                    description={record.errorMessage}
                    type="error"
                    showIcon
                  />
                ) : (
                  <Text type="secondary">아직 콘텐츠가 생성되지 않았습니다.</Text>
                )}
              </div>
            ),
          }}
        />
      </Card>
    </div>
  );
};

export default GeminiPage;