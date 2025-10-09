import React, { useState, useEffect } from 'react'
import { Card, List, Button, Typography, Tag, Space, Drawer, Form, Input, Select, message, Spin, Switch } from 'antd'
import { FileTextOutlined, EditOutlined, PlusOutlined, PlayCircleOutlined, HistoryOutlined } from '@ant-design/icons'
import { API_BASE_URL } from '../../services/api'

const { Title, Text } = Typography
const { TextArea } = Input

interface WorkflowTemplate {
  id: number
  name: string
  description: string
  steps: WorkflowStep[]
  version: string
  status: string
  created_at: string
  updated_at?: string
  created_by?: number
}

interface WorkflowStep {
  name: string
  prompt_template: string
  approver_role: string
  auto_transition: boolean
}

const AdminWorkflows: React.FC = () => {
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowTemplate | null>(null)
  const [form] = Form.useForm()
  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const fetchWorkflows = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/workflows/`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()
      setWorkflows(data)
    } catch (error) {
      console.error('Failed to fetch workflows:', error)
      message.error('워크플로우 목록을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveWorkflow = async (values: any) => {
    try {
      setSubmitting(true)
      
      const workflowData = {
        name: values.name,
        description: values.description,
        steps: values.steps || [],
        version: values.version || 'v1.0',
        status: values.status || 'active'
      }
      
      let response
      if (selectedWorkflow) {
        // Update existing workflow
        response = await fetch(`${API_BASE_URL}/workflows/${selectedWorkflow.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(workflowData)
        })
      } else {
        // Create new workflow
        response = await fetch(`${API_BASE_URL}/workflows/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(workflowData)
        })
      }
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save workflow')
      }
      
      message.success(`워크플로우가 ${selectedWorkflow ? '수정' : '생성'}되었습니다`)
      setDrawerVisible(false)
      form.resetFields()
      fetchWorkflows() // Refresh the list
    } catch (error) {
      console.error('Save workflow error:', error)
      message.error(`저장 중 오류가 발생했습니다: ${error.message}`)
    } finally {
      setSubmitting(false)
    }
  }

  const handleActivateWorkflow = async (workflowId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/activate`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to activate workflow')
      }
      
      message.success('워크플로우가 활성화되었습니다')
      fetchWorkflows() // Refresh the list
    } catch (error) {
      console.error('Activate workflow error:', error)
      message.error('워크플로우 활성화에 실패했습니다')
    }
  }

  const handleDeactivateWorkflow = async (workflowId: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/deactivate`, {
        method: 'POST'
      })
      
      if (!response.ok) {
        throw new Error('Failed to deactivate workflow')
      }
      
      message.success('워크플로우가 비활성화되었습니다')
      fetchWorkflows() // Refresh the list
    } catch (error) {
      console.error('Deactivate workflow error:', error)
      message.error('워크플로우 비활성화에 실패했습니다')
    }
  }

  const handleEditWorkflow = (workflow: WorkflowTemplate) => {
    setSelectedWorkflow(workflow)
    form.setFieldsValue({
      ...workflow,
      steps: workflow.steps.map(step => ({
        ...step,
        auto_transition: step.auto_transition
      }))
    })
    setDrawerVisible(true)
  }


  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3}>워크플로우 템플릿</Title>
          <Text type="secondary">콘텐츠 생성 워크플로우를 관리합니다</Text>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => {
            setSelectedWorkflow(null)
            form.resetFields()
            setDrawerVisible(true)
          }}
        >
          템플릿 추가
        </Button>
      </div>

      <Card>
        <Spin spinning={loading}>
          <List
            itemLayout="vertical"
            dataSource={workflows}
            locale={{
              emptyText: workflows.length === 0 ? '워크플로우 템플릿이 없습니다' : '데이터를 불러오는 중...'
            }}
            renderItem={(workflow) => (
              <List.Item
                actions={[
                <Button key="edit" icon={<EditOutlined />} onClick={() => handleEditWorkflow(workflow)}>
                  편집
                </Button>,
                <Button key="history" icon={<HistoryOutlined />}>
                  버전 이력
                </Button>,
                workflow.status === 'active' ? (
                  <Button key="deactivate" icon={<PlayCircleOutlined />} onClick={() => handleDeactivateWorkflow(workflow.id)}>
                    비활성화
                  </Button>
                ) : (
                  <Button key="activate" icon={<PlayCircleOutlined />} type="primary" onClick={() => handleActivateWorkflow(workflow.id)}>
                    활성화
                  </Button>
                )
              ]}
            >
              <List.Item.Meta
                avatar={<FileTextOutlined style={{ fontSize: '24px', color: '#722ed1' }} />}
                title={
                  <Space>
                    <span style={{ fontSize: '16px', fontWeight: 600 }}>{workflow.name}</span>
                    <Tag color={workflow.status === 'active' ? 'green' : 'red'}>
                      {workflow.status === 'active' ? '활성' : '비활성'}
                    </Tag>
                    <Tag color="blue">{workflow.version}</Tag>
                  </Space>
                }
                description={
                  <div>
                    <Text type="secondary">{workflow.description}</Text>
                    <div style={{ marginTop: 8 }}>
                      <Space wrap>
                        {workflow.steps.map((step, index) => (
                          <Tag key={index} color="processing">
                            {step.name}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        생성일: {workflow.created_at} | 단계: {workflow.steps.length}개
                      </Text>
                    </div>
                  </div>
                }
              />
              </List.Item>
            )}
          />
        </Spin>
      </Card>

      <Drawer
        title={selectedWorkflow ? '워크플로우 편집' : '새 워크플로우 추가'}
        width={800}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerVisible(false)}>취소</Button>
            <Button type="primary" loading={submitting} onClick={() => form.submit()}>
              저장
            </Button>
          </Space>
        }
      >
        <Form form={form} layout="vertical" onFinish={handleSaveWorkflow}>
          <Form.Item name="name" label="템플릿 이름" rules={[{ required: true }]}>
            <Input placeholder="예: 기본 블로그 포스트" />
          </Form.Item>
          <Form.Item name="description" label="설명" rules={[{ required: true }]}>
            <Input placeholder="워크플로우 단계를 간단히 설명해주세요" />
          </Form.Item>
          <Form.Item name="status" label="상태">
            <Select defaultValue="active">
              <Select.Option value="active">활성</Select.Option>
              <Select.Option value="inactive">비활성</Select.Option>
            </Select>
          </Form.Item>

          <Title level={4} style={{ marginTop: 24 }}>워크플로우 단계</Title>
          <Form.List name="steps">
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Card key={key} size="small" style={{ marginBottom: 16 }}>
                    <Form.Item
                      {...restField}
                      name={[name, 'name']}
                      label="단계 이름"
                      rules={[{ required: true }]}
                    >
                      <Input placeholder="예: 초안 작성" />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'prompt_template']}
                      label="프롬프트 템플릿"
                      rules={[{ required: true }]}
                    >
                      <TextArea 
                        rows={3} 
                        placeholder="예: 다음 주제로 블로그 초안을 작성해주세요: {topic}"
                      />
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'approver_role']}
                      label="승인자"
                      rules={[{ required: true }]}
                    >
                      <Select>
                        <Select.Option value="editor">Editor</Select.Option>
                        <Select.Option value="admin">Admin</Select.Option>
                        <Select.Option value="owner">Owner</Select.Option>
                      </Select>
                    </Form.Item>
                    <Form.Item
                      {...restField}
                      name={[name, 'auto_transition']}
                      label="자동 전환"
                      valuePropName="checked"
                    >
                      <Switch checkedChildren="자동" unCheckedChildren="수동" />
                    </Form.Item>
                    <Button type="link" onClick={() => remove(name)} danger>
                      단계 삭제
                    </Button>
                  </Card>
                ))}
                <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                  단계 추가
                </Button>
              </>
            )}
          </Form.List>
        </Form>
      </Drawer>
    </div>
  )
}

export default AdminWorkflows