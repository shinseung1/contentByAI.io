import React, { useState, useEffect } from 'react'
import { Card, Form, Input, Button, Select, InputNumber, Switch, Typography, Space, message, Row, Col, Statistic, Progress, Alert, List, Tag, Divider } from 'antd'
import { BulbOutlined, SendOutlined, FireOutlined, GlobalOutlined, EyeOutlined, HistoryOutlined, ClockCircleOutlined } from '@ant-design/icons'
import { api, GenerationRequest, GenerationResponse, API_BASE_URL } from '../services/api'

const { Title, Text } = Typography
const { TextArea } = Input

interface WorkflowTemplate {
  id: number
  name: string
  description: string
  status: string
}

const GenerationOpenAI: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [currentJob, setCurrentJob] = useState<string | null>(null)
  const [jobStatus, setJobStatus] = useState<GenerationResponse | null>(null)
  const [progress, setProgress] = useState(0)
  const [historyJobs, setHistoryJobs] = useState<any[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [workflowTemplates, setWorkflowTemplates] = useState<WorkflowTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null)

  // 워크플로우 템플릿 로드
  const fetchWorkflowTemplates = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/workflows/active`)
      if (response.ok) {
        const templates = await response.json()
        setWorkflowTemplates(templates)
        // 첫 번째 활성 템플릿을 기본 선택
        if (templates.length > 0) {
          setSelectedTemplate(templates[0])
          form.setFieldsValue({ workflow_template: templates[0].id })
        }
      }
    } catch (error) {
      console.error('Failed to fetch workflow templates:', error)
    }
  }

  // 히스토리 로드
  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const jobs = await api.listGenerationJobs('openai')
      setHistoryJobs(jobs)
    } catch (error) {
      console.error('Failed to load history:', error)
    } finally {
      setHistoryLoading(false)
    }
  }

  // 컴포넌트 마운트 시 히스토리 및 워크플로우 템플릿 로드
  useEffect(() => {
    loadHistory()
    fetchWorkflowTemplates()
  }, [])

  const handleGenerate = async (values: any) => {
    setLoading(true)
    setCurrentJob(null)
    setJobStatus(null)
    setProgress(0)

    try {
      const request: GenerationRequest = {
        ...values,
        provider: 'openai',
        tone: 'professional', // tone은 워크플로우 템플릿에서 결정됨
        workflow_template_id: values.workflow_template
      }

      console.log('OpenAI generation request:', request)
      
      // Start generation
      const jobResponse = await api.generateContent(request)
      setCurrentJob(jobResponse.jobId)
      
      message.success(`OpenAI 콘텐츠 생성이 시작되었습니다! (Job ID: ${jobResponse.jobId})`)
      
      // Poll for results
      pollJobStatus(jobResponse.jobId)
      
    } catch (error) {
      console.error('Generation error:', error)
      message.error('콘텐츠 생성 중 오류가 발생했습니다: ' + (error as Error).message)
      setLoading(false)
    }
  }

  const pollJobStatus = async (jobId: string) => {
    try {
      const status = await api.getGenerationJob(jobId)
      setJobStatus(status)
      setProgress(status.progress * 100)

      if (status.status === 'completed') {
        message.success('콘텐츠 생성이 완료되었습니다!')
        setLoading(false)
        loadHistory() // 히스토리 새로고침
      } else if (status.status === 'failed') {
        message.error(`콘텐츠 생성이 실패했습니다: ${status.error}`)
        setLoading(false)
      } else if (status.status === 'in_progress') {
        // Continue polling
        setTimeout(() => pollJobStatus(jobId), 2000)
      }
    } catch (error) {
      console.error('Polling error:', error)
      message.error('작업 상태 확인 중 오류가 발생했습니다')
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <Title level={1}>
          <BulbOutlined /> OpenAI 콘텐츠 생성
        </Title>
        <Text type="secondary">OpenAI의 GPT 모델을 사용하여 창의적인 콘텐츠를 생성합니다</Text>
      </div>

      <Row gutter={[24, 24]}>
        <Col span={8}>
          <Card>
            <Statistic
              title="모델"
              value="GPT-4 Turbo"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#10a37f' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="창의성"
              value="높음"
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#ff6900' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="글로벌 지원"
              value="전세계"
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#0969da' }}
            />
          </Card>
        </Col>
      </Row>

      <Card 
        title={
          <Space>
            <BulbOutlined style={{ color: '#10a37f' }} />
            새로운 콘텐츠 생성
          </Space>
        }
        style={{ marginTop: 24 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            provider: 'openai',
            word_count: 800,
            include_images: true,
            target_language: 'ko',
          }}
        >
          <Form.Item name="provider" hidden>
            <Input value="openai" />
          </Form.Item>

          <Form.Item
            name="topic"
            label="주제"
            rules={[
              { required: true, message: '주제를 입력해주세요.' },
              { min: 10, message: '주제는 최소 10자 이상이어야 합니다.' },
            ]}
          >
            <TextArea
              rows={3}
              placeholder="OpenAI GPT로 생성할 콘텐츠의 주제를 구체적으로 입력해주세요. 예: 'ChatGPT와 GPT-4의 창의적 글쓰기 활용법과 실무 적용 사례'"
            />
          </Form.Item>

          <Form.Item 
            name="workflow_template" 
            label="워크플로우 템플릿"
            rules={[{ required: true, message: '워크플로우 템플릿을 선택해주세요.' }]}
          >
            <Select 
              placeholder="워크플로우 템플릿을 선택하세요"
              onChange={(templateId) => {
                const template = workflowTemplates.find(t => t.id === templateId)
                setSelectedTemplate(template || null)
              }}
              loading={workflowTemplates.length === 0}
            >
              {workflowTemplates.map(template => (
                <Select.Option key={template.id} value={template.id}>
                  {template.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          {selectedTemplate && (
            <div style={{ 
              marginBottom: 16, 
              padding: 12, 
              backgroundColor: '#000000', 
              borderRadius: 4,
              border: '1px solid #333333',
              color: '#ffffff'
            }}>
              <strong style={{ color: '#ffffff' }}>선택된 템플릿:</strong> {selectedTemplate.name}
              <br />
              <span style={{ color: '#cccccc', fontSize: '12px' }}>
                {selectedTemplate.description}
              </span>
            </div>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="word_count" label="목표 단어 수">
                <InputNumber
                  min={300}
                  max={3000}
                  step={100}
                  style={{ width: '100%' }}
                  placeholder="800"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="target_language" label="언어">
                <Select>
                  <Select.Option value="ko">한국어</Select.Option>
                  <Select.Option value="en">영어</Select.Option>
                  <Select.Option value="ja">일본어</Select.Option>
                  <Select.Option value="zh">중국어</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="include_images" label="이미지 포함" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item style={{ marginTop: 32 }}>
            <Space size="large">
              <Button
                type="primary"
                htmlType="submit"
                icon={<SendOutlined />}
                loading={loading}
                size="large"
                style={{ 
                  background: 'linear-gradient(135deg, #10a37f, #0969da)',
                  border: 'none',
                  minWidth: '200px'
                }}
              >
                OpenAI로 생성 시작
              </Button>
              <Button size="large" onClick={() => {
                form.resetFields()
                // 템플릿 기본값 다시 설정
                if (workflowTemplates.length > 0) {
                  form.setFieldsValue({ workflow_template: workflowTemplates[0].id })
                }
              }}>
                초기화
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      {/* Job Status Display */}
      {currentJob && (
        <Card 
          title={
            <Space>
              <BulbOutlined style={{ color: '#10a37f' }} />
              생성 진행 상황
            </Space>
          } 
          style={{ marginTop: 24 }}
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>Job ID: </Text>
              <Text code>{currentJob}</Text>
            </div>
            <div>
              <Text strong>상태: </Text>
              <Text>{jobStatus?.status || 'Starting...'}</Text>
            </div>
            <div>
              <Text strong>메시지: </Text>
              <Text>{jobStatus?.message || 'Initializing...'}</Text>
            </div>
            <Progress 
              percent={progress} 
              status={loading ? 'active' : 'normal'}
              strokeColor={{
                '0%': '#10a37f',
                '100%': '#ff6900'
              }}
            />
          </Space>
        </Card>
      )}

      {/* Generation Result Display */}
      {(jobStatus?.result || jobStatus?.content) && (
        <Card 
          title={
            <Space>
              <EyeOutlined style={{ color: '#ff6900' }} />
              생성된 콘텐츠
            </Space>
          }
          style={{ marginTop: 24 }}
          extra={
            <Space>
              <Button type="primary">편집</Button>
              <Button>저장</Button>
            </Space>
          }
        >
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Title level={3}>
                {jobStatus.result?.title || jobStatus.content?.title || '생성된 콘텐츠'}
              </Title>
            </div>
            
            {(jobStatus.content?.summary || jobStatus.result?.contentPreview) && (
              <Alert
                message="요약"
                description={jobStatus.content?.summary || jobStatus.result?.contentPreview}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <div 
              style={{ 
                border: '1px solid #e1e5e9',
                borderRadius: '8px',
                padding: '24px',
                maxHeight: '800px',
                overflow: 'auto',
                background: '#ffffff',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                color: '#000000'
              }}
              className="generated-content"
            >
              <style>{`
                .generated-content, .generated-content * { 
                  color: #000000 !important; 
                }
                .generated-content h1 { 
                  font-size: 2.2em; 
                  font-weight: 700; 
                  margin-bottom: 0.5em; 
                  color: #000000 !important; 
                  line-height: 1.3;
                }
                .generated-content h2 { 
                  font-size: 1.6em; 
                  font-weight: 600; 
                  margin: 1.5em 0 0.8em; 
                  color: #000000 !important; 
                  line-height: 1.4;
                }
                .generated-content h3 { 
                  font-size: 1.3em; 
                  font-weight: 500; 
                  margin: 1.2em 0 0.6em; 
                  color: #000000 !important; 
                  line-height: 1.4;
                }
                .generated-content p { 
                  margin-bottom: 1.2em; 
                  line-height: 1.7; 
                  color: #000000 !important;
                  font-size: 15px;
                }
                .generated-content ul, .generated-content ol { 
                  margin-bottom: 1.2em; 
                  padding-left: 1.5em; 
                  color: #000000 !important;
                }
                .generated-content li { 
                  margin-bottom: 0.5em; 
                  line-height: 1.6;
                  color: #000000 !important;
                }
                .generated-content div { 
                  color: #000000 !important;
                }
                .generated-content span { 
                  color: inherit !important;
                }
                .generated-content figure { 
                  margin: 2em 0; 
                  text-align: center; 
                }
                .generated-content img { 
                  max-width: 100%; 
                  height: auto; 
                  border-radius: 8px; 
                  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .generated-content figcaption { 
                  margin-top: 0.8em; 
                  font-style: italic; 
                  color: #666 !important; 
                  font-size: 14px;
                }
                .generated-content aside { 
                  background: #f8f9fa; 
                  padding: 1.5em; 
                  border-radius: 8px; 
                  margin: 1.5em 0; 
                  border-left: 4px solid #10a37f;
                  color: #000000 !important;
                }
                .generated-content aside h3 { 
                  margin-top: 0; 
                  color: #10a37f !important;
                }
                .generated-content aside ul { 
                  margin-bottom: 0; 
                  color: #000000 !important;
                }
                .generated-content a { 
                  color: #3498db !important; 
                  text-decoration: none; 
                }
                .generated-content a:hover { 
                  text-decoration: underline; 
                }
                .generated-content strong { 
                  color: #e74c3c !important;
                  font-weight: 600;
                }
                .generated-content em { 
                  color: #000000 !important;
                  font-style: italic;
                }
              `}</style>
              <div 
                dangerouslySetInnerHTML={{ 
                  __html: jobStatus.content?.content || jobStatus.content || '<p>콘텐츠 로딩 중...</p>' 
                }}
              />
            </div>

            {jobStatus.content?.tags && jobStatus.content.tags.length > 0 && (
              <div>
                <Text strong>태그: </Text>
                <Space wrap>
                  {jobStatus.content.tags.map((tag, index) => (
                    <span key={index} style={{
                      background: 'rgba(16, 163, 127, 0.15)',
                      color: '#10a37f',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      #{tag}
                    </span>
                  ))}
                </Space>
              </div>
            )}

            {jobStatus.result && (
              <div>
                <Text strong>통계: </Text>
                <Space>
                  <Text type="secondary">단어 수: {jobStatus.result.wordCount}</Text>
                  <Divider type="vertical" />
                  <Text type="secondary">SEO 점수: {jobStatus.result.seoScore}</Text>
                </Space>
              </div>
            )}
          </Space>
        </Card>
      )}

      <Card 
        title={
          <Space>
            <HistoryOutlined style={{ color: '#10a37f' }} />
            OpenAI 생성 히스토리
          </Space>
        }
        style={{ marginTop: 24 }}
        extra={
          <Button type="link" onClick={loadHistory} loading={historyLoading}>
            새로고침
          </Button>
        }
      >
        {historyJobs.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 0', 
            color: '#a6a6a6' 
          }}>
            아직 OpenAI로 생성된 콘텐츠가 없습니다.
          </div>
        ) : (
          <List
            dataSource={historyJobs}
            renderItem={(job: any) => (
              <List.Item>
                <List.Item.Meta
                  title={
                    <Space>
                      <Text strong>{job.topic}</Text>
                      <Tag color={
                        job.status === 'completed' ? 'success' :
                        job.status === 'failed' ? 'error' :
                        job.status === 'in_progress' ? 'processing' : 'default'
                      }>
                        {job.status}
                      </Tag>
                    </Space>
                  }
                  description={
                    <Space direction="vertical" size="small">
                      <Space>
                        <ClockCircleOutlined />
                        <Text type="secondary">
                          {job.created_at ? new Date(job.created_at).toLocaleString('ko-KR') : '날짜 없음'}
                        </Text>
                        <Divider type="vertical" />
                        <Text type="secondary">톤: {job.tone || '미설정'}</Text>
                        <Divider type="vertical" />
                        <Text type="secondary">목표: {job.word_count || job.wordCount || '미설정'}자</Text>
                      </Space>
                      {job.content && (
                        <div>
                          <Text type="secondary">
                            {(() => {
                              let contentText = '';
                              if (typeof job.content === 'string') {
                                contentText = job.content;
                              } else if (job.content?.content && typeof job.content.content === 'string') {
                                contentText = job.content.content;
                              } else {
                                return '콘텐츠 미리보기 불가';
                              }
                              
                              // Remove HTML tags and get plain text
                              const plainText = contentText.replace(/<[^>]*>/g, '').trim();
                              return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText;
                            })()}
                          </Text>
                        </div>
                      )}
                      {job.errorMessage && (
                        <Text type="danger">{job.errorMessage}</Text>
                      )}
                    </Space>
                  }
                />
                {job.status === 'completed' && job.content && (
                  <Button 
                    type="primary" 
                    size="small"
                    onClick={() => {
                      setJobStatus({
                        ...job,
                        result: {
                          bundleId: `bundle_${job.jobId}`,
                          title: job.topic,
                          contentPreview: typeof job.content === 'string' ? job.content : job.content?.content || '',
                          wordCount: typeof job.content === 'string' ? job.content.split(' ').length : (job.content?.content ? job.content.content.split(' ').length : 0),
                          imagesCount: job.content?.images?.length || 0,
                          seoScore: 85
                        }
                      })
                    }}
                  >
                    보기
                  </Button>
                )}
              </List.Item>
            )}
          />
        )}
      </Card>
    </div>
  )
}

export default GenerationOpenAI