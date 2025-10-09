import React, { useEffect } from 'react'
import { Card, Form, Input, Button, Select, InputNumber, Switch, Typography, Space, message } from 'antd'
import { EditOutlined, SendOutlined } from '@ant-design/icons'
import { API_BASE_URL } from '../services/api'

const { Title } = Typography
const { TextArea } = Input

interface WorkflowTemplate {
  id: number
  name: string
  description: string
  status: string
}

const Generation: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)
  const [workflowTemplates, setWorkflowTemplates] = React.useState<WorkflowTemplate[]>([])
  const [selectedTemplate, setSelectedTemplate] = React.useState<WorkflowTemplate | null>(null)

  useEffect(() => {
    fetchWorkflowTemplates()
  }, [])

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

  const handleTemplateChange = (templateId: number) => {
    const template = workflowTemplates.find(t => t.id === templateId)
    setSelectedTemplate(template || null)
  }

  const handleGenerate = async (values: any) => {
    setLoading(true)
    try {
      const requestData = {
        topic: values.topic,
        tone: 'professional', // tone은 워크플로우 템플릿에서 결정됨
        word_count: values.word_count,
        target_language: values.target_language,
        include_images: values.include_images,
        provider: 'gemini',
        workflow_template_id: values.workflow_template // 워크플로우 템플릿 ID 추가
      }

      const response = await fetch(`${API_BASE_URL}/generation/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })

      if (response.ok) {
        const result = await response.json()
        message.success(`콘텐츠 생성이 시작되었습니다! Job ID: ${result.job_id}`)
        form.resetFields()
        // 템플릿 기본값 다시 설정
        if (workflowTemplates.length > 0) {
          form.setFieldsValue({ workflow_template: workflowTemplates[0].id })
        }
      } else {
        const error = await response.json()
        message.error(`콘텐츠 생성 실패: ${error.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('Generation error:', error)
      message.error('콘텐츠 생성 중 오류가 발생했습니다.')
    } finally {
      setLoading(false)
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

          <Form.Item 
            name="workflow_template" 
            label="워크플로우 템플릿"
            rules={[{ required: true, message: '워크플로우 템플릿을 선택해주세요.' }]}
          >
            <Select 
              placeholder="워크플로우 템플릿을 선택하세요"
              onChange={handleTemplateChange}
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
              backgroundColor: '#f5f5f5', 
              borderRadius: 4,
              border: '1px solid #d9d9d9'
            }}>
              <strong>선택된 템플릿:</strong> {selectedTemplate.name}
              <br />
              <span style={{ color: '#666', fontSize: '12px' }}>
                {selectedTemplate.description}
              </span>
            </div>
          )}

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
        title="생성 히스토리" 
        style={{ marginTop: 24 }}
        extra={<Button type="link">전체 보기</Button>}
      >
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          아직 생성된 콘텐츠가 없습니다.
        </div>
      </Card>
    </div>
  )
}

export default Generation