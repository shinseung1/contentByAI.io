import React, { useState, useEffect } from 'react'
import { 
  Card, 
  Typography, 
  Select, 
  Button, 
  Tag, 
  Space, 
  Modal, 
  Row, 
  Col, 
  Divider, 
  Empty,
  Spin,
  message,
  List
} from 'antd'
import { 
  EyeOutlined, 
  CalendarOutlined, 
  ClockCircleOutlined, 
  FileTextOutlined, 
  UserOutlined, 
  GlobalOutlined, 
  TagOutlined,
  HistoryOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

interface GenerationJob {
  job_id: string
  provider: string
  status: string
  message: string
  progress: number
  created_at: string
  completed_at?: string
  tone: string
  word_count: number
  error?: string
  target_language: string
  include_images: boolean
  content?: string
}

interface JobContent {
  title: string
  html_content: string
  summary?: string
  tags?: string[]
  images?: any[]
}

export default function GenerationHistory() {
  const [jobs, setJobs] = useState<GenerationJob[]>([])
  const [filteredJobs, setFilteredJobs] = useState<GenerationJob[]>([])
  const [loading, setLoading] = useState(true)
  const [providerFilter, setProviderFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [selectedJob, setSelectedJob] = useState<GenerationJob | null>(null)
  const [jobContent, setJobContent] = useState<JobContent | null>(null)
  const [contentLoading, setContentLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)

  useEffect(() => {
    fetchJobs()
  }, [])

  useEffect(() => {
    filterJobs()
  }, [jobs, providerFilter, statusFilter])

  const fetchJobs = async () => {
    try {
      const response = await fetch('http://127.0.0.1:3005/api/v1/generation/jobs')
      const data = await response.json()
      
      if (data.error) {
        message.error('작업 목록을 불러오는데 실패했습니다.')
        setJobs([])
      } else {
        setJobs(data)
      }
    } catch (error) {
      message.error('서버 연결에 실패했습니다.')
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  const filterJobs = () => {
    let filtered = jobs

    if (providerFilter !== 'all') {
      filtered = filtered.filter(job => job.provider === providerFilter)
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(job => job.status === statusFilter)
    }

    setFilteredJobs(filtered)
  }

  const fetchJobContent = async (jobId: string) => {
    setContentLoading(true)
    try {
      const response = await fetch(`http://127.0.0.1:3005/api/v1/generation/jobs/${jobId}`)
      const data = await response.json()
      
      if (data.content) {
        try {
          const parsedContent = JSON.parse(data.content)
          setJobContent(parsedContent)
        } catch (e) {
          message.error('콘텐츠 형식이 올바르지 않습니다.')
          setJobContent(null)
        }
      } else {
        setJobContent(null)
      }
    } catch (error) {
      message.error('콘텐츠를 불러오는데 실패했습니다.')
      setJobContent(null)
    } finally {
      setContentLoading(false)
    }
  }

  const handleViewContent = (job: GenerationJob) => {
    setSelectedJob(job)
    setModalVisible(true)
    fetchJobContent(job.job_id)
  }

  const getProviderColor = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'gemini': return 'blue'
      case 'openai': return 'green'
      case 'claude': return 'purple'
      case 'grok': return 'orange'
      default: return 'default'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'failed': return 'error'
      case 'in_progress': return 'processing'
      case 'pending': return 'default'
      default: return 'default'
    }
  }

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A'
    try {
      return new Date(dateString).toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch (e) {
      return dateString
    }
  }

  const stripHtml = (html: string) => {
    const div = document.createElement('div')
    div.innerHTML = html
    return div.textContent || div.innerText || ''
  }

  const getContentPreview = (content: string, maxLength = 150) => {
    if (!content) return 'No content available'
    
    try {
      const parsed = JSON.parse(content)
      const htmlContent = parsed.html_content || ''
      const textContent = stripHtml(htmlContent)
      return textContent.length > maxLength 
        ? textContent.substring(0, maxLength) + '...' 
        : textContent
    } catch (e) {
      return 'Invalid content format'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '완료'
      case 'failed': return '실패'
      case 'in_progress': return '진행중'
      case 'pending': return '대기중'
      default: return status
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>생성 히스토리를 불러오는 중...</div>
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>
            <HistoryOutlined /> 생성 히스토리
          </Title>
          <Text type="secondary">과거에 생성된 콘텐츠들을 확인하고 관리할 수 있습니다.</Text>
        </div>

        {/* Filters */}
        <Card>
          <Row gutter={16} align="middle">
            <Col>
              <Space>
                <UserOutlined />
                <Text>AI 제공자:</Text>
                <Select 
                  value={providerFilter} 
                  onChange={setProviderFilter}
                  style={{ width: 140 }}
                >
                  <Option value="all">모든 제공자</Option>
                  <Option value="gemini">Gemini</Option>
                  <Option value="openai">OpenAI</Option>
                  <Option value="claude">Claude</Option>
                  <Option value="grok">Grok</Option>
                </Select>
              </Space>
            </Col>
            
            <Col>
              <Space>
                <TagOutlined />
                <Text>상태:</Text>
                <Select 
                  value={statusFilter} 
                  onChange={setStatusFilter}
                  style={{ width: 120 }}
                >
                  <Option value="all">모든 상태</Option>
                  <Option value="completed">완료</Option>
                  <Option value="failed">실패</Option>
                  <Option value="in_progress">진행중</Option>
                  <Option value="pending">대기중</Option>
                </Select>
              </Space>
            </Col>
            
            <Col flex="auto">
              <Text type="secondary" style={{ float: 'right' }}>
                총 {filteredJobs.length}개의 작업
              </Text>
            </Col>
          </Row>
        </Card>

        {/* Jobs List */}
        {filteredJobs.length === 0 ? (
          <Card>
            <Empty
              description="선택한 조건에 맞는 생성 작업이 없습니다."
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </Card>
        ) : (
          <List
            grid={{ gutter: 16, column: 1 }}
            dataSource={filteredJobs}
            renderItem={(job) => (
              <List.Item>
                <Card
                  hoverable
                  actions={[
                    job.status === 'completed' && job.content ? (
                      <Button 
                        type="primary" 
                        icon={<EyeOutlined />}
                        onClick={() => handleViewContent(job)}
                      >
                        내용 보기
                      </Button>
                    ) : null
                  ].filter(Boolean)}
                >
                  <Row justify="space-between" align="top">
                    <Col flex="auto">
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Space wrap>
                          <Tag color={getProviderColor(job.provider)}>
                            {job.provider?.toUpperCase() || 'Unknown'}
                          </Tag>
                          <Tag color={getStatusColor(job.status)}>
                            {getStatusText(job.status)}
                          </Tag>
                          <Tag>{job.target_language?.toUpperCase() || 'KO'}</Tag>
                          {job.include_images && <Tag>이미지 포함</Tag>}
                        </Space>

                        <Title level={4} style={{ margin: 0 }}>{job.message}</Title>
                        
                        <div>
                          {job.status === 'completed' && job.content && (
                            <Text type="secondary">{getContentPreview(job.content)}</Text>
                          )}
                          {job.status === 'failed' && job.error && (
                            <Text type="danger">오류: {job.error}</Text>
                          )}
                        </div>

                        <Space wrap size="large">
                          <Space size="small">
                            <CalendarOutlined />
                            <Text type="secondary">{formatDate(job.created_at)}</Text>
                          </Space>
                          {job.completed_at && (
                            <Space size="small">
                              <ClockCircleOutlined />
                              <Text type="secondary">완료: {formatDate(job.completed_at)}</Text>
                            </Space>
                          )}
                          <Space size="small">
                            <FileTextOutlined />
                            <Text type="secondary">{job.word_count}자</Text>
                          </Space>
                          <Space size="small">
                            <GlobalOutlined />
                            <Text type="secondary">{job.tone}</Text>
                          </Space>
                        </Space>
                      </Space>
                    </Col>
                  </Row>
                </Card>
              </List.Item>
            )}
          />
        )}

        {/* Content Modal */}
        <Modal
          title={
            selectedJob ? (
              <Space>
                <Tag color={getProviderColor(selectedJob.provider)}>
                  {selectedJob.provider?.toUpperCase()}
                </Tag>
                {selectedJob.message}
              </Space>
            ) : '콘텐츠 보기'
          }
          open={modalVisible}
          onCancel={() => setModalVisible(false)}
          footer={null}
          width="90%"
          style={{ maxWidth: 1200 }}
        >
          {contentLoading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>콘텐츠를 불러오는 중...</div>
            </div>
          ) : jobContent ? (
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <div>
                <Title level={4}>제목</Title>
                <Card>
                  <Text>{jobContent.title}</Text>
                </Card>
              </div>
              
              {jobContent.summary && (
                <div>
                  <Title level={4}>요약</Title>
                  <Card>
                    <Text>{jobContent.summary}</Text>
                  </Card>
                </div>
              )}
              
              {jobContent.tags && jobContent.tags.length > 0 && (
                <div>
                  <Title level={4}>태그</Title>
                  <Space wrap>
                    {jobContent.tags.map((tag, index) => (
                      <Tag key={index}>{tag}</Tag>
                    ))}
                  </Space>
                </div>
              )}
              
              <div>
                <Title level={4}>콘텐츠</Title>
                <Card>
                  <div 
                    style={{ 
                      maxHeight: '400px', 
                      overflowY: 'auto',
                      lineHeight: '1.6'
                    }}
                    dangerouslySetInnerHTML={{ __html: jobContent.html_content }}
                  />
                </Card>
              </div>
            </Space>
          ) : (
            <Empty description="콘텐츠를 불러올 수 없습니다." />
          )}
        </Modal>
      </Space>
    </div>
  )
}