import React from 'react'
import { Card, Table, Typography, Tag, Space, Input, DatePicker, Select } from 'antd'
import { AuditOutlined, SearchOutlined } from '@ant-design/icons'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const AdminLogging: React.FC = () => {
  const logData = [
    { 
      id: '1', 
      timestamp: '2024-01-15 14:30:25', 
      user: 'user1@company.com', 
      action: 'content_generation', 
      model: 'gpt-4', 
      tokens: 1250, 
      cost: 0.025, 
      latency: 2.3,
      status: 'success'
    },
    { 
      id: '2', 
      timestamp: '2024-01-15 14:28:10', 
      user: 'admin@company.com', 
      action: 'user_created', 
      model: null, 
      tokens: 0, 
      cost: 0, 
      latency: 0.1,
      status: 'success'
    },
    { 
      id: '3', 
      timestamp: '2024-01-15 14:25:45', 
      user: 'editor@company.com', 
      action: 'content_generation', 
      model: 'claude-3-sonnet', 
      tokens: 890, 
      cost: 0.018, 
      latency: 1.8,
      status: 'failed'
    }
  ]

  const columns = [
    { title: '시간', dataIndex: 'timestamp', key: 'timestamp', width: 150 },
    { title: '사용자', dataIndex: 'user', key: 'user', width: 200 },
    { title: '작업', dataIndex: 'action', key: 'action' },
    { 
      title: '모델', 
      dataIndex: 'model', 
      key: 'model',
      render: (model: string) => model ? <Tag>{model}</Tag> : '-'
    },
    { 
      title: '토큰', 
      dataIndex: 'tokens', 
      key: 'tokens',
      render: (tokens: number) => tokens > 0 ? tokens.toLocaleString() : '-'
    },
    { 
      title: '비용', 
      dataIndex: 'cost', 
      key: 'cost',
      render: (cost: number) => cost > 0 ? `$${cost}` : '-'
    },
    { 
      title: '지연시간', 
      dataIndex: 'latency', 
      key: 'latency',
      render: (latency: number) => latency > 0 ? `${latency}s` : '-'
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status === 'success' ? '성공' : '실패'}
        </Tag>
      )
    }
  ]

  return (
    <div>
      <Title level={3}>로깅/감사</Title>
      <Text type="secondary">시스템 로그와 사용자 활동을 모니터링합니다</Text>

      <Card style={{ marginTop: 24 }}>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Input.Search
              placeholder="사용자, 작업, 모델 검색"
              allowClear
              style={{ width: 250 }}
              prefix={<SearchOutlined />}
            />
            <Select placeholder="작업 유형" style={{ width: 150 }} allowClear>
              <Select.Option value="content_generation">콘텐츠 생성</Select.Option>
              <Select.Option value="user_management">사용자 관리</Select.Option>
              <Select.Option value="system_config">시스템 설정</Select.Option>
            </Select>
            <Select placeholder="상태" style={{ width: 100 }} allowClear>
              <Select.Option value="success">성공</Select.Option>
              <Select.Option value="failed">실패</Select.Option>
            </Select>
          </Space>
          <RangePicker />
        </Space>

        <Table
          columns={columns}
          dataSource={logData}
          rowKey="id"
          size="middle"
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `총 ${total}개의 로그`
          }}
        />
      </Card>
    </div>
  )
}

export default AdminLogging