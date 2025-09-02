import React, { useState } from 'react'
import { Card, Table, Button, Form, Input, Select, Switch, Space, Tag, Typography, Row, Col, Drawer, message } from 'antd'
import { ApiOutlined, EditOutlined, PlusOutlined, KeyOutlined, SettingOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

interface APIKey {
  id: string
  alias: string
  provider: string
  status: string
  scope: string[]
  created_at: string
  last_used: string
}

interface ModelMapping {
  task_type: string
  default_model: string
  fallback_model: string
  retry_count: number
  timeout: number
}

const AdminModels: React.FC = () => {
  const [keyDrawerVisible, setKeyDrawerVisible] = useState(false)
  const [mappingDrawerVisible, setMappingDrawerVisible] = useState(false)
  const [selectedKey, setSelectedKey] = useState<APIKey | null>(null)
  const [selectedMapping, setSelectedMapping] = useState<ModelMapping | null>(null)
  const [keyForm] = Form.useForm()
  const [mappingForm] = Form.useForm()

  const apiKeys: APIKey[] = [
    {
      id: '1',
      alias: 'OpenAI-Production',
      provider: 'OpenAI',
      status: 'active',
      scope: ['gpt-4', 'gpt-3.5-turbo'],
      created_at: '2024-01-15',
      last_used: '1분 전'
    },
    {
      id: '2', 
      alias: 'Claude-Main',
      provider: 'Anthropic',
      status: 'active',
      scope: ['claude-3-sonnet', 'claude-3-haiku'],
      created_at: '2024-01-20',
      last_used: '5분 전'
    },
    {
      id: '3',
      alias: 'Gemini-Test',
      provider: 'Google',
      status: 'inactive',
      scope: ['gemini-pro', 'gemini-pro-vision'],
      created_at: '2024-02-01',
      last_used: '2시간 전'
    }
  ]

  const modelMappings: ModelMapping[] = [
    { task_type: '초안 작성', default_model: 'gpt-4', fallback_model: 'claude-3-sonnet', retry_count: 3, timeout: 60 },
    { task_type: '요약', default_model: 'gpt-3.5-turbo', fallback_model: 'claude-3-haiku', retry_count: 2, timeout: 30 },
    { task_type: '번역', default_model: 'gpt-4', fallback_model: 'gemini-pro', retry_count: 3, timeout: 45 },
    { task_type: 'SEO 최적화', default_model: 'claude-3-sonnet', fallback_model: 'gpt-4', retry_count: 2, timeout: 60 }
  ]

  const keyColumns: ColumnsType<APIKey> = [
    {
      title: 'API 키',
      dataIndex: 'alias',
      key: 'alias',
      render: (alias, record) => (
        <Space>
          <KeyOutlined />
          <div>
            <div style={{ fontWeight: 500 }}>{alias}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.provider}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status === 'active' ? '활성' : '비활성'}
        </Tag>
      ),
    },
    {
      title: '범위',
      dataIndex: 'scope',
      key: 'scope',
      render: (scope) => (
        <Space wrap>
          {scope.map((model: string) => <Tag key={model}>{model}</Tag>)}
        </Space>
      ),
    },
    {
      title: '마지막 사용',
      dataIndex: 'last_used',
      key: 'last_used',
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button 
            icon={<EditOutlined />} 
            size="small"
            onClick={() => handleEditKey(record)}
          >
            편집
          </Button>
        </Space>
      ),
    },
  ]

  const mappingColumns: ColumnsType<ModelMapping> = [
    {
      title: '작업 유형',
      dataIndex: 'task_type',
      key: 'task_type',
    },
    {
      title: '기본 모델',
      dataIndex: 'default_model',
      key: 'default_model',
      render: (model) => <Tag color="blue">{model}</Tag>,
    },
    {
      title: '폴백 모델',
      dataIndex: 'fallback_model',
      key: 'fallback_model',
      render: (model) => <Tag color="orange">{model}</Tag>,
    },
    {
      title: '재시도',
      dataIndex: 'retry_count',
      key: 'retry_count',
      render: (count) => `${count}회`,
    },
    {
      title: '타임아웃',
      dataIndex: 'timeout',
      key: 'timeout',
      render: (timeout) => `${timeout}초`,
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record) => (
        <Button 
          icon={<EditOutlined />} 
          size="small"
          onClick={() => handleEditMapping(record)}
        >
          편집
        </Button>
      ),
    },
  ]

  const handleEditKey = (key: APIKey) => {
    setSelectedKey(key)
    keyForm.setFieldsValue(key)
    setKeyDrawerVisible(true)
  }

  const handleEditMapping = (mapping: ModelMapping) => {
    setSelectedMapping(mapping)
    mappingForm.setFieldsValue(mapping)
    setMappingDrawerVisible(true)
  }

  const handleSaveKey = async (values: any) => {
    try {
      console.log('Saving API key:', values)
      message.success('API 키가 저장되었습니다')
      setKeyDrawerVisible(false)
      keyForm.resetFields()
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  const handleSaveMapping = async (values: any) => {
    try {
      console.log('Saving model mapping:', values)
      message.success('모델 매핑이 저장되었습니다')
      setMappingDrawerVisible(false)
      mappingForm.resetFields()
    } catch (error) {
      message.error('저장 중 오류가 발생했습니다')
    }
  }

  return (
    <div>
      <Title level={3}>모델/프로바이더 관리</Title>
      <Text type="secondary">API 키와 모델 설정을 관리합니다</Text>

      <Row gutter={[0, 24]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card 
            title={
              <Space>
                <KeyOutlined />
                API 키 관리
              </Space>
            }
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={() => {
                  setSelectedKey(null)
                  keyForm.resetFields()
                  setKeyDrawerVisible(true)
                }}
              >
                키 추가
              </Button>
            }
          >
            <Table
              columns={keyColumns}
              dataSource={apiKeys}
              rowKey="id"
              size="middle"
            />
          </Card>
        </Col>

        <Col span={24}>
          <Card 
            title={
              <Space>
                <SettingOutlined />
                기본 모델 매핑
              </Space>
            }
          >
            <Table
              columns={mappingColumns}
              dataSource={modelMappings}
              rowKey="task_type"
              size="middle"
            />
          </Card>
        </Col>
      </Row>

      <Drawer
        title={selectedKey ? 'API 키 편집' : '새 API 키 추가'}
        width={500}
        open={keyDrawerVisible}
        onClose={() => setKeyDrawerVisible(false)}
        extra={
          <Space>
            <Button onClick={() => setKeyDrawerVisible(false)}>취소</Button>
            <Button type="primary" onClick={() => keyForm.submit()}>
              저장
            </Button>
          </Space>
        }
      >
        <Form form={keyForm} layout="vertical" onFinish={handleSaveKey}>
          <Form.Item name="alias" label="별칭" rules={[{ required: true }]}>
            <Input placeholder="예: OpenAI-Production" />
          </Form.Item>
          <Form.Item name="provider" label="제공업체" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="OpenAI">OpenAI</Select.Option>
              <Select.Option value="Anthropic">Anthropic</Select.Option>
              <Select.Option value="Google">Google</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="api_key" label="API 키" rules={[{ required: true }]}>
            <Input.Password placeholder="sk-..." />
          </Form.Item>
          <Form.Item name="status" label="상태" valuePropName="checked">
            <Switch checkedChildren="활성" unCheckedChildren="비활성" />
          </Form.Item>
          <Form.Item name="scope" label="허용 모델">
            <Select mode="multiple" placeholder="사용할 모델을 선택하세요">
              <Select.Option value="gpt-4">GPT-4</Select.Option>
              <Select.Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Select.Option>
              <Select.Option value="claude-3-sonnet">Claude 3 Sonnet</Select.Option>
              <Select.Option value="claude-3-haiku">Claude 3 Haiku</Select.Option>
              <Select.Option value="gemini-pro">Gemini Pro</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title="모델 매핑 편집"
        width={500}
        open={mappingDrawerVisible}
        onClose={() => setMappingDrawerVisible(false)}
        extra={
          <Space>
            <Button onClick={() => setMappingDrawerVisible(false)}>취소</Button>
            <Button type="primary" onClick={() => mappingForm.submit()}>
              저장
            </Button>
          </Space>
        }
      >
        <Form form={mappingForm} layout="vertical" onFinish={handleSaveMapping}>
          <Form.Item name="default_model" label="기본 모델" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="gpt-4">GPT-4</Select.Option>
              <Select.Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Select.Option>
              <Select.Option value="claude-3-sonnet">Claude 3 Sonnet</Select.Option>
              <Select.Option value="gemini-pro">Gemini Pro</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="fallback_model" label="폴백 모델" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="gpt-4">GPT-4</Select.Option>
              <Select.Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Select.Option>
              <Select.Option value="claude-3-sonnet">Claude 3 Sonnet</Select.Option>
              <Select.Option value="gemini-pro">Gemini Pro</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="retry_count" label="재시도 횟수">
            <Input type="number" min={1} max={10} />
          </Form.Item>
          <Form.Item name="timeout" label="타임아웃 (초)">
            <Input type="number" min={10} max={300} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}

export default AdminModels