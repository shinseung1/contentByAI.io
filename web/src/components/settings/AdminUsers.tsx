import React, { useState } from 'react'
import { Table, Card, Button, Tag, Space, Drawer, Form, Input, Select, DatePicker, Switch, message, Badge, Avatar, Dropdown } from 'antd'
import { UserOutlined, EditOutlined, DeleteOutlined, PlusOutlined, MoreOutlined, KeyOutlined } from '@ant-design/icons'
import { Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'

const { Title, Text } = Typography

interface User {
  id: string
  email: string
  name: string
  role: string
  status: string
  expires_at: string
  last_seen_at: string
  monthly_token_limit: number
  monthly_cost_cap: number
  mfa_enabled: boolean
}

const AdminUsers: React.FC = () => {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [form] = Form.useForm()

  const users: User[] = [
    {
      id: '1',
      email: 'admin@company.com',
      name: '관리자',
      role: 'admin',
      status: 'active',
      expires_at: '2024-12-31',
      last_seen_at: '2분 전',
      monthly_token_limit: 1000000,
      monthly_cost_cap: 500,
      mfa_enabled: true
    },
    {
      id: '2',
      email: 'editor@company.com',
      name: '에디터',
      role: 'editor',
      status: 'active',
      expires_at: '2024-11-30',
      last_seen_at: '1시간 전',
      monthly_token_limit: 500000,
      monthly_cost_cap: 200,
      mfa_enabled: false
    },
    {
      id: '3',
      email: 'viewer@company.com',
      name: '뷰어',
      role: 'viewer',
      status: 'inactive',
      expires_at: '2024-10-15',
      last_seen_at: '3일 전',
      monthly_token_limit: 100000,
      monthly_cost_cap: 50,
      mfa_enabled: false
    }
  ]

  const columns: ColumnsType<User> = [
    {
      title: '사용자',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 500 }}>{name}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{record.email}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: '롤',
      dataIndex: 'role',
      key: 'role',
      render: (role) => {
        const colors = {
          owner: 'purple',
          admin: 'blue',
          editor: 'green',
          viewer: 'orange',
          service: 'gray'
        }
        return <Tag color={colors[role as keyof typeof colors]}>{role}</Tag>
      },
    },
    {
      title: '상태',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge 
          status={status === 'active' ? 'success' : 'error'} 
          text={status === 'active' ? '활성' : '비활성'} 
        />
      ),
    },
    {
      title: '만료일',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date) => <Text>{date}</Text>,
    },
    {
      title: '마지막 접속',
      dataIndex: 'last_seen_at',
      key: 'last_seen_at',
      render: (time) => <Text type="secondary">{time}</Text>,
    },
    {
      title: '작업',
      key: 'actions',
      render: (_, record) => (
        <Dropdown
          menu={{
            items: [
              {
                key: 'edit',
                icon: <EditOutlined />,
                label: '편집',
                onClick: () => handleEditUser(record)
              },
              {
                key: 'reset-password',
                icon: <KeyOutlined />,
                label: '비밀번호 재설정'
              },
              {
                type: 'divider'
              },
              {
                key: 'delete',
                icon: <DeleteOutlined />,
                label: '삭제',
                danger: true
              }
            ]
          }}
          trigger={['click']}
        >
          <Button icon={<MoreOutlined />} />
        </Dropdown>
      ),
    },
  ]

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    form.setFieldsValue(user)
    setDrawerVisible(true)
  }

  const handleSaveUser = async (values: any) => {
    try {
      console.log('Saving user:', values)
      message.success('사용자 정보가 저장되었습니다')
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
          <Title level={3}>사용자 관리</Title>
          <Text type="secondary">시스템 사용자 계정을 관리합니다</Text>
        </div>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => {
            setSelectedUser(null)
            form.resetFields()
            setDrawerVisible(true)
          }}
        >
          사용자 추가
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `총 ${total}명의 사용자`
          }}
        />
      </Card>

      <Drawer
        title={selectedUser ? '사용자 편집' : '새 사용자 추가'}
        width={600}
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
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
        >
          <div style={{ marginBottom: 24 }}>
            <Title level={4}>기본정보</Title>
            <Form.Item name="name" label="이름" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="email" label="이메일" rules={[{ required: true, type: 'email' }]}>
              <Input />
            </Form.Item>
            <Form.Item name="role" label="역할" rules={[{ required: true }]}>
              <Select>
                <Select.Option value="owner">Owner</Select.Option>
                <Select.Option value="admin">Admin</Select.Option>
                <Select.Option value="editor">Editor</Select.Option>
                <Select.Option value="viewer">Viewer</Select.Option>
                <Select.Option value="service">Service</Select.Option>
              </Select>
            </Form.Item>
          </div>

          <div style={{ marginBottom: 24 }}>
            <Title level={4}>유효기간</Title>
            <Form.Item name="expires_at" label="만료일">
              <DatePicker style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="auto_renew" label="자동연장" valuePropName="checked">
              <Switch />
            </Form.Item>
          </div>

          <div style={{ marginBottom: 24 }}>
            <Title level={4}>크레딧/한도</Title>
            <Form.Item name="monthly_token_limit" label="월 토큰 한도">
              <Input type="number" suffix="토큰" />
            </Form.Item>
            <Form.Item name="monthly_cost_cap" label="월 비용 상한">
              <Input type="number" suffix="USD" />
            </Form.Item>
          </div>

          <div>
            <Title level={4}>보안</Title>
            <Form.Item name="mfa_enabled" label="2단계 인증" valuePropName="checked">
              <Switch />
            </Form.Item>
            <Space>
              <Button icon={<KeyOutlined />}>비밀번호 재설정 링크 발급</Button>
            </Space>
          </div>
        </Form>
      </Drawer>
    </div>
  )
}

export default AdminUsers