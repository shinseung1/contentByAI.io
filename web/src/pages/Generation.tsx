import React from 'react'
import { Card, Form, Input, Button, Select, InputNumber, Switch, Typography, Space, message, List, Tag, Spin, Modal } from 'antd'
import { EditOutlined, SendOutlined, HistoryOutlined, CheckCircleOutlined, LoadingOutlined, ExclamationCircleOutlined, EyeOutlined } from '@ant-design/icons'
import { api, GenerationResponse } from '../services/api'

const { Title, Text } = Typography
const { TextArea } = Input

const Generation: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)
  const [jobs, setJobs] = React.useState<GenerationResponse[]>([])
  const [jobsLoading, setJobsLoading] = React.useState(false)
  const [selectedJob, setSelectedJob] = React.useState<GenerationResponse | null>(null)
  const [modalVisible, setModalVisible] = React.useState(false)

  const loadJobs = React.useCallback(async () => {
    setJobsLoading(true)
    try {
      const jobList = await api.listGenerationJobs()
      setJobs(jobList)
      console.log('Loaded jobs:', jobList)
    } catch (error) {
      console.error('Failed to load jobs:', error)
      message.error('히스토리를 불러오는데 실패했습니다.')
    } finally {
      setJobsLoading(false)
    }
  }, [])

  React.useEffect(() => {
    loadJobs()
  }, [loadJobs])

  const handleGenerate = async (values: any) => {
    setLoading(true)
    try {
      // API 호출 로직
      console.log('Generation request:', values)
      message.success('콘텐츠 생성 요청이 시작되었습니다!')
      // 생성 후 히스토리 새로고침
      setTimeout(() => {
        loadJobs()
      }, 2000)
    } catch (error) {
      message.error('콘텐츠 생성 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <LoadingOutlined style={{ color: '#1890ff' }} />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success'
      case 'failed':
        return 'error'
      default:
        return 'processing'
    }
  }

  const parseJobContent = (job: GenerationResponse) => {
    try {
      // Debug logging
      console.log('Job content type:', typeof job.content)
      console.log('Job content:', job.content)
      
      if (typeof job.content === 'string') {
        const parsed = JSON.parse(job.content)
        return {
          title: parsed.title || '제목 없음',
          summary: extractSummaryFromHtml(parsed.html_content) || '요약 없음'
        }
      } else if (job.content && typeof job.content === 'object') {
        // Handle the actual API response structure with html_content
        const htmlContent = job.content.html_content || job.content.content
        const title = job.content.title || '제목 없음'
        const summary = job.content.summary || extractSummaryFromHtml(htmlContent) || '요약 없음'
        
        // Debug logging
        console.log('Parsed title:', title)
        console.log('Parsed summary:', summary)
        
        return {
          title: title,
          summary: summary
        }
      }
    } catch (error) {
      console.error('Error parsing job content:', error, job)
    }
    
    return {
      title: '콘텐츠 제목 없음',
      summary: '요약을 불러올 수 없습니다'
    }
  }

  const extractSummaryFromHtml = (htmlContent: string | undefined | any) => {
    if (!htmlContent) return ''
    
    // Ensure we have a string
    if (typeof htmlContent !== 'string') {
      console.log('htmlContent is not string:', typeof htmlContent, htmlContent)
      return String(htmlContent).substring(0, 100) + '...'
    }
    
    try {
      // If it's nested JSON, try to parse again
      if (htmlContent.includes('```json')) {
        const jsonMatch = htmlContent.match(/```json\s*({[\s\S]*?})\s*```/)
        if (jsonMatch) {
          const innerJson = JSON.parse(jsonMatch[1])
          if (innerJson.html_content) {
            return extractSummaryFromHtml(innerJson.html_content)
          }
        }
      }
      
      // Remove HTML tags and clean up
      const textContent = htmlContent
        .replace(/<[^>]*>/g, '') // Remove HTML tags
        .replace(/```json/g, '') // Remove code block markers  
        .replace(/```/g, '')
        .replace(/\\"/g, '"')
        .replace(/\\/g, '')
        .replace(/&quot;/g, '"')
        .replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ') // Replace multiple spaces with single space
        .trim()
      
      // Look for Korean text patterns - find text after emoji or meaningful content
      const koreanMatch = textContent.match(/[✨🎯🚀🚗🚌📊❓].{10,}/)
      if (koreanMatch) {
        const koreanText = koreanMatch[0].replace(/^[✨🎯🚀🚗🚌📊❓]\s*/, '').trim()
        return koreanText.length > 150 
          ? koreanText.substring(0, 150) + '...'
          : koreanText
      }
      
      // Look for the first meaningful Korean sentence
      const sentences = textContent.split(/[.!?。]/)
      for (const sentence of sentences) {
        const cleanSentence = sentence.trim()
        if (cleanSentence.length > 20 && /[가-힣]/.test(cleanSentence)) {
          return cleanSentence.length > 150 
            ? cleanSentence.substring(0, 150) + '...'
            : cleanSentence + '.'
        }
      }
      
      // Fallback: first meaningful text
      const firstMeaningful = textContent.match(/[가-힣].{20,}/)
      if (firstMeaningful) {
        const text = firstMeaningful[0]
        return text.length > 150 
          ? text.substring(0, 150) + '...'
          : text
      }
      
      // Last fallback
      return textContent.length > 150 
        ? textContent.substring(0, 150) + '...'
        : textContent
        
    } catch (error) {
      console.error('Error extracting summary:', error)
      return '요약을 불러올 수 없습니다'
    }
  }

  const handleViewJob = (job: GenerationResponse) => {
    setSelectedJob(job)
    setModalVisible(true)
  }

  const renderJobContent = (job: GenerationResponse) => {
    if (!job.content) {
      return <div>콘텐츠가 없습니다.</div>
    }

    try {
      let htmlContent = ''
      let title = ''

      if (typeof job.content === 'string') {
        const parsed = JSON.parse(job.content)
        htmlContent = parsed.html_content || parsed.content || ''
        title = parsed.title || '제목 없음'
      } else if (job.content && typeof job.content === 'object') {
        htmlContent = job.content.html_content || job.content.content || ''
        title = job.content.title || '제목 없음'
      }

      return (
        <div>
          <h2 style={{ marginBottom: '20px', color: '#1890ff' }}>{title}</h2>
          <div 
            dangerouslySetInnerHTML={{ __html: htmlContent }}
            style={{
              lineHeight: '1.6',
              fontSize: '16px'
            }}
          />
        </div>
      )
    } catch (error) {
      console.error('Error rendering job content:', error)
      return <div>콘텐츠를 표시할 수 없습니다.</div>
    }
  }

  return (
    <div>
      <div className="page-header">
        <Title level={1}>콘텐츠 생성</Title>
      </div>

      <Card title={<><EditOutlined /> 새로운 콘텐츠 생성</>}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleGenerate}
          initialValues={{
            tone: 'professional',
            word_count: 800,
            include_images: true,
            target_language: 'ko',
          }}
        >
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
              placeholder="생성할 콘텐츠의 주제를 구체적으로 입력해주세요. 예: '인공지능이 마케팅에 미치는 영향과 활용 방안'"
            />
          </Form.Item>

          <Form.Item name="tone" label="톤 앤 매너">
            <Select>
              <Select.Option value="professional">전문적</Select.Option>
              <Select.Option value="casual">캐주얼</Select.Option>
              <Select.Option value="friendly">친근한</Select.Option>
              <Select.Option value="academic">학술적</Select.Option>
              <Select.Option value="conversational">대화형</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="word_count" label="목표 단어 수">
            <InputNumber
              min={300}
              max={3000}
              step={100}
              style={{ width: '100%' }}
              placeholder="800"
            />
          </Form.Item>

          <Form.Item name="target_language" label="언어">
            <Select>
              <Select.Option value="ko">한국어</Select.Option>
              <Select.Option value="en">영어</Select.Option>
              <Select.Option value="ja">일본어</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="include_images" label="이미지 포함" valuePropName="checked">
            <Switch />
          </Form.Item>

          <Form.Item style={{ marginTop: 24 }}>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<SendOutlined />}
                loading={loading}
                size="large"
              >
                콘텐츠 생성 시작
              </Button>
              <Button size="large" onClick={() => form.resetFields()}>
                초기화
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card 
        title={<><HistoryOutlined /> 생성 히스토리</>}
        style={{ marginTop: 24 }}
        extra={
          <Button 
            type="link" 
            onClick={loadJobs}
            loading={jobsLoading}
          >
            새로고침
          </Button>
        }
      >
        {jobsLoading ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#999' }}>히스토리를 불러오는 중...</div>
          </div>
        ) : jobs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            아직 생성된 콘텐츠가 없습니다.
          </div>
        ) : (
          <List
            dataSource={jobs.slice(0, 5)}
            renderItem={(job) => {
              const { title, summary } = parseJobContent(job)
              return (
                <List.Item>
                  <List.Item.Meta
                    avatar={getStatusIcon(job.status)}
                    title={
                      <Space>
                        <Text strong>{title}</Text>
                        <Tag color={getStatusColor(job.status)}>
                          {job.status === 'completed' ? '완료' : 
                           job.status === 'failed' ? '실패' : '진행중'}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <Text>
                            {summary}
                          </Text>
                        </div>
                        <div style={{ marginBottom: 4 }}>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            ID: {job.job_id?.slice(0, 8)} | 
                            톤: {job.tone || 'professional'} | 
                            단어수: {job.word_count || 800} | 
                            생성일: {job.created_at ? new Date(job.created_at).toLocaleDateString() : '알 수 없음'}
                          </Text>
                        </div>
                      </div>
                    }
                  />
                  <div>
                    <Button 
                      type="link" 
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handleViewJob(job)}
                    >
                      상세보기
                    </Button>
                  </div>
                </List.Item>
              )
            }}
          />
        )}
      </Card>

      <Modal
        title="콘텐츠 상세보기"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            닫기
          </Button>
        ]}
        width={900}
        style={{ maxHeight: '80vh' }}
        bodyStyle={{ maxHeight: '70vh', overflow: 'auto' }}
      >
        {selectedJob ? renderJobContent(selectedJob) : null}
      </Modal>
    </div>
  )
}

export default Generation