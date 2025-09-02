import React, { useState } from 'react'
import { Card, Table, Typography, Tag, Space, Button, Input, Select } from 'antd'
import { FileTextOutlined, SearchOutlined, RedoOutlined, EditOutlined, CopyOutlined } from '@ant-design/icons'

const { Title, Text } = Typography

const UserTasks: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState<string>('')

  const tasks = [
    {
      id: '1',
      title: 'AI 마케팅 전략 가이드',
      status: 'published',
      created_at: '2024-01-15',
      updated_at: '2024-01-16',
      model: 'GPT-4',
      word_count: 1250
    },
    {
      id: '2', 
      title: '소셜 미디어 콘텐츠 최적화',
      status: 'draft',
      created_at: '2024-01-14',
      updated_at: '2024-01-14',
      model: 'Claude-3',
      word_count: 890
    },
    {
      id: '3',
      title: 'SEO 최적화 체크리스트',
      status: 'scheduled',
      created_at: '2024-01-13',
      updated_at: '2024-01-13',
      model: 'Gemini-Pro',
      word_count: 750
    },
    {
      id: '4',
      title: '브랜드 스토리텔링 가이드',
      status: 'failed',
      created_at: '2024-01-12',
      updated_at: '2024-01-12',
      model: 'GPT-4',
      word_count: 0
    }
  ]

  const getStatusTag = (status: string) => {
    const statusMap = {
      draft: { color: 'blue', text: '초안' },
      scheduled: { color: 'orange', text: '예약됨' },
      published: { color: 'green', text: '발행됨' },
      failed: { color: 'red', text: '실패' }
    }
    const config = statusMap[status as keyof typeof statusMap]
    return <Tag color={config.color}>{config.text}</Tag>
  }

  const columns = [
    {
      title: '제목',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{title}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.model} | {record.word_count > 0 ? `${record.word_count}자` : '생성 실패'}
          </Text>
        </div>
      )
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: getStatusTag
    },
    {
      title: '생성일',
      dataIndex: 'created_at',
      key: 'created_at'
    },
    {
      title: '수정일',
      dataIndex: 'updated_at',
      key: 'updated_at'
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.status === 'failed' && (
            <Button icon={<RedoOutlined />} size="small" type="primary">
              재시도
            </Button>
          )}
          {(record.status === 'draft' || record.status === 'scheduled') && (
            <Button icon={<EditOutlined />} size="small">
              수정
            </Button>
          )}
          <Button icon={<CopyOutlined />} size="small">
            복제
          </Button>
        </Space>
      )
    }
  ]

  const filteredTasks = filterStatus ? tasks.filter(task => task.status === filterStatus) : tasks

  return (
    <div>
      <Title level={3}>내 작업</Title>
      <Text type="secondary">생성한 콘텐츠와 작업 상태를 관리합니다</Text>

      <Card style={{ marginTop: 24 }}>
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Input.Search
              placeholder="제목으로 검색"
              allowClear
              style={{ width: 250 }}
              prefix={<SearchOutlined />}
            />
            <Select 
              placeholder="상태 필터" 
              style={{ width: 120 }} 
              allowClear
              value={filterStatus}
              onChange={setFilterStatus}
            >
              <Select.Option value="draft">초안</Select.Option>
              <Select.Option value="scheduled">예약됨</Select.Option>
              <Select.Option value="published">발행됨</Select.Option>
              <Select.Option value="failed">실패</Select.Option>
            </Select>
          </Space>
        </Space>

        <Table
          columns={columns}
          dataSource={filteredTasks}
          rowKey="id"
          size="middle"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `총 ${total}개의 작업`
          }}
        />
      </Card>
    </div>
  )
}

export default UserTasks