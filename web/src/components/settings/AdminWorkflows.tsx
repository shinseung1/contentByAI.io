import React, { useState } from 'react'
import { Card, List, Button, Typography, Tag, Space, Drawer, Form, Input, Select, message } from 'antd'
import { FileTextOutlined, EditOutlined, PlusOutlined, PlayCircleOutlined, HistoryOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { TextArea } = Input

interface WorkflowTemplate {
  id: string
  name: string
  description: string
  steps: WorkflowStep[]
  version: string
  status: string
  created_at: string
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

  const workflows: WorkflowTemplate[] = [
    {
      id: '1',
      name: '기본 블로그 포스트',
      description: 'outline → draft → fact-check → seo → publish',
      steps: [
        { name: '아웃라인 생성', prompt_template: '다음 주제로 블로그 아웃라인을 작성해주세요: {topic}', approver_role: 'editor', auto_transition: true },
        { name: '초안 작성', prompt_template: '다음 아웃라인을 바탕으로 상세한 초안을 작성해주세요: {outline}', approver_role: 'editor', auto_transition: false },
        { name: '사실 검증', prompt_template: '다음 내용의 사실을 검증하고 출처를 추가해주세요: {draft}', approver_role: 'admin', auto_transition: false },
        { name: 'SEO 최적화', prompt_template: '다음 콘텐츠를 SEO에 최적화해주세요: {content}', approver_role: 'editor', auto_transition: true },
        { name: '발행', prompt_template: '', approver_role: 'admin', auto_transition: false }
      ],
      version: 'v1.2',
      status: 'active',
      created_at: '2024-01-15'
    },
    {
      id: '2',
      name: '소셜 미디어 포스트',
      description: 'draft → optimize → schedule',
      steps: [
        { name: '초안 생성', prompt_template: 'SNS용 짧은 포스트를 작성해주세요: {topic}', approver_role: 'editor', auto_transition: true },
        { name: '최적화', prompt_template: '다음 포스트를 플랫폼에 맞게 최적화해주세요: {draft}', approver_role: 'editor', auto_transition: true },
        { name: '예약 발행', prompt_template: '', approver_role: 'editor', auto_transition: false }
      ],
      version: 'v1.0',
      status: 'active',
      created_at: '2024-02-01'
    }
  ]

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

  const handleSaveWorkflow = async (values: any) => {
    try {
      console.log('Saving workflow:', values)
      message.success('워크플로우가 저장되었습니다')
      setDrawerVisible(false)
      form.resetFields()
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
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
        <List
          itemLayout="vertical"
          dataSource={workflows}
          renderItem={(workflow) => (
            <List.Item
              actions={[
                <Button key="edit" icon={<EditOutlined />} onClick={() => handleEditWorkflow(workflow)}>
                  편집
                </Button>,
                <Button key="history" icon={<HistoryOutlined />}>
                  버전 이력
                </Button>,
                <Button key="activate" icon={<PlayCircleOutlined />} type="primary">
                  활성화
                </Button>
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
      </Card>

      <Drawer
        title={selectedWorkflow ? '워크플로우 편집' : '새 워크플로우 추가'}
        width={800}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        extra={
          <Space>
            <Button onClick={() => setDrawerVisible(false)}>취소</Button>
            <Button type="primary" onClick={() => form.submit()}>
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